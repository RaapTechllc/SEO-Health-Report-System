"""
Idempotency key computation utility for audit request deduplication.

This module provides functions to generate deterministic hashes for audit requests,
enabling deduplication and caching of identical audit operations.
"""

import hashlib
import json
from urllib.parse import parse_qs, urlencode, urlparse


def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL for consistent hashing.

    Applies the following normalization rules:
    1. Lowercase scheme and host
    2. Strip default ports (80 for http, 443 for https)
    3. Normalize trailing slash (remove except for root path)
    4. Remove fragments (#...)
    5. Sort query parameters

    Args:
        url: The URL to canonicalize.

    Returns:
        A normalized URL string suitable for consistent hashing.

    Examples:
        >>> canonicalize_url("HTTPS://Example.COM:443/path/")
        'https://example.com/path'
        >>> canonicalize_url("http://site.com/page?b=2&a=1")
        'http://site.com/page?a=1&b=2'
        >>> canonicalize_url("https://site.com/#section")
        'https://site.com/'
    """
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower() if parsed.hostname else ""

    port = parsed.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None

    path = parsed.path.rstrip("/") or "/"

    query_params = parse_qs(parsed.query, keep_blank_values=True)
    sorted_query = urlencode(sorted(query_params.items()), doseq=True) if query_params else ""

    netloc = host + (f":{port}" if port else "")
    return f"{scheme}://{netloc}{path}" + (f"?{sorted_query}" if sorted_query else "")


def compute_idempotency_key(
    tenant_id: str,
    target_url: str,
    options: dict,
    recipe_version: str = "v1"
) -> str:
    """
    Compute deterministic hash for audit request deduplication.

    Generates a consistent SHA256 hash based on the tenant, target URL,
    audit options, and recipe version. The same inputs will always produce
    the same hash, enabling request deduplication.

    Args:
        tenant_id: Unique identifier for the tenant/customer.
        target_url: The URL being audited (will be canonicalized).
        options: Dictionary of audit options/configuration.
        recipe_version: Version of the audit recipe (default: "v1").

    Returns:
        A 64-character hex string (SHA256 hash).

    Examples:
        >>> compute_idempotency_key("tenant-123", "https://example.com", {"depth": 3}, "v1")
        'a1b2c3...'  # 64-character hex string
    """
    canonical_url = canonicalize_url(target_url)

    cleaned_options = {k: v for k, v in options.items() if v is not None}
    canonical_options = json.dumps(cleaned_options, sort_keys=True, default=str)

    payload = f"{tenant_id}|{canonical_url}|{canonical_options}|{recipe_version}"
    return hashlib.sha256(payload.encode()).hexdigest()


__all__ = ["canonicalize_url", "compute_idempotency_key"]
