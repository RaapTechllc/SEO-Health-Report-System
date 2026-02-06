"""
Rate limiting middleware for API protection.
Uses in-memory storage (upgrade to Redis for production scale).

Supports:
- Per-endpoint rate limits
- Tier-based limits (basic/pro/enterprise)
- Per-tenant override support
- X-RateLimit-* headers in responses
"""

import os
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from abc import ABC, abstractmethod

import logging

_logger = logging.getLogger(__name__)


class RateLimitBackend(ABC):
    """Abstract backend for rate limit storage."""

    @abstractmethod
    def increment(self, key: str, window_seconds: int) -> int:
        """Increment counter for key, return current count."""
        ...

    @abstractmethod
    def get_count(self, key: str, window_seconds: int) -> int:
        """Get current count for key within window."""
        ...

    @abstractmethod
    def get_ttl(self, key: str) -> int:
        """Get seconds until key expires."""
        ...


class InMemoryBackend(RateLimitBackend):
    """In-memory rate limit storage (existing behavior)."""

    def __init__(self):
        self._counts: dict[str, list] = defaultdict(list)

    def _cleanup(self, key: str, window: int) -> None:
        cutoff = time.time() - window
        self._counts[key] = [t for t in self._counts[key] if t > cutoff]

    def increment(self, key: str, window_seconds: int) -> int:
        self._cleanup(key, window_seconds)
        self._counts[key].append(time.time())
        return len(self._counts[key])

    def get_count(self, key: str, window_seconds: int) -> int:
        self._cleanup(key, window_seconds)
        return len(self._counts[key])

    def get_ttl(self, key: str) -> int:
        if self._counts[key]:
            oldest = min(self._counts[key])
            return max(0, int(oldest + 60 - time.time()))
        return 60


class RedisBackend(RateLimitBackend):
    """Redis-backed rate limit storage using sliding window sorted sets."""

    def __init__(self, redis_url: str):
        try:
            import redis as redis_lib
            self._redis = redis_lib.from_url(redis_url, decode_responses=True)
            self._redis.ping()
            _logger.info("Redis rate limit backend connected")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def increment(self, key: str, window_seconds: int) -> int:
        import uuid
        now = time.time()
        pipe = self._redis.pipeline()
        rkey = f"rl:{key}"
        pipe.zremrangebyscore(rkey, 0, now - window_seconds)
        pipe.zadd(rkey, {f"{now}:{uuid.uuid4().hex[:8]}": now})
        pipe.zcard(rkey)
        pipe.expire(rkey, window_seconds + 1)
        results = pipe.execute()
        return results[2]

    def get_count(self, key: str, window_seconds: int) -> int:
        now = time.time()
        rkey = f"rl:{key}"
        self._redis.zremrangebyscore(rkey, 0, now - window_seconds)
        return self._redis.zcard(rkey)

    def get_ttl(self, key: str) -> int:
        ttl = self._redis.ttl(f"rl:{key}")
        return max(0, ttl) if ttl > 0 else 60


def _create_backend() -> RateLimitBackend:
    """Auto-detect and create rate limit backend."""
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            return RedisBackend(redis_url)
        except Exception as e:
            _logger.warning(f"Failed to connect to Redis for rate limiting, falling back to in-memory: {e}")
    else:
        _logger.info("REDIS_URL not set, using in-memory rate limiting (not suitable for multi-process production)")
    return InMemoryBackend()


# Global backend instance
_backend = _create_backend()

# Configuration defaults
DEFAULT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))
DEFAULT_AUDITS_PER_DAY = int(os.getenv("RATE_LIMIT_AUDITS_PER_DAY", "10"))

# Tier-based limits (requests per minute)
TIER_LIMITS = {
    "basic": {
        "requests_per_minute": 100,
        "audits_per_day": 5,
        "concurrent_audits": 1,
    },
    "pro": {
        "requests_per_minute": 500,
        "audits_per_day": 25,
        "concurrent_audits": 3,
    },
    "enterprise": {
        "requests_per_minute": 2000,
        "audits_per_day": 100,
        "concurrent_audits": 10,
    },
    "default": {
        "requests_per_minute": DEFAULT_REQUESTS_PER_MINUTE,
        "audits_per_day": DEFAULT_AUDITS_PER_DAY,
        "concurrent_audits": 1,
    },
}

# Per-tenant overrides storage (tenant_id -> limits dict)
_tenant_overrides: dict[str, dict] = {}

# Per-endpoint limits (requests per minute)
ENDPOINT_LIMITS = {
    "/audit": 60,  # 60 audit requests per minute (poller friendly)
    "/checkout/create": 10,  # 5 checkout requests per minute
    "/auth/register": 20,  # 20 registrations per minute
    "/auth/login": 30,  # 30 login attempts per minute
}

# In-memory storage (use Redis in production)
_request_counts: dict[str, list] = defaultdict(list)
_audit_counts: dict[str, list] = defaultdict(list)
_endpoint_counts: dict[str, list] = defaultdict(list)


def _cleanup_old_entries(entries: list, window_seconds: int) -> list:
    """Remove entries older than the window."""
    cutoff = time.time() - window_seconds
    return [t for t in entries if t > cutoff]


def get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_tier_limits(tier: str = "default", tenant_id: Optional[str] = None) -> dict:
    """Get rate limits for a specific tier, with optional tenant overrides."""
    base_limits = TIER_LIMITS.get(tier, TIER_LIMITS["default"]).copy()

    if tenant_id and tenant_id in _tenant_overrides:
        base_limits.update(_tenant_overrides[tenant_id])

    return base_limits


def set_tenant_override(tenant_id: str, overrides: dict) -> None:
    """Set custom rate limits for a specific tenant."""
    _tenant_overrides[tenant_id] = overrides


def remove_tenant_override(tenant_id: str) -> None:
    """Remove custom rate limits for a tenant."""
    _tenant_overrides.pop(tenant_id, None)


def get_tenant_override(tenant_id: str) -> Optional[dict]:
    """Get custom rate limits for a tenant if set."""
    return _tenant_overrides.get(tenant_id)


def check_rate_limit(request: Request, tier: str = "default", tenant_id: Optional[str] = None) -> dict:
    """
    Check if request is within rate limits.

    Returns dict with rate limit info for headers.
    Raises HTTPException(429) if limit exceeded.
    """
    client_ip = get_client_ip(request)
    key = f"{tenant_id}:{client_ip}" if tenant_id else client_ip
    current_time = time.time()
    limits = get_tier_limits(tier, tenant_id)

    # Clean up old entries (1 minute window)
    _request_counts[key] = _cleanup_old_entries(
        _request_counts[key], 60
    )

    requests_limit = limits["requests_per_minute"]
    requests_used = len(_request_counts[key])
    requests_remaining = max(0, requests_limit - requests_used)

    # Calculate reset time (seconds until window resets)
    if _request_counts[key]:
        oldest = min(_request_counts[key])
        reset_time = max(0, int(oldest + 60 - current_time))
    else:
        reset_time = 60

    rate_info = {
        "limit": requests_limit,
        "remaining": requests_remaining,
        "reset": reset_time,
        "tier": tier,
    }

    if tenant_id:
        rate_info["tenant_id"] = tenant_id

    # Check limit
    if requests_used >= requests_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {requests_limit} requests per minute for {tier} tier.",
            headers={
                "X-RateLimit-Limit": str(requests_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(reset_time),
            }
        )

    # Record request
    _request_counts[key].append(current_time)
    rate_info["remaining"] = requests_remaining - 1

    return rate_info


def get_remaining_requests(request: Request, tier: str = "default", tenant_id: Optional[str] = None) -> int:
    """Get remaining requests in current window without incrementing count."""
    client_ip = get_client_ip(request)
    key = f"{tenant_id}:{client_ip}" if tenant_id else client_ip
    limits = get_tier_limits(tier, tenant_id)

    _request_counts[key] = _cleanup_old_entries(_request_counts[key], 60)
    requests_used = len(_request_counts[key])
    return max(0, limits["requests_per_minute"] - requests_used)


def get_reset_time(request: Request, tenant_id: Optional[str] = None) -> int:
    """Get seconds until rate limit window resets."""
    client_ip = get_client_ip(request)
    key = f"{tenant_id}:{client_ip}" if tenant_id else client_ip
    current_time = time.time()

    _request_counts[key] = _cleanup_old_entries(_request_counts[key], 60)

    if _request_counts[key]:
        oldest = min(_request_counts[key])
        return max(0, int(oldest + 60 - current_time))
    return 60


def check_endpoint_limit(request: Request) -> Optional[dict]:
    """
    Check per-endpoint rate limits.
    Returns rate info if applicable, None if no specific limit.
    """
    path = request.url.path

    # Find matching endpoint limit
    endpoint_limit = None
    for endpoint, limit in ENDPOINT_LIMITS.items():
        if path.startswith(endpoint):
            endpoint_limit = limit
            break

    if endpoint_limit is None:
        return None

    client_ip = get_client_ip(request)
    key = f"{client_ip}:{path}"
    current_time = time.time()

    # Clean up old entries (1 minute window)
    _endpoint_counts[key] = _cleanup_old_entries(_endpoint_counts[key], 60)

    used = len(_endpoint_counts[key])
    remaining = max(0, endpoint_limit - used)

    if used >= endpoint_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Endpoint rate limit exceeded. Max {endpoint_limit} requests per minute for {path}.",
            headers={
                "X-RateLimit-Limit": str(endpoint_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "60",
                "Retry-After": "60",
            }
        )

    _endpoint_counts[key].append(current_time)

    return {
        "endpoint_limit": endpoint_limit,
        "endpoint_remaining": remaining - 1,
    }


def check_audit_limit(user_id: str, tier: str = "default") -> dict:
    """
    Check if user is within audit limits.

    Returns dict with audit limit info.
    Raises HTTPException(429) if limit exceeded.
    """
    current_time = time.time()
    limits = get_tier_limits(tier)

    # Clean up old entries (24 hours)
    _audit_counts[user_id] = _cleanup_old_entries(_audit_counts[user_id], 86400)

    audits_limit = limits["audits_per_day"]
    audits_used = len(_audit_counts[user_id])
    audits_remaining = max(0, audits_limit - audits_used)

    # Calculate reset time
    if _audit_counts[user_id]:
        oldest = min(_audit_counts[user_id])
        reset_time = int(oldest + 86400 - current_time)
    else:
        reset_time = 86400

    audit_info = {
        "limit": audits_limit,
        "remaining": audits_remaining,
        "reset": reset_time,
        "tier": tier,
    }

    # Check limit
    if audits_used >= audits_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Audit limit exceeded. Max {audits_limit} audits per day for {tier} tier.",
            headers={
                "X-RateLimit-Audit-Limit": str(audits_limit),
                "X-RateLimit-Audit-Remaining": "0",
                "X-RateLimit-Audit-Reset": str(reset_time),
                "Retry-After": str(reset_time),
            }
        )

    # Record audit
    _audit_counts[user_id].append(current_time)
    audit_info["remaining"] = audits_remaining - 1

    return audit_info


def get_rate_limit_status(request: Request, tier: str = "default", tenant_id: Optional[str] = None) -> dict:
    """Get current rate limit status for client."""
    client_ip = get_client_ip(request)
    key = f"{tenant_id}:{client_ip}" if tenant_id else client_ip
    limits = get_tier_limits(tier, tenant_id)
    current_time = time.time()

    _request_counts[key] = _cleanup_old_entries(_request_counts[key], 60)

    requests_used = len(_request_counts[key])
    requests_limit = limits["requests_per_minute"]

    if _request_counts[key]:
        oldest = min(_request_counts[key])
        reset_time = max(0, int(oldest + 60 - current_time))
    else:
        reset_time = 60

    return {
        "tier": tier,
        "tenant_id": tenant_id,
        "requests": {
            "used": requests_used,
            "limit": requests_limit,
            "remaining": max(0, requests_limit - requests_used),
            "reset": reset_time,
        },
        "limits": limits,
    }


def add_rate_limit_headers(response: Response, rate_info: dict) -> Response:
    """Add X-RateLimit-* headers to response."""
    response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", 0))
    response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining", 0))
    response.headers["X-RateLimit-Reset"] = str(rate_info.get("reset", 0))

    if "tier" in rate_info:
        response.headers["X-RateLimit-Tier"] = rate_info["tier"]

    return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds rate limiting to all requests.

    Extracts tier from JWT token if available, otherwise uses default limits.
    """

    def __init__(self, app, default_tier: str = "default"):
        super().__init__(app)
        self.default_tier = default_tier

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Get tier from request (would normally extract from JWT)
        tier = self.default_tier

        try:
            # Check general rate limit
            rate_info = check_rate_limit(request, tier)

            # Check endpoint-specific limit
            endpoint_info = check_endpoint_limit(request)
            if endpoint_info:
                rate_info.update(endpoint_info)

        except HTTPException:
            raise

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response = add_rate_limit_headers(response, rate_info)

        return response
