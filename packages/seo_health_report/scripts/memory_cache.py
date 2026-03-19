"""
In-memory caching for fast repeated access to audit results and API responses.

This provides a simple TTL-based cache that's faster than disk for frequently
accessed data like audit status and results.
"""

import time
from functools import wraps
from threading import Lock
from typing import Any, Callable, Optional

# Global in-memory cache
_cache: dict[str, tuple[Any, float]] = {}
_cache_lock = Lock()

# Default TTL in seconds
DEFAULT_TTL = 300  # 5 minutes
AUDIT_RESULT_TTL = 3600  # 1 hour for completed audits
AUDIT_STATUS_TTL = 10  # 10 seconds for status polling


def get(key: str) -> Optional[Any]:
    """Get value from cache if not expired."""
    with _cache_lock:
        if key in _cache:
            value, expiry = _cache[key]
            if time.time() < expiry:
                return value
            else:
                del _cache[key]
    return None


def set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Set value in cache with TTL."""
    with _cache_lock:
        _cache[key] = (value, time.time() + ttl)


def delete(key: str) -> bool:
    """Delete key from cache. Returns True if key existed."""
    with _cache_lock:
        if key in _cache:
            del _cache[key]
            return True
    return False


def clear() -> int:
    """Clear all cache entries. Returns count of cleared items."""
    with _cache_lock:
        count = len(_cache)
        _cache.clear()
        return count


def clear_expired() -> int:
    """Clear only expired entries. Returns count of cleared items."""
    now = time.time()
    cleared = 0
    with _cache_lock:
        keys_to_delete = [k for k, (_, expiry) in _cache.items() if now >= expiry]
        for key in keys_to_delete:
            del _cache[key]
            cleared += 1
    return cleared


def stats() -> dict:
    """Get cache statistics."""
    now = time.time()
    with _cache_lock:
        total = len(_cache)
        expired = sum(1 for _, (_, expiry) in _cache.items() if now >= expiry)
        return {
            "total_entries": total,
            "active_entries": total - expired,
            "expired_entries": expired,
        }


def cached_memory(prefix: str = "", ttl: int = DEFAULT_TTL):
    """
    Decorator for caching function results in memory.

    Args:
        prefix: Cache key prefix (default: function name)
        ttl: Time-to-live in seconds

    Example:
        @cached_memory("audit_status", ttl=10)
        def get_audit_status(audit_id: str) -> dict:
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            key_prefix = prefix or func.__name__
            key = f"{key_prefix}:{hash((args, tuple(sorted(kwargs.items()))))}"

            # Check cache
            result = get(key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                set(key, result, ttl)

            return result
        return wrapper
    return decorator


def cached_memory_async(prefix: str = "", ttl: int = DEFAULT_TTL):
    """
    Decorator for caching async function results in memory.

    Args:
        prefix: Cache key prefix (default: function name)
        ttl: Time-to-live in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            key_prefix = prefix or func.__name__
            key = f"{key_prefix}:{hash((args, tuple(sorted(kwargs.items()))))}"

            # Check cache
            result = get(key)
            if result is not None:
                return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                set(key, result, ttl)

            return result
        return wrapper
    return decorator


# Convenience functions for common cache operations
def cache_audit_result(audit_id: str, result: dict) -> None:
    """Cache a completed audit result."""
    set(f"audit_result:{audit_id}", result, AUDIT_RESULT_TTL)


def get_cached_audit_result(audit_id: str) -> Optional[dict]:
    """Get cached audit result."""
    return get(f"audit_result:{audit_id}")


def cache_audit_status(audit_id: str, status: dict) -> None:
    """Cache audit status for polling."""
    set(f"audit_status:{audit_id}", status, AUDIT_STATUS_TTL)


def get_cached_audit_status(audit_id: str) -> Optional[dict]:
    """Get cached audit status."""
    return get(f"audit_status:{audit_id}")


def invalidate_audit_cache(audit_id: str) -> None:
    """Invalidate all cache entries for an audit."""
    delete(f"audit_result:{audit_id}")
    delete(f"audit_status:{audit_id}")
