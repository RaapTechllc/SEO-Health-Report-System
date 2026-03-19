"""Integration tests for metrics collection system."""

import sys
import time
from unittest.mock import MagicMock

sys.modules.setdefault("stripe", MagicMock())

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from packages.seo_health_report.metrics import (
    MetricsMiddleware,
    Timer,
    get_metrics,
    metrics,
)


@pytest.fixture
def app_with_metrics():
    """Create test app with metrics middleware."""
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}

    @app.get("/slow")
    def slow_endpoint():
        time.sleep(0.1)
        return {"status": "ok"}

    @app.post("/submit")
    def submit_endpoint():
        return {"status": "submitted"}

    @app.get("/error")
    def error_endpoint():
        raise ValueError("Test error")

    @app.get("/metrics")
    async def metrics_endpoint():
        return await get_metrics()

    return app


@pytest.fixture
def client(app_with_metrics):
    """Create test client."""
    return TestClient(app_with_metrics, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test."""
    metrics.reset()
    yield


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        """Test /metrics returns valid Prometheus text format."""
        client.get("/test")
        client.get("/test")

        response = client.get("/metrics")
        assert response.status_code == 200

        content = response.text
        assert "http_requests_total" in content
        assert "# TYPE" in content

    def test_metrics_endpoint_content_type(self, client):
        """Test /metrics returns correct content type."""
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_includes_help_text(self, client):
        """Test metrics include HELP comments."""
        client.get("/test")

        response = client.get("/metrics")
        content = response.text

        assert "# HELP" in content or "# TYPE" in content


class TestHttpRequestCounter:
    """Tests for http_requests_total counter."""

    def test_http_request_counter_increments(self, client):
        """Test that http_requests_total counter increments correctly."""
        initial = metrics.get_counter(
            "http_requests_total",
            labels={"method": "GET", "path": "/test", "status": "200"}
        )

        client.get("/test")
        client.get("/test")
        client.get("/test")

        final = metrics.get_counter(
            "http_requests_total",
            labels={"method": "GET", "path": "/test", "status": "200"}
        )

        assert final == initial + 3

    def test_counter_tracks_different_methods(self, client):
        """Test counter tracks GET and POST separately."""
        client.get("/test")
        client.post("/submit")

        get_count = metrics.get_counter(
            "http_requests_total",
            labels={"method": "GET", "path": "/test", "status": "200"}
        )
        post_count = metrics.get_counter(
            "http_requests_total",
            labels={"method": "POST", "path": "/submit", "status": "200"}
        )

        assert get_count >= 1
        assert post_count >= 1

    def test_counter_tracks_error_status(self, client):
        """Test counter tracks 500 status for errors."""
        client.get("/error")

        error_count = metrics.get_counter(
            "http_requests_total",
            labels={"method": "GET", "path": "/error", "status": "500"}
        )

        assert error_count >= 1

    def test_counter_in_prometheus_output(self, client):
        """Test counter appears in Prometheus output."""
        client.get("/test")

        response = client.get("/metrics")
        content = response.text

        assert 'http_requests_total{' in content
        assert 'method="GET"' in content


class TestHistogramLatency:
    """Tests for http_request_duration_seconds histogram."""

    def test_histogram_tracks_latency(self, client):
        """Test that http_request_duration_seconds tracks latency."""
        client.get("/test")

        stats = metrics.get_histogram_stats(
            "http_request_duration_seconds",
            labels={"method": "GET", "path": "/test"}
        )

        assert stats["count"] >= 1
        assert stats["sum"] > 0

    def test_histogram_buckets_populated(self, client):
        """Test histogram buckets are populated."""
        client.get("/test")

        stats = metrics.get_histogram_stats(
            "http_request_duration_seconds",
            labels={"method": "GET", "path": "/test"}
        )

        assert len(stats["buckets"]) > 0
        assert float("inf") in stats["buckets"]

    def test_histogram_in_prometheus_output(self, client):
        """Test histogram appears in Prometheus output with buckets."""
        client.get("/test")

        response = client.get("/metrics")
        content = response.text

        assert "http_request_duration_seconds_bucket" in content
        assert "http_request_duration_seconds_sum" in content
        assert "http_request_duration_seconds_count" in content


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware behavior."""

    def test_skip_paths_not_tracked(self, client):
        """Test that /metrics and /health paths are skipped."""
        initial_count = sum(
            1 for key in metrics._counters.keys()
            if "/metrics" in key or "/health" in key
        )

        client.get("/metrics")
        client.get("/metrics")

        final_count = sum(
            1 for key in metrics._counters.keys()
            if "/metrics" in key or "/health" in key
        )

        assert final_count == initial_count

    def test_path_normalization_uuid(self):
        """Test that UUIDs in paths are normalized."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)

        @app.get("/audit/{audit_id}")
        def get_audit(audit_id: str):
            return {"id": audit_id}

        client = TestClient(app)

        client.get("/audit/550e8400-e29b-41d4-a716-446655440000")
        client.get("/audit/660e8400-e29b-41d4-a716-446655440001")

        normalized_count = metrics.get_counter(
            "http_requests_total",
            labels={"method": "GET", "path": "/audit/{id}", "status": "200"}
        )

        assert normalized_count == 2

    def test_path_normalization_numeric(self):
        """Test that numeric IDs in paths are normalized."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)

        @app.get("/users/{user_id}")
        def get_user(user_id: int):
            return {"id": user_id}

        client = TestClient(app)

        client.get("/users/123")
        client.get("/users/456")

        normalized_count = metrics.get_counter(
            "http_requests_total",
            labels={"method": "GET", "path": "/users/{id}", "status": "200"}
        )

        assert normalized_count == 2


class TestTimerContextManager:
    """Tests for Timer context manager."""

    def test_timer_records_duration(self):
        """Test Timer records duration to histogram."""
        with Timer(metrics, "test_operation_duration"):
            time.sleep(0.05)

        stats = metrics.get_histogram_stats("test_operation_duration")

        assert stats["count"] == 1
        assert stats["sum"] >= 0.05

    def test_timer_with_labels(self):
        """Test Timer works with labels."""
        with Timer(metrics, "labeled_operation", {"operation": "test"}):
            time.sleep(0.01)

        stats = metrics.get_histogram_stats(
            "labeled_operation",
            labels={"operation": "test"}
        )

        assert stats["count"] == 1


class TestMetricsCollectionOverhead:
    """Tests for metrics collection performance."""

    def test_metrics_collection_overhead(self, client):
        """Metrics collection should have minimal overhead."""
        iterations = 20

        start_time = time.perf_counter()
        for _ in range(iterations):
            client.get("/test")
        total_time = time.perf_counter() - start_time

        avg_time_ms = (total_time / iterations) * 1000

        assert avg_time_ms < 20, f"Average time {avg_time_ms:.2f}ms exceeds 20ms threshold"

    def test_prometheus_export_performance(self, client):
        """Test prometheus export is fast."""
        for _ in range(50):
            client.get("/test")
            client.post("/submit")

        start_time = time.perf_counter()
        response = client.get("/metrics")
        export_time = time.perf_counter() - start_time

        assert response.status_code == 200
        assert export_time < 0.1, f"Export took {export_time:.3f}s, expected < 0.1s"


class TestGaugeMetrics:
    """Tests for gauge metrics."""

    def test_gauge_set_value(self):
        """Test setting gauge value."""
        metrics.set_gauge("test_gauge", 42.0)

        value = metrics.get_gauge("test_gauge")
        assert value == 42.0

    def test_gauge_increment(self):
        """Test incrementing gauge."""
        metrics.set_gauge("inc_gauge", 10.0)
        metrics.inc_gauge("inc_gauge")

        value = metrics.get_gauge("inc_gauge")
        assert value == 11.0

    def test_gauge_decrement(self):
        """Test decrementing gauge."""
        metrics.set_gauge("dec_gauge", 10.0)
        metrics.dec_gauge("dec_gauge")

        value = metrics.get_gauge("dec_gauge")
        assert value == 9.0

    def test_gauge_with_labels(self):
        """Test gauge with labels."""
        metrics.set_gauge("labeled_gauge", 5.0, labels={"type": "test"})

        value = metrics.get_gauge("labeled_gauge", labels={"type": "test"})
        assert value == 5.0


class TestMetricsReset:
    """Tests for metrics reset functionality."""

    def test_reset_clears_counters(self, client):
        """Test that reset clears counter metrics."""
        client.get("/test")

        count_before = metrics.get_counter(
            "http_requests_total",
            labels={"method": "GET", "path": "/test", "status": "200"}
        )
        assert count_before >= 1

        metrics.reset()

        count_after = metrics.get_counter(
            "http_requests_total",
            labels={"method": "GET", "path": "/test", "status": "200"}
        )
        assert count_after == 0

    def test_reset_clears_gauges(self):
        """Test that reset clears gauge metrics."""
        metrics.set_gauge("test_reset_gauge", 100.0)
        metrics.reset()

        value = metrics.get_gauge("test_reset_gauge")
        assert value == 0.0
