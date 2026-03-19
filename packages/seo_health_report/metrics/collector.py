"""
In-memory metrics collection with Prometheus export.

Provides thread-safe Counter, Histogram, and Gauge metrics with minimal overhead.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Optional


@dataclass
class HistogramBuckets:
    """Standard histogram bucket configurations."""

    HTTP_LATENCY = (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
    AUDIT_DURATION = (1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0)


class MetricsRegistry:
    """
    Thread-safe metrics registry with Prometheus-compatible export.

    Supports three metric types:
    - Counter: Monotonically increasing values (e.g., request count)
    - Histogram: Distribution of values with buckets (e.g., latency)
    - Gauge: Point-in-time values that can go up/down (e.g., active connections)

    Usage:
        from packages.seo_health_report.metrics import metrics

        # Counter
        metrics.inc_counter("http_requests_total", labels={"method": "GET", "status": "200"})

        # Histogram
        metrics.observe_histogram("http_request_duration_seconds", 0.125, labels={"method": "GET"})

        # Gauge
        metrics.set_gauge("active_audits", 5)
        metrics.inc_gauge("active_audits")
        metrics.dec_gauge("active_audits")
    """

    def __init__(self):
        self._counters: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._histogram_buckets: dict[str, tuple[float, ...]] = {}
        self._gauges: dict[str, float] = {}
        self._lock = Lock()
        self._metric_help: dict[str, str] = {}
        self._metric_type: dict[str, str] = {}

    def register_counter(self, name: str, help_text: str = "") -> None:
        """Register a counter metric with help text."""
        with self._lock:
            self._metric_type[name] = "counter"
            if help_text:
                self._metric_help[name] = help_text

    def register_histogram(
        self,
        name: str,
        help_text: str = "",
        buckets: tuple[float, ...] = HistogramBuckets.HTTP_LATENCY,
    ) -> None:
        """Register a histogram metric with help text and bucket configuration."""
        with self._lock:
            self._metric_type[name] = "histogram"
            self._histogram_buckets[name] = buckets
            if help_text:
                self._metric_help[name] = help_text

    def register_gauge(self, name: str, help_text: str = "") -> None:
        """Register a gauge metric with help text."""
        with self._lock:
            self._metric_type[name] = "gauge"
            if help_text:
                self._metric_help[name] = help_text

    def inc_counter(self, name: str, labels: Optional[dict[str, str]] = None, value: float = 1.0) -> None:
        """
        Increment a counter by the given value.

        Args:
            name: Metric name
            labels: Optional label key-value pairs
            value: Amount to increment (default: 1)
        """
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Record an observation in a histogram.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional label key-value pairs
        """
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)

    def set_gauge(self, name: str, value: float, labels: Optional[dict[str, str]] = None) -> None:
        """
        Set a gauge to a specific value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional label key-value pairs
        """
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def inc_gauge(self, name: str, labels: Optional[dict[str, str]] = None, value: float = 1.0) -> None:
        """Increment a gauge by the given value."""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = self._gauges.get(key, 0.0) + value

    def dec_gauge(self, name: str, labels: Optional[dict[str, str]] = None, value: float = 1.0) -> None:
        """Decrement a gauge by the given value."""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = self._gauges.get(key, 0.0) - value

    def get_counter(self, name: str, labels: Optional[dict[str, str]] = None) -> float:
        """Get current counter value."""
        key = self._make_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Optional[dict[str, str]] = None) -> float:
        """Get current gauge value."""
        key = self._make_key(name, labels)
        with self._lock:
            return self._gauges.get(key, 0.0)

    def get_histogram_stats(self, name: str, labels: Optional[dict[str, str]] = None) -> dict:
        """Get histogram statistics (count, sum, buckets)."""
        key = self._make_key(name, labels)
        base_name = name.split("{")[0] if "{" in name else name
        buckets = self._histogram_buckets.get(base_name, HistogramBuckets.HTTP_LATENCY)

        with self._lock:
            values = self._histograms.get(key, [])
            if not values:
                return {"count": 0, "sum": 0.0, "buckets": {}}

            bucket_counts = {}
            for le in buckets:
                bucket_counts[le] = sum(1 for v in values if v <= le)
            bucket_counts[float("inf")] = len(values)

            return {
                "count": len(values),
                "sum": sum(values),
                "buckets": bucket_counts,
            }

    def prometheus_format(self) -> str:
        """
        Export all metrics in Prometheus text exposition format.

        Returns:
            String in Prometheus format, ready for /metrics endpoint
        """
        lines = []
        processed_metrics = set()

        with self._lock:
            # Process counters
            for key, value in sorted(self._counters.items()):
                base_name = self._extract_base_name(key)
                if base_name not in processed_metrics:
                    if base_name in self._metric_help:
                        lines.append(f"# HELP {base_name} {self._metric_help[base_name]}")
                    lines.append(f"# TYPE {base_name} counter")
                    processed_metrics.add(base_name)
                lines.append(f"{key} {value}")

            # Process histograms
            histogram_groups: dict[str, list[tuple[str, list[float]]]] = defaultdict(list)
            for key, values in self._histograms.items():
                base_name = self._extract_base_name(key)
                histogram_groups[base_name].append((key, values))

            for base_name, group in sorted(histogram_groups.items()):
                if base_name not in processed_metrics:
                    if base_name in self._metric_help:
                        lines.append(f"# HELP {base_name} {self._metric_help[base_name]}")
                    lines.append(f"# TYPE {base_name} histogram")
                    processed_metrics.add(base_name)

                buckets = self._histogram_buckets.get(base_name, HistogramBuckets.HTTP_LATENCY)

                for key, values in group:
                    if not values:
                        continue

                    # Extract labels from key
                    labels_str = ""
                    if "{" in key:
                        labels_str = key[key.index("{"):key.index("}") + 1]
                        labels_prefix = labels_str[:-1] + "," if labels_str != "{}" else "{"
                    else:
                        labels_prefix = "{"

                    # Output bucket counts
                    for le in buckets:
                        count = sum(1 for v in values if v <= le)
                        le_label = f'le="{le}"'
                        bucket_labels = f"{labels_prefix}{le_label}}}" if labels_prefix != "{" else f"{{{le_label}}}"
                        lines.append(f"{base_name}_bucket{bucket_labels} {count}")

                    # +Inf bucket
                    inf_label = 'le="+Inf"'
                    inf_labels = f"{labels_prefix}{inf_label}}}" if labels_prefix != "{" else f"{{{inf_label}}}"
                    lines.append(f"{base_name}_bucket{inf_labels} {len(values)}")

                    # Sum and count
                    suffix = labels_str if labels_str else ""
                    lines.append(f"{base_name}_sum{suffix} {sum(values)}")
                    lines.append(f"{base_name}_count{suffix} {len(values)}")

            # Process gauges
            for key, value in sorted(self._gauges.items()):
                base_name = self._extract_base_name(key)
                if base_name not in processed_metrics:
                    if base_name in self._metric_help:
                        lines.append(f"# HELP {base_name} {self._metric_help[base_name]}")
                    lines.append(f"# TYPE {base_name} gauge")
                    processed_metrics.add(base_name)
                lines.append(f"{key} {value}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()

    def _make_key(self, name: str, labels: Optional[dict[str, str]] = None) -> str:
        """Create metric key with optional labels."""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _extract_base_name(self, key: str) -> str:
        """Extract base metric name from key with labels."""
        if "{" in key:
            return key[:key.index("{")]
        return key


class Timer:
    """
    Context manager for timing operations and recording to histogram.

    Usage:
        with Timer(metrics, "http_request_duration_seconds", {"method": "GET"}):
            do_something()
    """

    def __init__(
        self,
        registry: MetricsRegistry,
        metric_name: str,
        labels: Optional[dict[str, str]] = None,
    ):
        self.registry = registry
        self.metric_name = metric_name
        self.labels = labels
        self.start_time: float = 0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        duration = time.perf_counter() - self.start_time
        self.registry.observe_histogram(self.metric_name, duration, self.labels)


# Global metrics registry singleton
metrics = MetricsRegistry()

# Pre-register standard metrics
metrics.register_counter(
    "http_requests_total",
    "Total number of HTTP requests"
)
metrics.register_histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    buckets=HistogramBuckets.HTTP_LATENCY,
)
metrics.register_gauge(
    "active_audits",
    "Number of currently running audits"
)
metrics.register_counter(
    "audit_total",
    "Total number of audits by tier and status"
)
metrics.register_histogram(
    "audit_duration_seconds",
    "Audit completion time in seconds",
    buckets=HistogramBuckets.AUDIT_DURATION,
)
metrics.register_counter(
    "webhook_deliveries_total",
    "Total webhook delivery attempts by status"
)
