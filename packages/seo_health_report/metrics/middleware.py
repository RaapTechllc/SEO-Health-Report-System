"""
Metrics collection middleware for FastAPI/Starlette applications.

Automatically collects HTTP request metrics with minimal overhead.
"""

import time
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .collector import metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects HTTP request metrics.

    Metrics collected:
    - http_requests_total{method, path, status} - Request counter
    - http_request_duration_seconds{method, path} - Request latency histogram

    Usage:
        from fastapi import FastAPI
        from packages.seo_health_report.metrics.middleware import MetricsMiddleware

        app = FastAPI()
        app.add_middleware(MetricsMiddleware)
    """

    SKIP_PATHS: set[str] = {"/metrics", "/health", "/favicon.ico"}

    def __init__(
        self,
        app,
        skip_paths: Optional[set[str]] = None,
        normalize_paths: bool = True,
    ):
        """
        Initialize metrics middleware.

        Args:
            app: ASGI application
            skip_paths: Paths to exclude from metrics collection
            normalize_paths: If True, normalize paths with UUIDs/IDs to reduce cardinality
        """
        super().__init__(app)
        self.skip_paths = skip_paths or self.SKIP_PATHS
        self.normalize_paths = normalize_paths

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if path in self.skip_paths:
            return await call_next(request)

        normalized_path = self._normalize_path(path) if self.normalize_paths else path
        method = request.method

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start_time

            metrics.inc_counter(
                "http_requests_total",
                labels={"method": method, "path": normalized_path, "status": status},
            )

            metrics.observe_histogram(
                "http_request_duration_seconds",
                duration,
                labels={"method": method, "path": normalized_path},
            )

        return response

    def _normalize_path(self, path: str) -> str:
        """
        Normalize paths to reduce metric cardinality.

        Replaces UUIDs, numeric IDs, and other variable path segments with placeholders.

        Examples:
            /audit/abc123 -> /audit/{id}
            /users/550e8400-e29b-41d4-a716-446655440000 -> /users/{id}
            /reports/2024/01/15 -> /reports/{date}
        """
        import re

        parts = path.split("/")
        normalized = []

        for part in parts:
            if not part:
                normalized.append(part)
                continue

            # UUID pattern
            if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', part, re.I):
                normalized.append("{id}")
            # Hex ID (12+ chars)
            elif re.match(r'^[0-9a-f]{12,}$', part, re.I):
                normalized.append("{id}")
            # Numeric ID
            elif re.match(r'^\d+$', part):
                normalized.append("{id}")
            # Prefixed ID (e.g., audit_abc123, pay_xyz789)
            elif re.match(r'^[a-z]+_[a-z0-9]+$', part, re.I):
                normalized.append("{id}")
            # Date pattern (YYYY-MM-DD or YYYY/MM/DD)
            elif re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', part):
                normalized.append("{date}")
            else:
                normalized.append(part)

        return "/".join(normalized)


def create_metrics_endpoint():
    """
    Create a metrics endpoint handler for FastAPI.

    Usage:
        from fastapi import FastAPI
        from packages.seo_health_report.metrics.middleware import create_metrics_endpoint

        app = FastAPI()
        app.get("/metrics")(create_metrics_endpoint())

    Returns:
        Async function that returns Prometheus-formatted metrics
    """
    async def metrics_endpoint() -> Response:
        from starlette.responses import PlainTextResponse

        content = metrics.prometheus_format()
        return PlainTextResponse(
            content=content,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return metrics_endpoint


async def get_metrics() -> Response:
    """
    Direct endpoint handler for /metrics.

    Usage:
        from fastapi import FastAPI
        from packages.seo_health_report.metrics.middleware import get_metrics

        app = FastAPI()
        app.get("/metrics")(get_metrics)
    """
    from starlette.responses import PlainTextResponse

    content = metrics.prometheus_format()
    return PlainTextResponse(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
