"""
Structured logging package for SEO Health Report.

Provides JSON-formatted logging with request correlation for production observability.

Usage:
    from packages.seo_health_report.seo_logging import get_logger, set_request_context

    logger = get_logger(__name__)
    logger.info("Processing audit", extra_data={"audit_id": "123", "tier": "pro"})

Middleware:
    from packages.seo_health_report.seo_logging import RequestLoggingMiddleware

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
"""

from .middleware import (
    RequestLoggingMiddleware,
    UserContextMiddleware,
    configure_uvicorn_logging,
)
from .structured_logger import (
    JSONFormatter,
    StructuredLogger,
    clear_request_context,
    get_log_level,
    get_logger,
    is_json_logging_enabled,
    log_with_context,
    request_id_var,
    set_request_context,
    tenant_id_var,
    user_id_var,
)

__all__ = [
    "JSONFormatter",
    "StructuredLogger",
    "RequestLoggingMiddleware",
    "UserContextMiddleware",
    "clear_request_context",
    "configure_uvicorn_logging",
    "get_log_level",
    "get_logger",
    "is_json_logging_enabled",
    "log_with_context",
    "request_id_var",
    "set_request_context",
    "tenant_id_var",
    "user_id_var",
]
