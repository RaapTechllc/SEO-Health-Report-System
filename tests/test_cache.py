#!/usr/bin/env python3
"""
Test script to demonstrate API caching functionality.

This script shows how the caching system works and can be used to verify
cache hits/misses and performance improvements.
"""

import os
import sys
import time

# Add the seo-health-report scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'seo-health-report', 'scripts'))

from cache import TTL_HTTP_FETCH, cached, clear_cache, get_cache_stats


@cached("demo", TTL_HTTP_FETCH)
def simulate_api_call(url: str, delay: float = 1.0) -> dict:
    """Simulate a slow API call."""
    print(f"  Making API call to {url}...")
    time.sleep(delay)
    return {
        "url": url,
        "timestamp": time.time(),
        "data": f"Response from {url}"
    }

def main():
    print("=" * 60)
    print("SEO HEALTH REPORT - CACHE DEMO")
    print("=" * 60)

    # Test URLs
    test_urls = [
        "https://example.com",
        "https://test.com",
        "https://example.com"  # Duplicate to test cache hit
    ]

    print("\n1. Testing cache functionality...")

    for i, url in enumerate(test_urls, 1):
        print(f"\nCall {i}: {url}")
        start = time.time()
        result = simulate_api_call(url, delay=0.5)
        duration = time.time() - start
        print(f"  Duration: {duration:.3f}s")
        print(f"  Result: {result['data']}")

    print("\n2. Testing cache bypass...")
    print("\nCall with bypass flag:")
    start = time.time()
    result = simulate_api_call("https://example.com", delay=0.5, _bypass_cache=True)
    duration = time.time() - start
    print(f"  Duration: {duration:.3f}s (should be slow)")

    print("\n3. Cache statistics:")
    stats = get_cache_stats()
    if stats:
        for namespace, count in stats.items():
            print(f"  {namespace}: {count} entries")
    else:
        print("  Cache statistics not available (diskcache not installed)")

    print("\n4. Testing cache clear...")
    clear_cache("demo")
    print("  Demo cache cleared")

    print("\n5. Testing after clear (should be slow again)...")
    start = time.time()
    result = simulate_api_call("https://example.com", delay=0.5)
    duration = time.time() - start
    print(f"  Duration: {duration:.3f}s")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nNOTE: If diskcache is installed, you should see:")
    print("- First call to each URL is slow (~0.5s)")
    print("- Repeated calls to same URL are fast (<0.01s)")
    print("- Bypass calls are always slow")
    print("- Cache clear makes subsequent calls slow again")
    print("\nWithout diskcache, all calls will be slow (fallback behavior)")

if __name__ == "__main__":
    main()
