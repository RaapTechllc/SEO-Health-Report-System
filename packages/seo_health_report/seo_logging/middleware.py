"""
Logging middleware for FastAPI/Starlette applications.

Provides request ID propagation and automatic request/response logging.
"""

import time
import uuid
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .structured_logger import (
    clear_request_context,
    get_logger,
    set_request_context,
    tenant_id_var,
    user_id_var,
)

logger = get_logger("seo_health_report.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Generates/propagates X-Request-ID header
    2. Sets request context for log correlation
    3. Logs request start and completion with timing

    Usage:
        from fastapi import FastAPI
        from packages.seo_health_report.seo_logging.middleware import RequestLoggingMiddleware

        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
    """

    SKIP_PATHS = {"/health", "/metrics", "/favicon.ico"}

    def __init__(
        self,
        app,
        skip_paths: Optional[set] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        super().__init__(app)
        self.skip_paths = skip_paths or self.SKIP_PATHS
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        user_id = getattr(request.state, "user_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)

        set_request_context(
            request_id=request_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        path = request.url.path
        should_log = path not in self.skip_paths

        if should_log:
            log_data = {
                "method": request.method,
                "path": path,
                "query": str(request.query_params) if request.query_params else None,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", "")[:200],
            }
            logger.info("request_started", extra_data=log_data)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            response.headers["X-Request-ID"] = request_id

            if should_log:
                log_data = {
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }

                if response.status_code >= 400:
                    logger.warning("request_completed", extra_data=log_data)
                else:
                    logger.info("request_completed", extra_data=log_data)

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.exception(
                "request_failed",
                extra_data={
                    "method": request.method,
                    "path": path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            raise

        finally:
            clear_request_context()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts user/tenant from JWT and sets context.

    Should run AFTER authentication middleware.

    Usage:
        app.add_middleware(UserContextMiddleware)
        app.add_middleware(RequestLoggingMiddleware)  # Added first, runs last
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "id"):
                user_id_var.set(str(user.id))
            if hasattr(user, "tenant_id"):
                tenant_id_var.set(str(user.tenant_id))

        return await call_next(request)


def configure_uvicorn_logging():
    """
    Configure uvicorn to use structured logging.

    Call this before starting uvicorn:
        from packages.seo_health_report.seo_logging.middleware import configure_uvicorn_logging
        configure_uvicorn_logging()
        uvicorn.run(app, ...)
    """
    import logging

    from .structured_logger import JSONFormatter, get_log_level, is_json_logging_enabled

    if is_json_logging_enabled():
        for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
            uv_logger = logging.getLogger(logger_name)
            for handler in uv_logger.handlers:
                handler.setFormatter(JSONFormatter())
            uv_logger.setLevel(get_log_level())
