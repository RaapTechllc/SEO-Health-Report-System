"""
Centralized caching utilities for SEO Health Report system.

Provides disk-based caching for expensive API calls with configurable TTL.
"""

import hashlib
import inspect
import os
import sys
from functools import wraps
from typing import Callable

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config

# Get configuration
_config = get_config()

# Cache directory and TTL from config
CACHE_DIR = _config.cache_dir
TTL_PAGESPEED = _config.cache_ttl_pagespeed
TTL_AI_RESPONSE = _config.cache_ttl_ai_response
TTL_HTTP_FETCH = _config.cache_ttl_http_fetch


def get_cache(namespace: str = "default"):
    """Get or create cache instance."""
    try:
        from diskcache import Cache

        cache_path = os.path.join(CACHE_DIR, namespace)
        return Cache(cache_path)
    except ImportError:
        return None


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(namespace: str, ttl: int):
    """Decorator for caching function results (supports sync and async)."""

    def decorator(func: Callable):
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if kwargs.pop("_bypass_cache", False):
                    return await func(*args, **kwargs)

                cache = get_cache(namespace)
                if cache is None:
                    return await func(*args, **kwargs)

                key = cache_key(func.__name__, *args, **kwargs)

                result = cache.get(key)
                if result is not None:
                    return result

                result = await func(*args, **kwargs)
                if result is not None:
                    cache.set(key, result, expire=ttl)
                return result

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if kwargs.pop("_bypass_cache", False):
                    return func(*args, **kwargs)

                cache = get_cache(namespace)
                if cache is None:
                    return func(*args, **kwargs)

                key = cache_key(func.__name__, *args, **kwargs)

                result = cache.get(key)
                if result is not None:
                    return result

                result = func(*args, **kwargs)
                if result is not None:
                    cache.set(key, result, expire=ttl)
                return result

            return sync_wrapper

    return decorator


def clear_cache(namespace: str = None):
    """Clear cache (all or specific namespace)."""
    try:
        if namespace:
            cache = get_cache(namespace)
            if cache:
                cache.clear()
        else:
            # Clear all namespaces
            if os.path.exists(CACHE_DIR):
                import shutil

                shutil.rmtree(CACHE_DIR)
    except Exception:
        pass


def get_cache_stats() -> dict:
    """Get cache statistics."""
    stats = {}
    try:
        if os.path.exists(CACHE_DIR):
            for namespace in os.listdir(CACHE_DIR):
                cache = get_cache(namespace)
                if cache:
                    stats[namespace] = len(cache)
    except Exception:
        pass
    return stats
