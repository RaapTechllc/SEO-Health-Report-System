"""
Async utility functions for concurrent API calls.
"""

import asyncio
import inspect
from functools import wraps
from typing import Any, Callable, Optional

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


async def fetch_url_async(
    url: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 30,
    client: Optional[Any] = None,
) -> Optional[str]:
    """
    Async version of fetch_url.

    Args:
        url: URL to fetch
        headers: HTTP headers
        timeout: Timeout in seconds
        client: Reusable httpx client (optional)

    Returns:
        Response text or None on error
    """
    if not HAS_HTTPX:
        # Fallback to sync requests
        try:
            import requests

            response = requests.get(url, headers=headers, timeout=timeout)
            return response.text
        except Exception:
            return None

    try:
        should_close = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=timeout)

        response = await client.get(url, headers=headers or {})
        if should_close:
            await client.aclose()

        return response.text
    except Exception:
        return None


async def batch_fetch_urls(
    urls: list[str],
    headers: Optional[dict[str, str]] = None,
    timeout: int = 30,
    batch_size: int = 10,
) -> dict[str, Optional[str]]:
    """
    Fetch multiple URLs concurrently in batches.

    Args:
        urls: List of URLs to fetch
        headers: HTTP headers
        timeout: Timeout per request
        batch_size: Max concurrent requests

    Returns:
        Dict mapping URL to response text (or None on error)
    """
    if not HAS_HTTPX:
        # Fallback to sequential fetches
        return {url: await fetch_url_async(url, headers, timeout) for url in urls}

    results = {}

    async with httpx.AsyncClient(timeout=timeout) as client:
        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            tasks = [fetch_url_async(url, headers, client=client) for url in batch]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for url, response in zip(batch, responses):
                results[url] = response if not isinstance(response, Exception) else None

    return results


async def run_parallel(*funcs: Callable, **kwargs) -> list[Any]:
    """
    Run multiple functions concurrently.

    Args:
        *funcs: Functions to run (can be sync or async)
        **kwargs: Keyword arguments passed to all functions

    Returns:
        List of results in order of functions
    """

    async def wrap_func(func):
        if inspect.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            return func(**kwargs)

    tasks = [wrap_func(func) for func in funcs]
    return await asyncio.gather(*tasks)


def to_async(func: Callable) -> Callable:
    """
    Decorator to wrap sync function for use in async context.

    Args:
        func: Synchronous function

    Returns:
        Async wrapper function
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return async_wrapper


def to_sync(func: Callable) -> Callable:
    """
    Decorator to run async function in sync context.

    Args:
        func: Async function

    Returns:
        Sync wrapper function
    """

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return sync_wrapper
