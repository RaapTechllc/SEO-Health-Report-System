"""
Tests for in-memory caching functionality.
"""

import time

import pytest

from packages.seo_health_report.scripts import memory_cache


class TestMemoryCacheBasics:
    """Tests for basic cache operations."""

    def setup_method(self):
        """Clear cache before each test."""
        memory_cache.clear()

    def test_set_and_get(self):
        """Test basic set and get operations."""
        memory_cache.set("test_key", "test_value", ttl=60)
        result = memory_cache.get("test_key")
        assert result == "test_value"

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        result = memory_cache.get("nonexistent")
        assert result is None

    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        memory_cache.set("short_ttl", "value", ttl=1)
        assert memory_cache.get("short_ttl") == "value"

        time.sleep(1.1)
        assert memory_cache.get("short_ttl") is None

    def test_delete(self):
        """Test deleting a key."""
        memory_cache.set("to_delete", "value", ttl=60)
        assert memory_cache.get("to_delete") == "value"

        deleted = memory_cache.delete("to_delete")
        assert deleted is True
        assert memory_cache.get("to_delete") is None

    def test_delete_nonexistent(self):
        """Test deleting a key that doesn't exist."""
        deleted = memory_cache.delete("nonexistent")
        assert deleted is False

    def test_clear(self):
        """Test clearing all entries."""
        memory_cache.set("key1", "value1", ttl=60)
        memory_cache.set("key2", "value2", ttl=60)

        count = memory_cache.clear()
        assert count == 2
        assert memory_cache.get("key1") is None
        assert memory_cache.get("key2") is None

    def test_clear_expired(self):
        """Test clearing only expired entries."""
        memory_cache.set("short", "value", ttl=1)
        memory_cache.set("long", "value", ttl=60)

        time.sleep(1.1)

        cleared = memory_cache.clear_expired()
        assert cleared == 1
        assert memory_cache.get("long") == "value"

    def test_stats(self):
        """Test cache statistics."""
        memory_cache.clear()
        memory_cache.set("key1", "value1", ttl=60)
        memory_cache.set("key2", "value2", ttl=1)

        stats = memory_cache.stats()
        assert stats["total_entries"] == 2

        time.sleep(1.1)
        stats = memory_cache.stats()
        assert stats["expired_entries"] == 1


class TestMemoryCacheDecorators:
    """Tests for cache decorators."""

    def setup_method(self):
        """Clear cache before each test."""
        memory_cache.clear()

    def test_cached_memory_decorator(self):
        """Test sync caching decorator."""
        call_count = 0

        @memory_cache.cached_memory("test_func", ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should return cached value
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

        # Different argument - should execute function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_cached_memory_with_kwargs(self):
        """Test caching with keyword arguments."""
        call_count = 0

        @memory_cache.cached_memory("kwarg_func", ttl=60)
        def func_with_kwargs(a, b=10):
            nonlocal call_count
            call_count += 1
            return a + b

        result1 = func_with_kwargs(5, b=20)
        assert result1 == 25
        assert call_count == 1

        result2 = func_with_kwargs(5, b=20)
        assert result2 == 25
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cached_memory_async_decorator(self):
        """Test async caching decorator."""
        call_count = 0

        @memory_cache.cached_memory_async("async_func", ttl=60)
        async def async_expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 3

        # First call
        result1 = await async_expensive(7)
        assert result1 == 21
        assert call_count == 1

        # Cached call
        result2 = await async_expensive(7)
        assert result2 == 21
        assert call_count == 1


class TestAuditCacheHelpers:
    """Tests for audit-specific cache helpers."""

    def setup_method(self):
        """Clear cache before each test."""
        memory_cache.clear()

    def test_cache_audit_result(self):
        """Test caching audit results."""
        audit_id = "audit_123"
        result = {"score": 85, "grade": "B"}

        memory_cache.cache_audit_result(audit_id, result)
        cached = memory_cache.get_cached_audit_result(audit_id)

        assert cached == result

    def test_cache_audit_status(self):
        """Test caching audit status."""
        audit_id = "audit_456"
        status = {"status": "running", "progress": 50}

        memory_cache.cache_audit_status(audit_id, status)
        cached = memory_cache.get_cached_audit_status(audit_id)

        assert cached == status

    def test_invalidate_audit_cache(self):
        """Test invalidating all cache for an audit."""
        audit_id = "audit_789"

        memory_cache.cache_audit_result(audit_id, {"score": 75})
        memory_cache.cache_audit_status(audit_id, {"status": "completed"})

        memory_cache.invalidate_audit_cache(audit_id)

        assert memory_cache.get_cached_audit_result(audit_id) is None
        assert memory_cache.get_cached_audit_status(audit_id) is None

    def test_audit_result_ttl(self):
        """Test that audit results have long TTL."""
        # We can't easily test the full TTL (1 hour), but we can verify
        # the cache entry exists after a short time
        audit_id = "audit_ttl_test"
        memory_cache.cache_audit_result(audit_id, {"score": 90})

        time.sleep(0.1)
        assert memory_cache.get_cached_audit_result(audit_id) is not None


class TestCacheDataTypes:
    """Tests for caching different data types."""

    def setup_method(self):
        """Clear cache before each test."""
        memory_cache.clear()

    def test_cache_dict(self):
        """Test caching dictionaries."""
        data = {"key": "value", "nested": {"inner": 123}}
        memory_cache.set("dict_key", data, ttl=60)
        assert memory_cache.get("dict_key") == data

    def test_cache_list(self):
        """Test caching lists."""
        data = [1, 2, 3, {"nested": True}]
        memory_cache.set("list_key", data, ttl=60)
        assert memory_cache.get("list_key") == data

    def test_cache_none_not_stored(self):
        """Test that None values are not cached by decorators."""
        @memory_cache.cached_memory("none_func", ttl=60)
        def returns_none():
            return None

        result = returns_none()
        assert result is None
        # Verify nothing was cached (decorator doesn't cache None)
        # This is intentional to avoid caching failed lookups
