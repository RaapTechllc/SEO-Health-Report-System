"""
Rate Limiter Tests.

Tests concurrency limiting and per-host throttling.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.seo_health_report.scripts.rate_limiter import (
    TIER_LIMITS,
    RateLimiter,
    RateLimiterConfig,
    rate_limited_fetch,
)


class TestRateLimiterConfig:
    """Test rate limiter configuration."""

    def test_default_config(self):
        config = RateLimiterConfig()
        assert config.max_concurrent_fetches == 5
        assert config.min_host_delay_seconds == 0.5

    def test_tier_limits_exist(self):
        assert "basic" in TIER_LIMITS
        assert "pro" in TIER_LIMITS
        assert "enterprise" in TIER_LIMITS

    def test_basic_is_most_restrictive(self):
        basic = TIER_LIMITS["basic"]
        enterprise = TIER_LIMITS["enterprise"]
        assert basic.max_concurrent_fetches < enterprise.max_concurrent_fetches
        assert basic.min_host_delay_seconds > enterprise.min_host_delay_seconds


class TestRateLimiter:
    """Test rate limiter behavior."""

    @pytest.mark.asyncio
    async def test_concurrency_limit_enforced(self):
        """Test that concurrent requests are limited."""
        config = RateLimiterConfig(max_concurrent_fetches=2, min_host_delay_seconds=0)
        limiter = RateLimiter(config)

        acquired = []

        async def acquire_and_hold(host: str, duration: float):
            await limiter.acquire(host)
            acquired.append(time.time())
            await asyncio.sleep(duration)
            limiter.release()

        start = time.time()
        tasks = [
            asyncio.create_task(acquire_and_hold(f"host{i}.com", 0.1))
            for i in range(4)
        ]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start
        assert elapsed >= 0.15

    @pytest.mark.asyncio
    async def test_per_host_delay_enforced(self):
        """Test that requests to same host are throttled."""
        config = RateLimiterConfig(max_concurrent_fetches=10, min_host_delay_seconds=0.1)
        limiter = RateLimiter(config)

        times = []
        for _ in range(3):
            await limiter.acquire("example.com")
            times.append(time.time())
            limiter.release()

        for i in range(1, len(times)):
            delay = times[i] - times[i-1]
            assert delay >= 0.09

    @pytest.mark.asyncio
    async def test_different_hosts_not_throttled(self):
        """Test that different hosts can be fetched concurrently."""
        config = RateLimiterConfig(max_concurrent_fetches=10, min_host_delay_seconds=0.5)
        limiter = RateLimiter(config)

        start = time.time()

        for i in range(5):
            await limiter.acquire(f"host{i}.com")
            limiter.release()

        elapsed = time.time() - start
        assert elapsed < 0.2

    def test_for_tier_creates_correct_config(self):
        """Test tier-based limiter creation."""
        basic = RateLimiter.for_tier("basic")
        assert basic.config == TIER_LIMITS["basic"]

        unknown = RateLimiter.for_tier("unknown")
        assert unknown.config == TIER_LIMITS["basic"]


class TestRateLimitedFetch:
    """Test rate-limited fetch wrapper."""

    @pytest.mark.asyncio
    async def test_applies_rate_limiting(self):
        config = RateLimiterConfig(max_concurrent_fetches=1, min_host_delay_seconds=0.1)
        limiter = RateLimiter(config)

        mock_result = MagicMock()
        mock_result.status_code = 200

        with patch('packages.seo_health_report.scripts.rate_limiter.safe_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_result

            start = time.time()
            await rate_limited_fetch("https://example.com/1", limiter)
            await rate_limited_fetch("https://example.com/2", limiter)
            elapsed = time.time() - start

            assert elapsed >= 0.09
            assert mock_fetch.call_count == 2
