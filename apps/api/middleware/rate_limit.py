"""
Rate limit middleware that adds X-RateLimit-* headers to all responses.

Headers added:
- X-RateLimit-Limit: Maximum requests allowed per minute
- X-RateLimit-Remaining: Requests remaining in current window
- X-RateLimit-Reset: Seconds until the rate limit window resets
- Retry-After: (only on 429) Seconds to wait before retrying
"""

from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from rate_limiter import (
    TIER_LIMITS,
    add_rate_limit_headers,
    check_endpoint_limit,
    check_rate_limit,
)

SKIP_PATHS = {"/health", "/", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}


def extract_auth_info(request: Request) -> tuple[str, Optional[str]]:
    """
    Extract tier and tenant_id from request.

    Checks JWT token claims or API key for tier/tenant info.
    Falls back to 'default' tier for unauthenticated requests.
    """
    tier = "default"
    tenant_id = None

    # Check if user info was set by auth middleware
    if hasattr(request.state, "user"):
        user = request.state.user
        tier = getattr(user, "tier", "default") or "default"
        tenant_id = getattr(user, "tenant_id", None)

    # Check for tier in headers (for API key auth)
    header_tier = request.headers.get("X-Tier")
    if header_tier and header_tier in TIER_LIMITS:
        tier = header_tier

    header_tenant = request.headers.get("X-Tenant-ID")
    if header_tenant:
        tenant_id = header_tenant

    return tier, tenant_id


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces rate limits and adds X-RateLimit-* headers.

    Works for both authenticated and unauthenticated requests.
    Authenticated users get tier-based limits, unauthenticated get default limits.
    """

    def __init__(self, app, default_tier: str = "default", enabled: bool = True):
        super().__init__(app)
        self.default_tier = default_tier
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for certain paths
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        # Extract authentication info
        tier, tenant_id = extract_auth_info(request)
        if tier == "default":
            tier = self.default_tier

        rate_info = None

        try:
            # Check general rate limit
            rate_info = check_rate_limit(request, tier, tenant_id)

            # Check endpoint-specific limit
            endpoint_info = check_endpoint_limit(request)
            if endpoint_info:
                rate_info.update(endpoint_info)

        except Exception as exc:
            # Handle 429 from check_rate_limit
            if hasattr(exc, "status_code") and exc.status_code == 429:
                headers = dict(getattr(exc, "headers", {}) or {})
                return JSONResponse(
                    status_code=429,
                    content={"detail": str(exc.detail)},
                    headers=headers,
                )
            raise

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if rate_info:
            response = add_rate_limit_headers(response, rate_info)

        return response


def create_rate_limit_middleware(
    default_tier: str = "default",
    enabled: bool = True,
):
    """Factory function to create rate limit middleware with configuration."""
    def middleware_factory(app):
        return RateLimitHeadersMiddleware(app, default_tier=default_tier, enabled=enabled)
    return middleware_factory
