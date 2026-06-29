"""Root-level shim — canonical code lives in packages/rate_limiter/."""

from packages.rate_limiter import *  # noqa: F401,F403
from packages.rate_limiter import (  # noqa: F401
    ENDPOINT_LIMITS,
    TIER_LIMITS,
    RateLimitMiddleware,
    _audit_counts,
    _endpoint_counts,
    _request_counts,
    add_rate_limit_headers,
    check_audit_limit,
    check_endpoint_limit,
    check_rate_limit,
    get_client_ip,
    get_rate_limit_status,
    get_remaining_requests,
    get_reset_time,
    get_tier_limits,
)
