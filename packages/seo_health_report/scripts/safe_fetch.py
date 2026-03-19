"""Backwards-compatible re-export. Use packages.core.safe_fetch directly."""

from packages.core.safe_fetch import (  # noqa: F401
    FetchResult,
    SSRFError,
    SSRFProtectionError,
    resolve_dns,
    safe_fetch,
    safe_get,
    validate_ip,
    validate_url,
)
