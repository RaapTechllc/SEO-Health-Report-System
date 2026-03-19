"""
Tests for async utility functions.
"""

import asyncio
import inspect
import os
import sys

import pytest

# Add scripts to path for imports
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "seo-health-report", "scripts"),
)
from async_utils import (
    batch_fetch_urls,
    fetch_url_async,
    run_parallel,
    to_async,
    to_sync,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestFetchUrlAsync:
    """Test async URL fetching."""

    async def test_successful_fetch(self):
        """Test successful URL fetch."""
        result = await fetch_url_async("https://httpbin.org/get", timeout=10)
        assert result is not None
        assert len(result) > 0

    async def test_fetch_with_headers(self):
        """Test fetch with custom headers."""
        headers = {"User-Agent": "Test-Agent"}
        result = await fetch_url_async(
            "https://httpbin.org/get", headers=headers, timeout=10
        )
        assert result is not None

    async def test_fetch_timeout(self):
        """Test fetch with timeout."""
        result = await fetch_url_async("https://httpbin.org/delay/5", timeout=1)
        assert result is None  # Timeout


@pytest.mark.asyncio
@pytest.mark.unit
class TestBatchFetchUrls:
    """Test batch URL fetching."""

    async def test_batch_fetch_success(self):
        """Test fetching multiple URLs."""
        urls = ["https://httpbin.org/get", "https://httpbin.org/delay/1"]
        results = await batch_fetch_urls(urls, timeout=10, batch_size=2)
        assert len(results) == 2
        assert all(result is not None for result in results.values())

    async def test_batch_fetch_with_errors(self):
        """Test batch fetch with some errors."""
        urls = [
            "https://httpbin.org/get",
            "https://invalid-url-that-does-not-exist-12345.com",
        ]
        results = await batch_fetch_urls(urls, timeout=10)
        assert len(results) == 2
        assert results[urls[0]] is not None
        assert results[urls[1]] is None


@pytest.mark.asyncio
@pytest.mark.unit
class TestRunParallel:
    """Test running functions in parallel."""

    async def test_parallel_sync_functions(self):
        """Test running sync functions in parallel."""

        def func1():
            import time

            time.sleep(0.1)
            return "result1"

        def func2():
            import time

            time.sleep(0.1)
            return "result2"

        results = await run_parallel(func1, func2)
        assert results == ["result1", "result2"]

    async def test_parallel_async_functions(self):
        """Test running async functions in parallel."""

        async def func1():
            await asyncio.sleep(0.1)
            return "result1"

        async def func2():
            await asyncio.sleep(0.1)
            return "result2"

        results = await run_parallel(func1, func2)
        assert results == ["result1", "result2"]

    async def test_parallel_mixed_functions(self):
        """Test running mixed sync/async functions."""

        def sync_func():
            import time

            time.sleep(0.1)
            return "sync"

        async def async_func():
            await asyncio.sleep(0.1)
            return "async"

        results = await run_parallel(sync_func, async_func)
        assert results == ["sync", "async"]


@pytest.mark.unit
class TestDecorators:
    """Test async utility decorators."""

    def test_to_async_wraps_sync_function(self):
        """Test to_async decorator wraps sync function."""

        @to_async
        def sync_func(x):
            return x * 2

        assert inspect.iscoroutinefunction(sync_func)

        async def test():
            result = await sync_func(5)
            assert result == 10

        asyncio.run(test())

    def test_to_sync_wraps_async_function(self):
        """Test to_sync decorator wraps async function."""

        @to_sync
        async def async_func(x):
            await asyncio.sleep(0.01)
            return x * 2

        assert not inspect.iscoroutinefunction(async_func)
        result = async_func(5)
        assert result == 10
