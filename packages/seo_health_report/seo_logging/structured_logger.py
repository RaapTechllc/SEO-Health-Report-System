"""
Structured JSON logging for production observability.

Provides JSON-formatted logs with request correlation via context variables.
"""

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="")


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON with correlation context.

    Output format:
    {
        "timestamp": "2026-01-18T12:00:00.000Z",
        "level": "INFO",
        "logger": "seo_health_report.audit",
        "message": "Audit started",
        "request_id": "abc-123",
        "user_id": "user-456",
        "tenant_id": "tenant-789",
        "extra": {...}
    }
    """

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if request_id := request_id_var.get():
            log_data["request_id"] = request_id

        if user_id := user_id_var.get():
            log_data["user_id"] = user_id

        if tenant_id := tenant_id_var.get():
            log_data["tenant_id"] = tenant_id

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None

        if self.include_extra and hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        if record.levelno >= logging.WARNING:
            log_data["location"] = f"{record.pathname}:{record.lineno}"
            log_data["function"] = record.funcName

        return json.dumps(log_data, default=str)


class StructuredLogger(logging.Logger):
    """
    Logger that supports structured extra data.

    Usage:
        logger = get_logger("my.module")
        logger.info("User logged in", extra_data={"method": "oauth", "provider": "google"})
    """

    def _log(
        self,
        level: int,
        msg: object,
        args: tuple,
        exc_info: Optional[Any] = None,
        extra: Optional[dict] = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        **kwargs,
    ) -> None:
        if extra is None:
            extra = {}

        if "extra_data" in kwargs:
            extra["extra_data"] = kwargs.pop("extra_data")

        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel + 1)


logging.setLoggerClass(StructuredLogger)

_loggers: dict[str, logging.Logger] = {}
_is_json_mode: Optional[bool] = None


def is_json_logging_enabled() -> bool:
    """Check if JSON logging is enabled based on environment."""
    global _is_json_mode
    if _is_json_mode is None:
        env = os.environ.get("APP_ENV", "development").lower()
        force_json = os.environ.get("LOG_FORMAT", "").lower() == "json"
        _is_json_mode = force_json or env in ("production", "prod", "staging", "stage", "stg")
    return _is_json_mode


def get_log_level() -> int:
    """Get log level from environment."""
    level_str = os.environ.get("SEO_HEALTH_LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_str, logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    In production/staging: Returns JSON-formatted logger
    In development: Returns human-readable formatted logger

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        if is_json_logging_enabled():
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))

        logger.addHandler(handler)
        logger.setLevel(get_log_level())
        logger.propagate = False

    _loggers[name] = logger
    return logger


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> None:
    """
    Set request context for log correlation.

    Args:
        request_id: Unique request identifier
        user_id: Authenticated user ID
        tenant_id: Tenant/organization ID
    """
    if request_id is not None:
        request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)
    if tenant_id is not None:
        tenant_id_var.set(tenant_id)


def clear_request_context() -> None:
    """Clear request context after request completes."""
    request_id_var.set("")
    user_id_var.set("")
    tenant_id_var.set("")


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra_data,
) -> None:
    """
    Log a message with additional structured data.

    Args:
        logger: Logger instance
        level: Log level (logging.INFO, etc.)
        message: Log message
        **extra_data: Additional fields to include in log
    """
    record = logger.makeRecord(
        logger.name,
        level,
        "(unknown)",
        0,
        message,
        (),
        None,
    )
    record.extra_data = extra_data
    logger.handle(record)
