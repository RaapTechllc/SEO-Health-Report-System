"""
Rate Limiter for External HTTP Requests.

Provides concurrency limiting and per-host throttling to prevent
overwhelming target sites and hitting API quotas.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from packages.seo_health_report.scripts.safe_fetch import FetchResult, safe_fetch


@dataclass
class RateLimiterConfig:
    """Rate limiting configuration."""
    max_concurrent_fetches: int = 5
    min_host_delay_seconds: float = 0.5
    max_requests_per_minute: int = 60


# Tier-specific limits
TIER_LIMITS = {
    "basic": RateLimiterConfig(
        max_concurrent_fetches=3,
        min_host_delay_seconds=1.0,
        max_requests_per_minute=30
    ),
    "pro": RateLimiterConfig(
        max_concurrent_fetches=5,
        min_host_delay_seconds=0.5,
        max_requests_per_minute=60
    ),
    "enterprise": RateLimiterConfig(
        max_concurrent_fetches=10,
        min_host_delay_seconds=0.25,
        max_requests_per_minute=120
    ),
}


class RateLimiter:
    """
    Rate limiter for external HTTP requests.

    Enforces:
    - Maximum concurrent requests (global)
    - Minimum delay between requests to the same host
    """

    def __init__(self, config: Optional[RateLimiterConfig] = None):
        self.config = config or RateLimiterConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_fetches)
        self._host_last_request: dict[str, float] = {}
        self._host_lock = asyncio.Lock()

    async def acquire(self, host: str) -> None:
        """Acquire rate limit slot for a host."""
        # Enforce per-host delay
        async with self._host_lock:
            last = self._host_last_request.get(host, 0)
            elapsed = time.time() - last
            wait = self.config.min_host_delay_seconds - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self._host_last_request[host] = time.time()

        # Acquire global concurrency slot
        await self._semaphore.acquire()

    def release(self) -> None:
        """Release rate limit slot."""
        self._semaphore.release()

    @classmethod
    def for_tier(cls, tier: str) -> "RateLimiter":
        """Create rate limiter with tier-specific config."""
        config = TIER_LIMITS.get(tier, TIER_LIMITS["basic"])
        return cls(config)


async def rate_limited_fetch(
    url: str,
    limiter: RateLimiter,
    **kwargs
) -> FetchResult:
    """
    Fetch URL with rate limiting applied.

    Args:
        url: URL to fetch
        limiter: RateLimiter instance
        **kwargs: Additional arguments passed to safe_fetch

    Returns:
        FetchResult from safe_fetch
    """
    host = urlparse(url).netloc

    await limiter.acquire(host)
    try:
        return await safe_fetch(url, **kwargs)
    finally:
        limiter.release()


# Context manager for cleaner usage
class RateLimitedSession:
    """Context manager for rate-limited fetching."""

    def __init__(self, tier: str = "basic"):
        self.limiter = RateLimiter.for_tier(tier)

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch with rate limiting."""
        return await rate_limited_fetch(url, self.limiter, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass
