"""
Tests for audit metrics integration (Task 5.1.3).

Verifies that audit_total, audit_duration_seconds, and active_audits
metrics are properly emitted during audit lifecycle.
"""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.seo_health_report.metrics.collector import MetricsRegistry, metrics


class TestAuditMetricsIntegration:
    """Tests for audit metrics in the audit pipeline."""

    @pytest.fixture
    def fresh_metrics(self):
        """Create a fresh registry for testing."""
        registry = MetricsRegistry()
        registry.register_counter("audit_total", "Total number of audits by tier and status")
        registry.register_histogram(
            "audit_duration_seconds",
            "Audit completion time in seconds",
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0),
        )
        registry.register_gauge("active_audits", "Number of currently running audits")
        return registry

    def test_audit_counter_increment_on_completion(self, fresh_metrics):
        """Test audit_total counter increments on completed audit."""
        fresh_metrics.inc_counter("audit_total", labels={"tier": "basic", "status": "completed"})

        count = fresh_metrics.get_counter("audit_total", {"tier": "basic", "status": "completed"})
        assert count == 1.0

    def test_audit_counter_increment_on_failure(self, fresh_metrics):
        """Test audit_total counter increments on failed audit."""
        fresh_metrics.inc_counter("audit_total", labels={"tier": "pro", "status": "failed"})

        count = fresh_metrics.get_counter("audit_total", {"tier": "pro", "status": "failed"})
        assert count == 1.0

    def test_audit_counter_separates_by_tier(self, fresh_metrics):
        """Test audit_total counter separates by tier."""
        fresh_metrics.inc_counter("audit_total", labels={"tier": "basic", "status": "completed"})
        fresh_metrics.inc_counter("audit_total", labels={"tier": "pro", "status": "completed"})
        fresh_metrics.inc_counter("audit_total", labels={"tier": "basic", "status": "completed"})

        assert fresh_metrics.get_counter("audit_total", {"tier": "basic", "status": "completed"}) == 2.0
        assert fresh_metrics.get_counter("audit_total", {"tier": "pro", "status": "completed"}) == 1.0

    def test_audit_counter_separates_by_status(self, fresh_metrics):
        """Test audit_total counter separates by status."""
        fresh_metrics.inc_counter("audit_total", labels={"tier": "enterprise", "status": "completed"})
        fresh_metrics.inc_counter("audit_total", labels={"tier": "enterprise", "status": "failed"})
        fresh_metrics.inc_counter("audit_total", labels={"tier": "enterprise", "status": "completed"})

        assert fresh_metrics.get_counter("audit_total", {"tier": "enterprise", "status": "completed"}) == 2.0
        assert fresh_metrics.get_counter("audit_total", {"tier": "enterprise", "status": "failed"}) == 1.0

    def test_audit_duration_histogram_records(self, fresh_metrics):
        """Test audit_duration_seconds histogram records duration."""
        fresh_metrics.observe_histogram("audit_duration_seconds", 15.5, labels={"tier": "basic"})
        fresh_metrics.observe_histogram("audit_duration_seconds", 45.2, labels={"tier": "basic"})

        stats = fresh_metrics.get_histogram_stats("audit_duration_seconds", {"tier": "basic"})
        assert stats["count"] == 2
        assert abs(stats["sum"] - 60.7) < 0.001

    def test_audit_duration_histogram_buckets(self, fresh_metrics):
        """Test audit_duration_seconds uses AUDIT_DURATION buckets."""
        fresh_metrics.observe_histogram("audit_duration_seconds", 0.5, labels={"tier": "pro"})
        fresh_metrics.observe_histogram("audit_duration_seconds", 25.0, labels={"tier": "pro"})
        fresh_metrics.observe_histogram("audit_duration_seconds", 150.0, labels={"tier": "pro"})
        fresh_metrics.observe_histogram("audit_duration_seconds", 4000.0, labels={"tier": "pro"})

        stats = fresh_metrics.get_histogram_stats("audit_duration_seconds", {"tier": "pro"})
        buckets = stats["buckets"]

        assert buckets[1.0] == 1
        assert buckets[30.0] == 2
        assert buckets[300.0] == 3
        assert buckets[float("inf")] == 4

    def test_active_audits_gauge_increment(self, fresh_metrics):
        """Test active_audits gauge increments when audit starts."""
        fresh_metrics.inc_gauge("active_audits")
        assert fresh_metrics.get_gauge("active_audits") == 1.0

        fresh_metrics.inc_gauge("active_audits")
        assert fresh_metrics.get_gauge("active_audits") == 2.0

    def test_active_audits_gauge_decrement(self, fresh_metrics):
        """Test active_audits gauge decrements when audit finishes."""
        fresh_metrics.set_gauge("active_audits", 5)
        fresh_metrics.dec_gauge("active_audits")
        assert fresh_metrics.get_gauge("active_audits") == 4.0

    def test_active_audits_gauge_returns_to_zero(self, fresh_metrics):
        """Test active_audits gauge returns to zero when all audits complete."""
        fresh_metrics.inc_gauge("active_audits")
        fresh_metrics.inc_gauge("active_audits")
        fresh_metrics.inc_gauge("active_audits")

        assert fresh_metrics.get_gauge("active_audits") == 3.0

        fresh_metrics.dec_gauge("active_audits")
        fresh_metrics.dec_gauge("active_audits")
        fresh_metrics.dec_gauge("active_audits")

        assert fresh_metrics.get_gauge("active_audits") == 0.0


class TestAuditMetricsPrometheusFormat:
    """Tests for Prometheus format output of audit metrics."""

    @pytest.fixture
    def registry_with_audit_data(self):
        """Create registry with sample audit data."""
        registry = MetricsRegistry()
        registry.register_counter("audit_total", "Total number of audits by tier and status")
        registry.register_histogram(
            "audit_duration_seconds",
            "Audit completion time in seconds",
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0),
        )
        registry.register_gauge("active_audits", "Number of currently running audits")

        registry.inc_counter("audit_total", labels={"tier": "basic", "status": "completed"}, value=10)
        registry.inc_counter("audit_total", labels={"tier": "pro", "status": "failed"}, value=2)
        registry.observe_histogram("audit_duration_seconds", 15.0, labels={"tier": "basic"})
        registry.observe_histogram("audit_duration_seconds", 25.0, labels={"tier": "basic"})
        registry.set_gauge("active_audits", 3)

        return registry

    def test_audit_total_prometheus_format(self, registry_with_audit_data):
        """Test audit_total appears correctly in Prometheus format."""
        output = registry_with_audit_data.prometheus_format()

        assert "# HELP audit_total Total number of audits by tier and status" in output
        assert "# TYPE audit_total counter" in output
        assert 'audit_total{status="completed",tier="basic"} 10' in output
        assert 'audit_total{status="failed",tier="pro"} 2' in output

    def test_audit_duration_prometheus_format(self, registry_with_audit_data):
        """Test audit_duration_seconds appears correctly in Prometheus format."""
        output = registry_with_audit_data.prometheus_format()

        assert "# TYPE audit_duration_seconds histogram" in output
        assert 'audit_duration_seconds_bucket{tier="basic",le="30.0"} 2' in output
        assert 'audit_duration_seconds_count{tier="basic"} 2' in output
        assert "audit_duration_seconds_sum{tier=" in output

    def test_active_audits_prometheus_format(self, registry_with_audit_data):
        """Test active_audits appears correctly in Prometheus format."""
        output = registry_with_audit_data.prometheus_format()

        assert "# HELP active_audits Number of currently running audits" in output
        assert "# TYPE active_audits gauge" in output
        assert "active_audits 3" in output


class TestGlobalMetricsAuditPreregistration:
    """Tests for pre-registered audit metrics in global singleton."""

    def test_audit_total_preregistered(self):
        """Test audit_total is pre-registered in global metrics."""
        metrics.inc_counter("audit_total", labels={"tier": "test", "status": "test"})
        value = metrics.get_counter("audit_total", {"tier": "test", "status": "test"})
        assert value >= 1.0
        metrics.reset()

    def test_audit_duration_preregistered(self):
        """Test audit_duration_seconds is pre-registered in global metrics."""
        metrics.observe_histogram("audit_duration_seconds", 10.0, labels={"tier": "test"})
        stats = metrics.get_histogram_stats("audit_duration_seconds", {"tier": "test"})
        assert stats["count"] >= 1
        metrics.reset()

    def test_active_audits_preregistered(self):
        """Test active_audits is pre-registered in global metrics."""
        initial = metrics.get_gauge("active_audits")
        metrics.inc_gauge("active_audits")
        after = metrics.get_gauge("active_audits")
        assert after == initial + 1
        metrics.reset()


class TestAuditMetricsLifecycle:
    """Tests simulating audit lifecycle with metrics."""

    @pytest.fixture
    def fresh_metrics(self):
        """Create a fresh registry for testing."""
        registry = MetricsRegistry()
        registry.register_counter("audit_total", "Total number of audits by tier and status")
        registry.register_histogram(
            "audit_duration_seconds",
            "Audit completion time in seconds",
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0),
        )
        registry.register_gauge("active_audits", "Number of currently running audits")
        return registry

    def test_successful_audit_lifecycle(self, fresh_metrics):
        """Test metrics are correct after successful audit."""
        tier = "basic"
        start_time = time.perf_counter()

        fresh_metrics.inc_gauge("active_audits")
        assert fresh_metrics.get_gauge("active_audits") == 1.0

        time.sleep(0.01)

        fresh_metrics.dec_gauge("active_audits")
        duration = time.perf_counter() - start_time
        fresh_metrics.inc_counter("audit_total", labels={"tier": tier, "status": "completed"})
        fresh_metrics.observe_histogram("audit_duration_seconds", duration, labels={"tier": tier})

        assert fresh_metrics.get_gauge("active_audits") == 0.0
        assert fresh_metrics.get_counter("audit_total", {"tier": tier, "status": "completed"}) == 1.0

        stats = fresh_metrics.get_histogram_stats("audit_duration_seconds", {"tier": tier})
        assert stats["count"] == 1
        assert stats["sum"] >= 0.01

    def test_failed_audit_lifecycle(self, fresh_metrics):
        """Test metrics are correct after failed audit."""
        tier = "pro"
        start_time = time.perf_counter()

        fresh_metrics.inc_gauge("active_audits")

        time.sleep(0.005)

        fresh_metrics.dec_gauge("active_audits")
        duration = time.perf_counter() - start_time
        fresh_metrics.inc_counter("audit_total", labels={"tier": tier, "status": "failed"})
        fresh_metrics.observe_histogram("audit_duration_seconds", duration, labels={"tier": tier})

        assert fresh_metrics.get_gauge("active_audits") == 0.0
        assert fresh_metrics.get_counter("audit_total", {"tier": tier, "status": "failed"}) == 1.0

    def test_concurrent_audits(self, fresh_metrics):
        """Test metrics with concurrent audits."""
        fresh_metrics.inc_gauge("active_audits")
        assert fresh_metrics.get_gauge("active_audits") == 1.0

        fresh_metrics.inc_gauge("active_audits")
        assert fresh_metrics.get_gauge("active_audits") == 2.0

        fresh_metrics.inc_gauge("active_audits")
        assert fresh_metrics.get_gauge("active_audits") == 3.0

        fresh_metrics.dec_gauge("active_audits")
        fresh_metrics.inc_counter("audit_total", labels={"tier": "basic", "status": "completed"})
        assert fresh_metrics.get_gauge("active_audits") == 2.0

        fresh_metrics.dec_gauge("active_audits")
        fresh_metrics.inc_counter("audit_total", labels={"tier": "pro", "status": "failed"})
        assert fresh_metrics.get_gauge("active_audits") == 1.0

        fresh_metrics.dec_gauge("active_audits")
        fresh_metrics.inc_counter("audit_total", labels={"tier": "enterprise", "status": "completed"})
        assert fresh_metrics.get_gauge("active_audits") == 0.0

        assert fresh_metrics.get_counter("audit_total", {"tier": "basic", "status": "completed"}) == 1.0
        assert fresh_metrics.get_counter("audit_total", {"tier": "pro", "status": "failed"}) == 1.0
        assert fresh_metrics.get_counter("audit_total", {"tier": "enterprise", "status": "completed"}) == 1.0

    def test_audit_metrics_with_all_tiers(self, fresh_metrics):
        """Test metrics work with all tier values."""
        for tier in ["basic", "pro", "enterprise"]:
            fresh_metrics.inc_gauge("active_audits")
            fresh_metrics.dec_gauge("active_audits")
            fresh_metrics.inc_counter("audit_total", labels={"tier": tier, "status": "completed"})
            fresh_metrics.observe_histogram("audit_duration_seconds", 10.0, labels={"tier": tier})

        for tier in ["basic", "pro", "enterprise"]:
            assert fresh_metrics.get_counter("audit_total", {"tier": tier, "status": "completed"}) == 1.0
            stats = fresh_metrics.get_histogram_stats("audit_duration_seconds", {"tier": tier})
            assert stats["count"] == 1
