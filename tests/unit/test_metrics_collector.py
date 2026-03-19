"""
Tests for metrics collection system.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.seo_health_report.metrics.collector import (
    HistogramBuckets,
    MetricsRegistry,
    Timer,
    metrics,
)


class TestMetricsRegistry:
    """Tests for MetricsRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return MetricsRegistry()

    def test_counter_increment(self, registry):
        """Test counter increment."""
        registry.inc_counter("test_counter")
        assert registry.get_counter("test_counter") == 1.0

        registry.inc_counter("test_counter")
        assert registry.get_counter("test_counter") == 2.0

    def test_counter_increment_by_value(self, registry):
        """Test counter increment with custom value."""
        registry.inc_counter("test_counter", value=5.0)
        assert registry.get_counter("test_counter") == 5.0

        registry.inc_counter("test_counter", value=3.5)
        assert registry.get_counter("test_counter") == 8.5

    def test_counter_with_labels(self, registry):
        """Test counter with labels."""
        registry.inc_counter("requests", labels={"method": "GET", "status": "200"})
        registry.inc_counter("requests", labels={"method": "POST", "status": "201"})
        registry.inc_counter("requests", labels={"method": "GET", "status": "200"})

        assert registry.get_counter("requests", {"method": "GET", "status": "200"}) == 2.0
        assert registry.get_counter("requests", {"method": "POST", "status": "201"}) == 1.0

    def test_gauge_set(self, registry):
        """Test gauge set."""
        registry.set_gauge("active_connections", 10)
        assert registry.get_gauge("active_connections") == 10

        registry.set_gauge("active_connections", 5)
        assert registry.get_gauge("active_connections") == 5

    def test_gauge_increment(self, registry):
        """Test gauge increment."""
        registry.set_gauge("queue_size", 5)
        registry.inc_gauge("queue_size")
        assert registry.get_gauge("queue_size") == 6

        registry.inc_gauge("queue_size", value=3)
        assert registry.get_gauge("queue_size") == 9

    def test_gauge_decrement(self, registry):
        """Test gauge decrement."""
        registry.set_gauge("queue_size", 10)
        registry.dec_gauge("queue_size")
        assert registry.get_gauge("queue_size") == 9

        registry.dec_gauge("queue_size", value=4)
        assert registry.get_gauge("queue_size") == 5

    def test_gauge_with_labels(self, registry):
        """Test gauge with labels."""
        registry.set_gauge("cpu_usage", 50.5, labels={"core": "0"})
        registry.set_gauge("cpu_usage", 75.2, labels={"core": "1"})

        assert registry.get_gauge("cpu_usage", {"core": "0"}) == 50.5
        assert registry.get_gauge("cpu_usage", {"core": "1"}) == 75.2

    def test_histogram_observe(self, registry):
        """Test histogram observation."""
        registry.observe_histogram("request_duration", 0.1)
        registry.observe_histogram("request_duration", 0.2)
        registry.observe_histogram("request_duration", 0.15)

        stats = registry.get_histogram_stats("request_duration")
        assert stats["count"] == 3
        assert abs(stats["sum"] - 0.45) < 0.001

    def test_histogram_with_labels(self, registry):
        """Test histogram with labels."""
        registry.observe_histogram("duration", 0.1, labels={"method": "GET"})
        registry.observe_histogram("duration", 0.2, labels={"method": "GET"})
        registry.observe_histogram("duration", 0.5, labels={"method": "POST"})

        get_stats = registry.get_histogram_stats("duration", {"method": "GET"})
        assert get_stats["count"] == 2

        post_stats = registry.get_histogram_stats("duration", {"method": "POST"})
        assert post_stats["count"] == 1

    def test_histogram_buckets(self, registry):
        """Test histogram bucket calculation."""
        registry.register_histogram("test_hist", buckets=(0.1, 0.5, 1.0))

        registry.observe_histogram("test_hist", 0.05)
        registry.observe_histogram("test_hist", 0.3)
        registry.observe_histogram("test_hist", 0.7)
        registry.observe_histogram("test_hist", 1.5)

        stats = registry.get_histogram_stats("test_hist")
        assert stats["count"] == 4
        assert stats["buckets"][0.1] == 1  # 0.05 <= 0.1
        assert stats["buckets"][0.5] == 2  # 0.05, 0.3 <= 0.5
        assert stats["buckets"][1.0] == 3  # 0.05, 0.3, 0.7 <= 1.0
        assert stats["buckets"][float("inf")] == 4  # all values

    def test_reset(self, registry):
        """Test registry reset."""
        registry.inc_counter("counter1")
        registry.set_gauge("gauge1", 10)
        registry.observe_histogram("hist1", 0.5)

        registry.reset()

        assert registry.get_counter("counter1") == 0
        assert registry.get_gauge("gauge1") == 0
        assert registry.get_histogram_stats("hist1")["count"] == 0

    def test_make_key_without_labels(self, registry):
        """Test key creation without labels."""
        key = registry._make_key("test_metric")
        assert key == "test_metric"

    def test_make_key_with_labels(self, registry):
        """Test key creation with labels."""
        key = registry._make_key("test_metric", {"b": "2", "a": "1"})
        assert key == 'test_metric{a="1",b="2"}'

    def test_extract_base_name(self, registry):
        """Test base name extraction."""
        assert registry._extract_base_name("metric") == "metric"
        assert registry._extract_base_name('metric{label="value"}') == "metric"


class TestPrometheusFormat:
    """Tests for Prometheus format output."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return MetricsRegistry()

    def test_counter_format(self, registry):
        """Test counter Prometheus format."""
        registry.register_counter("test_counter", "A test counter")
        registry.inc_counter("test_counter")

        output = registry.prometheus_format()

        assert "# HELP test_counter A test counter" in output
        assert "# TYPE test_counter counter" in output
        assert "test_counter 1" in output

    def test_counter_with_labels_format(self, registry):
        """Test counter with labels in Prometheus format."""
        registry.inc_counter("requests", labels={"method": "GET", "status": "200"})

        output = registry.prometheus_format()

        assert 'requests{method="GET",status="200"} 1' in output

    def test_gauge_format(self, registry):
        """Test gauge Prometheus format."""
        registry.register_gauge("active_connections", "Current active connections")
        registry.set_gauge("active_connections", 42)

        output = registry.prometheus_format()

        assert "# HELP active_connections Current active connections" in output
        assert "# TYPE active_connections gauge" in output
        assert "active_connections 42" in output

    def test_histogram_format(self, registry):
        """Test histogram Prometheus format."""
        registry.register_histogram("duration", "Request duration", buckets=(0.1, 0.5, 1.0))
        registry.observe_histogram("duration", 0.05)
        registry.observe_histogram("duration", 0.3)

        output = registry.prometheus_format()

        assert "# TYPE duration histogram" in output
        assert 'duration_bucket{le="0.1"} 1' in output
        assert 'duration_bucket{le="0.5"} 2' in output
        assert 'duration_bucket{le="1.0"} 2' in output
        assert 'duration_bucket{le="+Inf"} 2' in output
        assert "duration_sum" in output
        assert "duration_count 2" in output

    def test_empty_registry_format(self, registry):
        """Test empty registry returns empty string."""
        output = registry.prometheus_format()
        assert output == ""

    def test_multiple_metrics_format(self, registry):
        """Test multiple metrics in output."""
        registry.inc_counter("counter1")
        registry.set_gauge("gauge1", 10)

        output = registry.prometheus_format()

        assert "counter1 1" in output
        assert "gauge1 10" in output


class TestTimer:
    """Tests for Timer context manager."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return MetricsRegistry()

    def test_timer_records_duration(self, registry):
        """Test that timer records duration."""
        with Timer(registry, "test_duration"):
            time.sleep(0.01)

        stats = registry.get_histogram_stats("test_duration")
        assert stats["count"] == 1
        assert stats["sum"] >= 0.01

    def test_timer_with_labels(self, registry):
        """Test timer with labels."""
        with Timer(registry, "operation_duration", {"op": "read"}):
            time.sleep(0.005)

        stats = registry.get_histogram_stats("operation_duration", {"op": "read"})
        assert stats["count"] == 1

    def test_timer_on_exception(self, registry):
        """Test that timer still records on exception."""
        try:
            with Timer(registry, "failing_operation"):
                time.sleep(0.005)
                raise ValueError("Test error")
        except ValueError:
            pass

        stats = registry.get_histogram_stats("failing_operation")
        assert stats["count"] == 1


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_counter_increments(self):
        """Test concurrent counter increments."""
        registry = MetricsRegistry()

        def increment_many():
            for _ in range(1000):
                registry.inc_counter("concurrent_counter")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(increment_many) for _ in range(10)]
            for f in futures:
                f.result()

        assert registry.get_counter("concurrent_counter") == 10000

    def test_concurrent_gauge_updates(self):
        """Test concurrent gauge updates don't crash."""
        registry = MetricsRegistry()
        registry.set_gauge("concurrent_gauge", 0)

        def update_gauge():
            for _i in range(100):
                registry.inc_gauge("concurrent_gauge")
                registry.dec_gauge("concurrent_gauge")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(update_gauge) for _ in range(10)]
            for f in futures:
                f.result()

        # After equal increments and decrements, should be 0
        assert registry.get_gauge("concurrent_gauge") == 0


class TestHistogramBuckets:
    """Tests for histogram bucket configurations."""

    def test_http_latency_buckets(self):
        """Test HTTP latency bucket defaults."""
        buckets = HistogramBuckets.HTTP_LATENCY
        assert 0.01 in buckets
        assert 0.1 in buckets
        assert 1.0 in buckets

    def test_audit_duration_buckets(self):
        """Test audit duration bucket defaults."""
        buckets = HistogramBuckets.AUDIT_DURATION
        assert 60.0 in buckets  # 1 minute
        assert 300.0 in buckets  # 5 minutes
        assert 3600.0 in buckets  # 1 hour


class TestGlobalMetrics:
    """Tests for global metrics singleton."""

    def test_global_metrics_exists(self):
        """Test global metrics registry exists."""
        assert metrics is not None
        assert isinstance(metrics, MetricsRegistry)

    def test_preregistered_metrics(self):
        """Test that standard metrics are pre-registered."""
        # These should not raise errors
        metrics.inc_counter("http_requests_total", labels={"method": "GET", "path": "/", "status": "200"})
        metrics.observe_histogram("http_request_duration_seconds", 0.1)
        metrics.set_gauge("active_audits", 5)

        # Cleanup
        metrics.reset()


class TestPerformance:
    """Performance tests for metrics collection."""

    def test_counter_increment_overhead(self):
        """Test counter increment is fast (<1ms for 1000 operations)."""
        registry = MetricsRegistry()

        start = time.perf_counter()
        for _ in range(1000):
            registry.inc_counter("perf_test", labels={"method": "GET"})
        duration = time.perf_counter() - start

        # 1000 operations should complete in <100ms
        assert duration < 0.1, f"Counter increment too slow: {duration:.3f}s for 1000 ops"

    def test_histogram_observe_overhead(self):
        """Test histogram observe is fast."""
        registry = MetricsRegistry()

        start = time.perf_counter()
        for _ in range(1000):
            registry.observe_histogram("perf_hist", 0.1, labels={"path": "/api"})
        duration = time.perf_counter() - start

        assert duration < 0.1, f"Histogram observe too slow: {duration:.3f}s for 1000 ops"

    def test_prometheus_format_overhead(self):
        """Test Prometheus format generation is fast."""
        registry = MetricsRegistry()

        # Add some metrics
        for i in range(100):
            registry.inc_counter("counter", labels={"id": str(i)})
            registry.observe_histogram("hist", i * 0.01)

        start = time.perf_counter()
        for _ in range(100):
            registry.prometheus_format()
        duration = time.perf_counter() - start

        assert duration < 1.0, f"Prometheus format too slow: {duration:.3f}s for 100 calls"
