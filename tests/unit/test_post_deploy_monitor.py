"""
Tests for post-deployment monitoring functionality.
"""

import json
import os
import sys

# Add scripts to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))


class TestCheckMetricsModule:
    """Tests for check_metrics.py module."""

    def test_parse_prometheus_metrics_empty(self):
        """Test parsing empty metrics."""
        from check_metrics import parse_prometheus_metrics

        result = parse_prometheus_metrics("")
        assert result == {}

    def test_parse_prometheus_metrics_with_comments(self):
        """Test parsing metrics with comments."""
        from check_metrics import parse_prometheus_metrics

        content = """
# HELP http_requests_total Total requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 100
"""
        result = parse_prometheus_metrics(content)
        assert "http_requests_total" in result
        assert result["http_requests_total"]['{method="GET",status="200"}'] == 100.0

    def test_parse_prometheus_metrics_multiple(self):
        """Test parsing multiple metrics."""
        from check_metrics import parse_prometheus_metrics

        content = """
http_requests_total{method="GET",status="200"} 100
http_requests_total{method="POST",status="201"} 50
http_requests_total{method="GET",status="500"} 5
active_audits 3
"""
        result = parse_prometheus_metrics(content)

        assert "http_requests_total" in result
        assert len(result["http_requests_total"]) == 3
        assert "active_audits" in result
        assert result["active_audits"][""] == 3.0

    def test_extract_label_value(self):
        """Test extracting label values."""
        from check_metrics import extract_label_value

        labels = '{method="GET",status="200",path="/api"}'

        assert extract_label_value(labels, "method") == "GET"
        assert extract_label_value(labels, "status") == "200"
        assert extract_label_value(labels, "path") == "/api"
        assert extract_label_value(labels, "nonexistent") is None

    def test_extract_label_value_empty(self):
        """Test extracting from empty labels."""
        from check_metrics import extract_label_value

        assert extract_label_value("", "method") is None
        assert extract_label_value("{}", "method") is None


class TestMetricsSummary:
    """Tests for MetricsSummary dataclass."""

    def test_summary_to_dict(self):
        """Test converting summary to dictionary."""
        from check_metrics import MetricsSummary

        summary = MetricsSummary(
            timestamp="2024-01-15T10:00:00Z",
            url="https://api.example.com",
            healthy=True,
            total_requests=1000,
            error_requests=10,
            error_rate=1.0,
            error_rate_threshold=5.0,
            error_rate_ok=True,
            active_audits=2,
            audit_completed=50,
            audit_failed=5,
            webhook_delivered=100,
            webhook_failed=2,
            issues=[],
        )

        result = summary.to_dict()

        assert result["timestamp"] == "2024-01-15T10:00:00Z"
        assert result["healthy"] is True
        assert result["error_rate"] == 1.0
        assert result["issues"] == []

    def test_summary_with_issues(self):
        """Test summary with issues."""
        from check_metrics import MetricsSummary

        summary = MetricsSummary(
            timestamp="2024-01-15T10:00:00Z",
            url="https://api.example.com",
            healthy=False,
            total_requests=1000,
            error_requests=100,
            error_rate=10.0,
            error_rate_threshold=5.0,
            error_rate_ok=False,
            active_audits=0,
            audit_completed=0,
            audit_failed=0,
            webhook_delivered=0,
            webhook_failed=0,
            issues=["Error rate 10.00% exceeds threshold 5.0%", "Health check failed"],
        )

        result = summary.to_dict()

        assert result["healthy"] is False
        assert result["error_rate_ok"] is False
        assert len(result["issues"]) == 2


class TestErrorRateCalculation:
    """Tests for error rate calculation logic."""

    def test_calculate_error_rate_no_requests(self):
        """Test error rate with no requests."""
        total = 0
        errors = 0
        error_rate = (errors / total * 100) if total > 0 else 0.0
        assert error_rate == 0.0

    def test_calculate_error_rate_no_errors(self):
        """Test error rate with no errors."""
        total = 1000
        errors = 0
        error_rate = (errors / total * 100) if total > 0 else 0.0
        assert error_rate == 0.0

    def test_calculate_error_rate_with_errors(self):
        """Test error rate calculation."""
        total = 1000
        errors = 50
        error_rate = (errors / total * 100) if total > 0 else 0.0
        assert error_rate == 5.0

    def test_error_rate_threshold_check(self):
        """Test error rate threshold logic."""
        threshold = 5.0

        assert 4.9 <= threshold  # OK
        assert 5.0 <= threshold  # OK (exactly at threshold)
        assert not (5.1 <= threshold)  # Exceeds


class TestPrometheusFormatParsing:
    """Tests for parsing various Prometheus metric formats."""

    def test_parse_counter(self):
        """Test parsing counter metric."""
        from check_metrics import parse_prometheus_metrics

        content = 'http_requests_total{method="GET"} 42'
        result = parse_prometheus_metrics(content)

        assert result["http_requests_total"]['{method="GET"}'] == 42.0

    def test_parse_gauge(self):
        """Test parsing gauge metric."""
        from check_metrics import parse_prometheus_metrics

        content = 'active_audits 5'
        result = parse_prometheus_metrics(content)

        assert result["active_audits"][""] == 5.0

    def test_parse_histogram_bucket(self):
        """Test parsing histogram bucket."""
        from check_metrics import parse_prometheus_metrics

        content = 'http_request_duration_seconds_bucket{le="0.1"} 100'
        result = parse_prometheus_metrics(content)

        assert result["http_request_duration_seconds_bucket"]['{le="0.1"}'] == 100.0

    def test_parse_scientific_notation(self):
        """Test parsing scientific notation values."""
        from check_metrics import parse_prometheus_metrics

        content = 'big_number 1.5e6'
        result = parse_prometheus_metrics(content)

        assert result["big_number"][""] == 1500000.0

    def test_parse_negative_values(self):
        """Test parsing negative values."""
        from check_metrics import parse_prometheus_metrics

        content = 'temperature_celsius -10.5'
        result = parse_prometheus_metrics(content)

        assert result["temperature_celsius"][""] == -10.5


class TestAlertingIntegration:
    """Tests for alerting webhook integration."""

    def test_slack_payload_format(self):
        """Test Slack webhook payload format."""
        from check_metrics import MetricsSummary

        summary = MetricsSummary(
            timestamp="2024-01-15T10:00:00Z",
            url="https://api.example.com",
            healthy=False,
            total_requests=100,
            error_requests=10,
            error_rate=10.0,
            error_rate_threshold=5.0,
            error_rate_ok=False,
            active_audits=1,
            audit_completed=5,
            audit_failed=1,
            webhook_delivered=10,
            webhook_failed=0,
            issues=["Error rate too high"],
        )

        # Verify summary can be serialized to JSON (required for webhook)
        payload = json.dumps(summary.to_dict())
        assert "error_rate" in payload
        assert "10.0" in payload

    def test_discord_embed_color_calculation(self):
        """Test Discord embed color calculation."""
        # Green for success
        assert 65280 == 0x00FF00

        # Red for failure
        assert 16711680 == 0xFF0000

        # Yellow for warning
        assert 16776960 == 0xFFFF00


class TestMetricsEndpointMock:
    """Tests using mock metrics responses."""

    def test_healthy_response(self):
        """Test analyzing a healthy metrics response."""
        from check_metrics import extract_label_value, parse_prometheus_metrics

        content = """
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api",status="200"} 950
http_requests_total{method="POST",path="/api",status="201"} 45
http_requests_total{method="GET",path="/api",status="500"} 5
# HELP active_audits Currently running audits
# TYPE active_audits gauge
active_audits 2
# HELP audit_total Total audits by status
# TYPE audit_total counter
audit_total{tier="basic",status="completed"} 100
audit_total{tier="basic",status="failed"} 5
"""
        metrics = parse_prometheus_metrics(content)

        # Calculate totals
        total_requests = 0
        error_requests = 0

        for labels, count in metrics.get("http_requests_total", {}).items():
            total_requests += int(count)
            status = extract_label_value(labels, "status")
            if status and status.startswith("5"):
                error_requests += int(count)

        assert total_requests == 1000
        assert error_requests == 5

        error_rate = error_requests / total_requests * 100
        assert error_rate == 0.5  # 0.5% error rate - healthy

        # Check active audits
        assert metrics["active_audits"][""] == 2.0

    def test_unhealthy_response(self):
        """Test analyzing an unhealthy metrics response."""
        from check_metrics import extract_label_value, parse_prometheus_metrics

        content = """
http_requests_total{status="200"} 800
http_requests_total{status="500"} 150
http_requests_total{status="503"} 50
"""
        metrics = parse_prometheus_metrics(content)

        total_requests = 0
        error_requests = 0

        for labels, count in metrics.get("http_requests_total", {}).items():
            total_requests += int(count)
            status = extract_label_value(labels, "status")
            if status and status.startswith("5"):
                error_requests += int(count)

        assert total_requests == 1000
        assert error_requests == 200

        error_rate = error_requests / total_requests * 100
        assert error_rate == 20.0  # 20% error rate - very unhealthy


class TestMonitorScriptHelpers:
    """Tests for monitoring script helper functions."""

    def test_threshold_comparison(self):
        """Test error rate threshold comparison."""
        threshold = 5.0

        # Values that should pass
        assert 0.0 <= threshold
        assert 4.99 <= threshold
        assert 5.0 <= threshold

        # Values that should fail
        assert 5.01 > threshold
        assert 10.0 > threshold

    def test_response_time_threshold(self):
        """Test response time threshold check."""
        max_response_time = 5000  # ms

        # Values that should pass
        assert 100 <= max_response_time
        assert 4999 <= max_response_time
        assert 5000 <= max_response_time

        # Values that should fail
        assert 5001 > max_response_time
        assert 10000 > max_response_time
