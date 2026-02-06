"""
Tests for metrics middleware.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.seo_health_report.metrics.collector import MetricsRegistry
from packages.seo_health_report.metrics.middleware import (
    MetricsMiddleware,
    create_metrics_endpoint,
    get_metrics,
)


class MockRequest:
    """Mock Starlette Request for testing."""

    def __init__(
        self,
        method: str = "GET",
        path: str = "/test",
    ):
        self.method = method
        self.url = MagicMock()
        self.url.path = path


class MockResponse:
    """Mock Starlette Response for testing."""

    def __init__(self, status_code: int = 200):
        self.status_code = status_code


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware."""

    @pytest.fixture
    def fresh_registry(self):
        """Create a fresh registry for each test."""
        registry = MetricsRegistry()
        with patch("packages.seo_health_report.metrics.middleware.metrics", registry):
            yield registry

    @pytest.mark.asyncio
    async def test_increments_request_counter(self, fresh_registry):
        """Test that middleware increments request counter."""
        app = MagicMock()
        middleware = MetricsMiddleware(app)

        request = MockRequest(method="GET", path="/api/test")
        response = MockResponse(status_code=200)

        async def call_next(req):
            return response

        await middleware.dispatch(request, call_next)

        count = fresh_registry.get_counter(
            "http_requests_total",
            {"method": "GET", "path": "/api/test", "status": "200"}
        )
        assert count == 1.0

    @pytest.mark.asyncio
    async def test_records_request_duration(self, fresh_registry):
        """Test that middleware records request duration."""
        app = MagicMock()
        middleware = MetricsMiddleware(app)

        request = MockRequest(method="POST", path="/api/audit")
        response = MockResponse(status_code=201)

        async def call_next(req):
            return response

        await middleware.dispatch(request, call_next)

        stats = fresh_registry.get_histogram_stats(
            "http_request_duration_seconds",
            {"method": "POST", "path": "/api/audit"}
        )
        assert stats["count"] == 1
        assert stats["sum"] > 0

    @pytest.mark.asyncio
    async def test_skips_metrics_endpoint(self, fresh_registry):
        """Test that /metrics endpoint is not counted."""
        app = MagicMock()
        middleware = MetricsMiddleware(app)

        request = MockRequest(method="GET", path="/metrics")
        response = MockResponse()

        async def call_next(req):
            return response

        await middleware.dispatch(request, call_next)

        # Check no metrics were recorded for /metrics path
        output = fresh_registry.prometheus_format()
        assert "/metrics" not in output or 'path="/metrics"' not in output

    @pytest.mark.asyncio
    async def test_skips_health_endpoint(self, fresh_registry):
        """Test that /health endpoint is not counted."""
        app = MagicMock()
        middleware = MetricsMiddleware(app)

        request = MockRequest(method="GET", path="/health")
        response = MockResponse()

        async def call_next(req):
            return response

        await middleware.dispatch(request, call_next)

        count = fresh_registry.get_counter(
            "http_requests_total",
            {"method": "GET", "path": "/health", "status": "200"}
        )
        assert count == 0

    @pytest.mark.asyncio
    async def test_custom_skip_paths(self, fresh_registry):
        """Test custom skip paths."""
        app = MagicMock()
        middleware = MetricsMiddleware(app, skip_paths={"/internal", "/private"})

        request = MockRequest(path="/internal")
        response = MockResponse()

        async def call_next(req):
            return response

        await middleware.dispatch(request, call_next)

        count = fresh_registry.get_counter(
            "http_requests_total",
            {"method": "GET", "path": "/internal", "status": "200"}
        )
        assert count == 0

    @pytest.mark.asyncio
    async def test_handles_exception(self, fresh_registry):
        """Test that middleware handles exceptions and still records metrics."""
        app = MagicMock()
        middleware = MetricsMiddleware(app)

        request = MockRequest(method="GET", path="/api/error")

        async def call_next(req):
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await middleware.dispatch(request, call_next)

        # Should still record the request with 500 status
        count = fresh_registry.get_counter(
            "http_requests_total",
            {"method": "GET", "path": "/api/error", "status": "500"}
        )
        assert count == 1.0

    @pytest.mark.asyncio
    async def test_records_different_status_codes(self, fresh_registry):
        """Test that different status codes are tracked separately."""
        app = MagicMock()
        middleware = MetricsMiddleware(app)

        async def make_request(status):
            request = MockRequest(path="/api/test")
            response = MockResponse(status_code=status)

            async def call_next(req):
                return response

            await middleware.dispatch(request, call_next)

        await make_request(200)
        await make_request(201)
        await make_request(400)
        await make_request(500)

        assert fresh_registry.get_counter("http_requests_total", {"method": "GET", "path": "/api/test", "status": "200"}) == 1
        assert fresh_registry.get_counter("http_requests_total", {"method": "GET", "path": "/api/test", "status": "201"}) == 1
        assert fresh_registry.get_counter("http_requests_total", {"method": "GET", "path": "/api/test", "status": "400"}) == 1
        assert fresh_registry.get_counter("http_requests_total", {"method": "GET", "path": "/api/test", "status": "500"}) == 1


class TestPathNormalization:
    """Tests for path normalization."""

    def test_normalize_uuid(self):
        """Test UUID normalization."""
        middleware = MetricsMiddleware(MagicMock())

        path = "/users/550e8400-e29b-41d4-a716-446655440000/profile"
        normalized = middleware._normalize_path(path)

        assert normalized == "/users/{id}/profile"

    def test_normalize_hex_id(self):
        """Test hex ID normalization."""
        middleware = MetricsMiddleware(MagicMock())

        path = "/audit/abc123def456/result"
        normalized = middleware._normalize_path(path)

        assert normalized == "/audit/{id}/result"

    def test_normalize_numeric_id(self):
        """Test numeric ID normalization."""
        middleware = MetricsMiddleware(MagicMock())

        path = "/posts/12345/comments"
        normalized = middleware._normalize_path(path)

        assert normalized == "/posts/{id}/comments"

    def test_normalize_prefixed_id(self):
        """Test prefixed ID normalization."""
        middleware = MetricsMiddleware(MagicMock())

        path = "/audit/audit_abc123/status"
        normalized = middleware._normalize_path(path)

        assert normalized == "/audit/{id}/status"

    def test_normalize_date(self):
        """Test date normalization."""
        middleware = MetricsMiddleware(MagicMock())

        path = "/reports/2024-01-15/summary"
        normalized = middleware._normalize_path(path)

        assert normalized == "/reports/{date}/summary"

    def test_no_normalization_for_static_path(self):
        """Test that static paths are not modified."""
        middleware = MetricsMiddleware(MagicMock())

        path = "/api/v1/users"
        normalized = middleware._normalize_path(path)

        assert normalized == "/api/v1/users"

    def test_empty_path(self):
        """Test empty path handling."""
        middleware = MetricsMiddleware(MagicMock())

        normalized = middleware._normalize_path("/")
        assert normalized == "/"

    @pytest.mark.asyncio
    async def test_normalization_disabled(self):
        """Test that normalization can be disabled."""
        app = MagicMock()
        registry = MetricsRegistry()

        middleware = MetricsMiddleware(app, normalize_paths=False)

        with patch("packages.seo_health_report.metrics.middleware.metrics", registry):
            request = MockRequest(path="/users/12345")
            response = MockResponse()

            async def call_next(req):
                return response

            await middleware.dispatch(request, call_next)

            # Path should NOT be normalized
            count = registry.get_counter(
                "http_requests_total",
                {"method": "GET", "path": "/users/12345", "status": "200"}
            )
            assert count == 1.0


class TestMetricsEndpoint:
    """Tests for metrics endpoint handlers."""

    @pytest.mark.asyncio
    async def test_get_metrics_returns_prometheus_format(self):
        """Test that get_metrics returns Prometheus format."""
        from packages.seo_health_report.metrics.collector import metrics

        # Add some test metrics
        metrics.inc_counter("test_endpoint_counter")

        response = await get_metrics()

        assert response.status_code == 200
        assert "text/plain" in response.media_type
        assert "test_endpoint_counter" in response.body.decode()

        # Cleanup
        metrics.reset()

    @pytest.mark.asyncio
    async def test_create_metrics_endpoint(self):
        """Test create_metrics_endpoint factory."""
        from packages.seo_health_report.metrics.collector import metrics

        endpoint = create_metrics_endpoint()

        metrics.set_gauge("test_gauge", 42)

        response = await endpoint()

        assert response.status_code == 200
        assert "test_gauge 42" in response.body.decode()

        # Cleanup
        metrics.reset()

    @pytest.mark.asyncio
    async def test_metrics_content_type(self):
        """Test that metrics endpoint has correct content type."""
        response = await get_metrics()

        assert "text/plain" in response.media_type
        assert "version=0.0.4" in response.media_type


class TestIntegration:
    """Integration tests for metrics system."""

    @pytest.mark.asyncio
    async def test_full_request_cycle(self):
        """Test complete request cycle with metrics."""
        registry = MetricsRegistry()
        app = MagicMock()
        middleware = MetricsMiddleware(app)

        with patch("packages.seo_health_report.metrics.middleware.metrics", registry):
            # Simulate multiple requests
            paths = ["/api/users", "/api/posts", "/api/users"]
            statuses = [200, 201, 404]

            for path, status in zip(paths, statuses):
                request = MockRequest(path=path)
                response = MockResponse(status_code=status)

                async def make_call_next(resp):
                    async def call_next(req):
                        return resp
                    return call_next

                await middleware.dispatch(request, await make_call_next(response))

            # Verify metrics
            output = registry.prometheus_format()

            assert "http_requests_total" in output
            assert "http_request_duration_seconds" in output
            assert 'path="/api/users"' in output
            assert 'path="/api/posts"' in output
