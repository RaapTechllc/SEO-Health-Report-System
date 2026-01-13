"""
Tests for cache module.
"""

import pytest
import time
from seo_health_report.scripts.cache import (
    get_cache,
    cache_key,
    cached,
    clear_cache,
    TTL_PAGESPEED,
    TTL_AI_RESPONSE,
    TTL_HTTP_FETCH,
)


class TestCacheKeyGeneration:
    """Test cache key generation."""

    def test_cache_key_with_args(self):
        """Test cache key generation with arguments."""
        key = cache_key("test_function", "arg1", "arg2")
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length

    def test_cache_key_with_kwargs(self):
        """Test cache key generation with keyword arguments."""
        key1 = cache_key("test_function", param1="value1", param2="value2")
        key2 = cache_key("test_function", param1="value1", param2="value2")
        assert key1 == key2

    def test_cache_key_order_matters(self):
        """Test that argument order matters for cache keys."""
        key1 = cache_key("test_function", "arg1", "arg2")
        key2 = cache_key("test_function", "arg2", "arg1")
        assert key1 != key2


class TestCacheDecorator:
    """Test cached decorator functionality."""

    def test_cached_function_without_diskcache(self, monkeypatch):
        """Test that cached decorator works without diskcache."""

        # Mock diskcache import to fail
        def mock_import(name, *args, **kwargs):
            if "diskcache" in name:
                raise ImportError("diskcache not installed")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        # Reload cache module
        import importlib
        import seo_health_report.scripts.cache as cache_module

        importlib.reload(cache_module)

        # Test that function still works
        @cache_module.cached("test", 60)
        def test_func(x):
            return x * 2

        result = test_func(5)
        assert result == 10

    def test_cached_with_bypass_flag(self):
        """Test _bypass_cache flag forces fresh computation."""
        call_count = []

        @cached("test_bypass", 60)
        def expensive_computation(x):
            call_count.append(x)
            return x * 2

        # First call
        result1 = expensive_computation(5)
        assert result1 == 10
        assert len(call_count) == 1

        # Second cached call (no diskcache means it runs again)
        result2 = expensive_computation(5)
        assert result2 == 10

        # Bypass cache
        result3 = expensive_computation(5, _bypass_cache=True)
        assert result3 == 10


class TestCacheValues:
    """Test cache TTL constants."""

    def test_ttl_pagespeed_value(self):
        """Test PageSpeed TTL is 24 hours."""
        assert TTL_PAGESPEED == 86400  # 24 * 60 * 60

    def test_ttl_ai_response_value(self):
        """Test AI response TTL is 7 days."""
        assert TTL_AI_RESPONSE == 604800  # 7 * 24 * 60 * 60

    def test_ttl_http_fetch_value(self):
        """Test HTTP fetch TTL is 1 hour."""
        assert TTL_HTTP_FETCH == 3600  # 60 * 60


class TestCacheManagement:
    """Test cache management functions."""

    def test_get_cache_without_diskcache(self, monkeypatch):
        """Test get_cache returns None without diskcache."""

        def mock_import(name, *args, **kwargs):
            if "diskcache" in name:
                raise ImportError("diskcache not installed")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        cache = get_cache("test_namespace")
        assert cache is None

    def test_clear_cache_without_diskcache(self, monkeypatch):
        """Test clear_cache works without diskcache."""
        # Should not raise exception
        clear_cache("test_namespace")
        clear_cache()  # Clear all

    def test_get_cache_stats_without_diskcache(self, monkeypatch):
        """Test get_cache_stats returns empty dict without diskcache."""

        def mock_import(name, *args, **kwargs):
            if "diskcache" in name:
                raise ImportError("diskcache not installed")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        # Import and reload
        import importlib
        import seo_health_report.scripts.cache as cache_module

        importlib.reload(cache_module)

        stats = cache_module.get_cache_stats()
        assert isinstance(stats, dict)
        assert len(stats) == 0


class TestCacheIntegration:
    """Integration tests with actual diskcache (if available)."""

    @pytest.mark.skipif(
        pytest.importorskip("diskcache", None) is None, reason="diskcache not installed"
    )
    def test_cache_set_and_get(self):
        """Test basic cache set and get."""
        cache = get_cache("integration_test")

        # Set a value
        cache.set("test_key", "test_value", expire=60)

        # Get the value
        value = cache.get("test_key")
        assert value == "test_value"

        # Clean up
        cache.clear()

    @pytest.mark.skipif(
        pytest.importorskip("diskcache", None) is None, reason="diskcache not installed"
    )
    def test_cache_expiration(self):
        """Test cache key expiration."""
        cache = get_cache("integration_test")

        # Set a value with 1 second TTL
        cache.set("expire_key", "expire_value", expire=1)

        # Should exist immediately
        assert cache.get("expire_key") == "expire_value"

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        assert cache.get("expire_key") is None

        # Clean up
        cache.clear()
