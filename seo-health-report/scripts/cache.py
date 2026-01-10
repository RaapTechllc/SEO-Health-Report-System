"""
Centralized caching utilities for SEO Health Report system.

Provides disk-based caching for expensive API calls with configurable TTL.
"""

import os
import hashlib
from typing import Any, Optional, Callable
from functools import wraps

# Default cache directory
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".seo-health-cache")

# TTL defaults (seconds)
TTL_PAGESPEED = 86400      # 24 hours
TTL_AI_RESPONSE = 604800   # 7 days  
TTL_HTTP_FETCH = 3600      # 1 hour

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
    """Decorator for caching function results."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check for bypass flag
            if kwargs.pop('_bypass_cache', False):
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
        return wrapper
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
