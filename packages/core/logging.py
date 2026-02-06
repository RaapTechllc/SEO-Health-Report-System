"""
Structured logging configuration for the SEO Health Report System.

Uses structlog for JSON output in production and colored console in development.
Includes request ID correlation for tracing requests across services.
"""

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

# Request ID context variable for cross-service correlation
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set the request ID for the current context. Returns the request ID."""
    rid = request_id or str(uuid.uuid4())
    request_id_var.set(rid)
    return rid


def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return request_id_var.get()


def add_request_id(logger, method_name, event_dict):
    """Structlog processor to add request_id to log entries."""
    rid = request_id_var.get()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def add_service_info(logger, method_name, event_dict):
    """Structlog processor to add service metadata."""
    event_dict["service"] = os.getenv("SERVICE_NAME", "seo-health-report")
    event_dict["environment"] = os.getenv("APP_ENV", "development")
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    json_output: Optional[bool] = None,
    service_name: str = "seo-health-report",
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Force JSON output. If None, auto-detect (JSON in production, console in dev).
        service_name: Service name to include in log entries.
    """
    try:
        import structlog

        if json_output is None:
            app_env = os.getenv("APP_ENV", "development").lower()
            json_output = app_env in ("production", "prod", "staging")

        os.environ.setdefault("SERVICE_NAME", service_name)

        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            add_request_id,
            add_service_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
        ]

        if json_output:
            renderer = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.dev.ConsoleRenderer(colors=True)

        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Quiet noisy loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    except ImportError:
        # Fallback if structlog not installed
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        logging.getLogger(__name__).warning(
            "structlog not installed, using basic logging. Install with: pip install structlog"
        )


def setup_sentry(dsn: Optional[str] = None) -> None:
    """
    Optional Sentry integration for error tracking.

    Args:
        dsn: Sentry DSN. If None, reads from SENTRY_DSN env var.
    """
    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        return

    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("APP_ENV", "development"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_RATE", "0.1")),
        )
    except ImportError:
        logging.getLogger(__name__).info("sentry-sdk not installed, Sentry integration disabled")


__all__ = [
    "setup_logging",
    "setup_sentry",
    "set_request_id",
    "get_request_id",
    "request_id_var",
]
