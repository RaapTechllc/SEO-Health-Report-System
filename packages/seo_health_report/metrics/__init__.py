"""
Metrics collection package for SEO Health Report.

Provides in-memory metrics collection with Prometheus-compatible export.

Usage:
    from packages.seo_health_report.metrics import metrics, Timer

    # Counter
    metrics.inc_counter("http_requests_total", labels={"method": "GET", "status": "200"})

    # Histogram
    metrics.observe_histogram("http_request_duration_seconds", 0.125)

    # Gauge
    metrics.set_gauge("active_audits", 5)
    metrics.inc_gauge("active_audits")
    metrics.dec_gauge("active_audits")

    # Timer context manager
    with Timer(metrics, "operation_duration_seconds"):
        do_something()

    # Export to Prometheus format
    print(metrics.prometheus_format())

Middleware:
    from packages.seo_health_report.metrics import MetricsMiddleware, get_metrics

    app = FastAPI()
    app.add_middleware(MetricsMiddleware)
    app.get("/metrics")(get_metrics)
"""

from .collector import (
    HistogramBuckets,
    MetricsRegistry,
    Timer,
    metrics,
)
from .middleware import (
    MetricsMiddleware,
    create_metrics_endpoint,
    get_metrics,
)

__all__ = [
    "HistogramBuckets",
    "MetricsRegistry",
    "MetricsMiddleware",
    "Timer",
    "create_metrics_endpoint",
    "get_metrics",
    "metrics",
]
