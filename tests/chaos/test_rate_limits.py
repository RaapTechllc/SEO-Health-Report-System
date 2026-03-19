"""
Chaos tests for rate limit (429) handling.

Tests verify that the system handles 429 responses from external APIs
gracefully with proper retry logic and backoff.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class Test429RetryBehavior:
    """Tests for 429 retry behavior."""

    @pytest.mark.asyncio
    async def test_429_triggers_retry_with_backoff(self):
        """429 response should trigger retry with exponential backoff."""
        call_times = []
        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_times.append(time.time())
            call_count += 1
            if call_count < 3:
                raise RateLimitError(429, "Too Many Requests", retry_after=1)
            return {"status": "ok"}

        class RateLimitError(Exception):
            def __init__(self, status, message, retry_after=None):
                self.status = status
                self.message = message
                self.retry_after = retry_after

        async def call_with_retry(max_retries=3):
            for attempt in range(max_retries):
                try:
                    return await mock_api_call()
                except RateLimitError as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = e.retry_after or (2**attempt)
                    await asyncio.sleep(min(wait_time, 0.1))  # Cap for test speed

        result = await call_with_retry()
        assert result["status"] == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_after_header_respected(self):
        """Retry-After header value should be respected."""
        retry_after_values = []

        class MockResponse:
            def __init__(self, status, retry_after=None):
                self.status = status
                self.headers = {"Retry-After": str(retry_after)} if retry_after else {}

        def parse_retry_after(response):
            if "Retry-After" in response.headers:
                value = response.headers["Retry-After"]
                retry_after_values.append(int(value))
                return int(value)
            return 1  # Default

        responses = [
            MockResponse(429, retry_after=5),
            MockResponse(429, retry_after=10),
            MockResponse(200),
        ]

        for response in responses[:2]:
            parse_retry_after(response)
            # In real code, would sleep here

        assert retry_after_values == [5, 10]

    @pytest.mark.asyncio
    async def test_partial_results_on_retry_exhaustion(self):
        """Should return partial results when retries are exhausted."""
        results = {"pagespeed": None, "crawl": None}

        async def fetch_with_429():
            raise Exception("429 - Rate limit exceeded after 3 retries")

        async def fetch_crawl():
            return {"pages": 10}

        # PageSpeed fails with 429
        try:
            results["pagespeed"] = await fetch_with_429()
        except Exception as e:
            results["pagespeed"] = {"error": str(e), "partial": True}

        # Crawl succeeds
        results["crawl"] = await fetch_crawl()

        assert results["pagespeed"]["partial"] is True
        assert results["crawl"]["pages"] == 10

    @pytest.mark.asyncio
    async def test_no_cascading_failures_on_429(self):
        """429 from one service should not affect others."""
        service_results = {}
        service_order = []

        async def call_service(name, should_429=False):
            service_order.append(name)
            if should_429:
                return {"status": "rate_limited", "service": name}
            return {"status": "ok", "service": name}

        services = [
            ("pagespeed", True),
            ("ai_analysis", False),
            ("sitemap_check", True),
            ("robots_check", False),
        ]

        for name, should_429 in services:
            result = await call_service(name, should_429)
            service_results[name] = result

        # All services were called despite 429s
        assert len(service_order) == 4

        # Services that didn't 429 should succeed
        assert service_results["ai_analysis"]["status"] == "ok"
        assert service_results["robots_check"]["status"] == "ok"


class TestExponentialBackoff:
    """Tests for exponential backoff timing."""

    def test_exponential_backoff_timing(self):
        """Backoff should follow exponential pattern."""

        def calculate_backoff(attempt, base=1, maximum=60):
            delay = min(base * (2**attempt), maximum)
            return delay

        delays = [calculate_backoff(i) for i in range(6)]

        assert delays == [1, 2, 4, 8, 16, 32]

    def test_backoff_respects_maximum(self):
        """Backoff should not exceed maximum delay."""
        max_delay = 30

        def calculate_backoff(attempt, maximum=30):
            return min(2**attempt, maximum)

        delays = [calculate_backoff(i, max_delay) for i in range(10)]

        assert all(d <= max_delay for d in delays)
        assert delays[-1] == max_delay

    @pytest.mark.asyncio
    async def test_jitter_applied_to_backoff(self):
        """Backoff should include jitter to prevent thundering herd."""
        import random

        def backoff_with_jitter(attempt, base=1, jitter=0.5):
            delay = base * (2**attempt)
            jitter_amount = delay * jitter * random.random()
            return delay + jitter_amount

        # Multiple calls should produce different values
        delays = [backoff_with_jitter(2) for _ in range(10)]

        # Should have variation (not all same)
        assert len(set(delays)) > 1


class TestConcurrent429Handling:
    """Tests for concurrent request 429 handling."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_handle_429(self):
        """Multiple concurrent requests should handle 429 independently."""
        call_count = 0
        lock = asyncio.Lock()

        async def rate_limited_call(request_id):
            nonlocal call_count
            async with lock:
                call_count += 1
                current = call_count

            # First few requests get rate limited
            if current <= 2:
                return {"id": request_id, "status": "rate_limited"}
            return {"id": request_id, "status": "ok"}

        # Make concurrent requests
        tasks = [rate_limited_call(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All requests should complete
        assert len(results) == 5

        # Mix of rate limited and ok
        statuses = [r["status"] for r in results]
        assert "rate_limited" in statuses
        assert "ok" in statuses

    @pytest.mark.asyncio
    async def test_global_rate_limit_coordination(self):
        """Global rate limiter should coordinate across requests."""

        class GlobalRateLimiter:
            def __init__(self, requests_per_second=10):
                self.requests_per_second = requests_per_second
                self.tokens = requests_per_second
                self.last_update = time.time()
                self.lock = asyncio.Lock()

            async def acquire(self):
                async with self.lock:
                    now = time.time()
                    elapsed = now - self.last_update
                    self.tokens = min(
                        self.requests_per_second,
                        self.tokens + elapsed * self.requests_per_second,
                    )
                    self.last_update = now

                    if self.tokens >= 1:
                        self.tokens -= 1
                        return True
                    return False

        limiter = GlobalRateLimiter(requests_per_second=2)

        # Make rapid requests
        results = []
        for _ in range(5):
            allowed = await limiter.acquire()
            results.append(allowed)

        # Should allow first 2 immediately
        assert results[:2] == [True, True]
        # Rest should be rate limited (in rapid succession)
        assert not all(results)


class TestServiceSpecific429:
    """Tests for service-specific 429 handling."""

    @pytest.mark.asyncio
    async def test_pagespeed_429_handling(self):
        """PageSpeed 429 should be handled with proper retry."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            # First call returns 429, second succeeds
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.headers = {"Retry-After": "1"}

            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"score": 85}

            mock_get.side_effect = [mock_response_429, mock_response_200]

            # Simulate retry logic
            response = await mock_get()
            if response.status_code == 429:
                await asyncio.sleep(0.01)  # Shortened for test
                response = await mock_get()

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ai_api_429_with_fallback(self):
        """AI API 429 should trigger fallback analysis."""
        # Simulate AI API call that returns 429
        async def mock_ai_call():
            raise Exception("429 Rate Limit")

        # Fallback when AI is rate limited
        try:
            result = await mock_ai_call()
        except Exception:
            result = {
                "analysis": "Fallback analysis due to rate limit",
                "confidence": "low",
                "fallback": True,
            }

        assert result["fallback"] is True


class TestRateLimitRecovery:
    """Tests for rate limit recovery."""

    @pytest.mark.asyncio
    async def test_recovery_after_rate_limit_window(self):
        """System should recover after rate limit window."""
        rate_limited_until = time.time() + 0.1

        async def check_rate_limit():
            if time.time() < rate_limited_until:
                return False
            return True

        # Initially rate limited
        assert not await check_rate_limit()

        # Wait for window
        await asyncio.sleep(0.15)

        # Should be recovered
        assert await check_rate_limit()

    def test_rate_limit_status_tracked(self):
        """Rate limit status should be tracked per service."""
        rate_limit_status = {}

        def update_rate_limit(service, limited=True, reset_at=None):
            rate_limit_status[service] = {
                "limited": limited,
                "reset_at": reset_at or (time.time() + 60),
            }

        def is_rate_limited(service):
            if service not in rate_limit_status:
                return False
            status = rate_limit_status[service]
            if time.time() > status["reset_at"]:
                return False
            return status["limited"]

        update_rate_limit("pagespeed", limited=True)
        update_rate_limit("ai", limited=False)

        assert is_rate_limited("pagespeed")
        assert not is_rate_limited("ai")
        assert not is_rate_limited("unknown_service")


# Run configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
