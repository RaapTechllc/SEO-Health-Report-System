"""Tests for the Admin Health Dashboard."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = MagicMock()
    user.id = "user-123"
    user.email = "user@example.com"
    user.role = "user"
    return user


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user object."""
    user = MagicMock()
    user.id = "admin-123"
    user.email = "admin@example.com"
    user.role = "admin"
    return user


class TestAdminHealthMetricsAggregation:
    """Test metrics aggregation logic."""

    def test_get_metrics_data_aggregation(self):
        """Test that metrics are correctly aggregated."""
        from packages.seo_health_report.metrics import metrics

        metrics.reset()

        metrics.set_gauge("active_audits", 3)
        metrics.inc_counter("audit_total", {"tier": "basic", "status": "completed"}, 10)
        metrics.inc_counter("audit_total", {"tier": "pro", "status": "completed"}, 5)
        metrics.inc_counter("audit_total", {"tier": "enterprise", "status": "completed"}, 2)
        metrics.inc_counter("audit_total", {"tier": "basic", "status": "failed"}, 1)
        metrics.inc_counter("audit_total", {"tier": "pro", "status": "failed"}, 1)

        for _ in range(17):
            metrics.observe_histogram("audit_duration_seconds", 50.0)

        from apps.admin.routes import _get_metrics_data

        data = _get_metrics_data()

        assert data["active_audits"] == 3
        assert data["total_audits"] == 19
        assert data["completed_audits"] == 17
        assert data["failed_audits"] == 2
        assert data["error_rate"] == pytest.approx(10.53, rel=0.01)
        assert data["avg_duration_seconds"] == 50.0

        metrics.reset()

    def test_get_metrics_data_zero_total(self):
        """Test error rate calculation with zero total audits."""
        from packages.seo_health_report.metrics import metrics

        metrics.reset()

        from apps.admin.routes import _get_metrics_data

        data = _get_metrics_data()

        assert data["error_rate"] == 0.0
        assert data["avg_duration_seconds"] == 0.0
        assert data["total_audits"] == 0

        metrics.reset()


class TestAdminHealthEndpoints:
    """Test admin health endpoints with auth."""

    def test_health_endpoint_requires_admin(self, mock_user):
        """Test that /admin/health returns 403 for non-admin users."""
        from auth import require_admin

        with pytest.raises(HTTPException) as exc_info:
            import asyncio

            async def check_admin():
                return await require_admin(mock_user)

            asyncio.get_event_loop().run_until_complete(check_admin())

        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)

    def test_health_endpoint_allows_admin(self, mock_admin_user):
        """Test that /admin/health allows admin users."""
        import asyncio

        from auth import require_admin

        async def check_admin():
            return await require_admin(mock_admin_user)

        result = asyncio.get_event_loop().run_until_complete(check_admin())
        assert result == mock_admin_user

    def test_metrics_json_endpoint_returns_valid_data(self):
        """Test that _get_metrics_data returns valid JSON-serializable data."""
        from packages.seo_health_report.metrics import metrics

        metrics.reset()
        metrics.set_gauge("active_audits", 5)
        metrics.inc_counter("audit_total", {"tier": "basic", "status": "completed"}, 10)

        from apps.admin.routes import _get_metrics_data

        data = _get_metrics_data()

        required_keys = [
            "active_audits",
            "total_audits",
            "completed_audits",
            "failed_audits",
            "error_rate",
            "avg_duration_seconds",
        ]

        for key in required_keys:
            assert key in data
            assert isinstance(data[key], (int, float))

        metrics.reset()


class TestAdminHealthIntegration:
    """Integration tests for admin health with FastAPI app."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        from fastapi import FastAPI

        from apps.admin.routes import router
        from auth import require_admin

        app = FastAPI()

        async def mock_require_admin():
            user = MagicMock()
            user.role = "admin"
            return user

        app.include_router(router, prefix="/admin")
        app.dependency_overrides[require_admin] = mock_require_admin

        return TestClient(app)

    def test_health_page_returns_html(self, client):
        """Test that /admin/health returns HTML content."""
        response = client.get("/admin/health")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "System Health Dashboard" in response.text

    def test_metrics_endpoint_returns_json(self, client):
        """Test that /admin/health/metrics returns JSON."""
        response = client.get("/admin/health/metrics")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert "active_audits" in data
        assert "error_rate" in data

    def test_health_page_contains_refresh_script(self, client):
        """Test that health page contains auto-refresh JavaScript."""
        response = client.get("/admin/health")

        assert response.status_code == 200
        assert "setInterval" in response.text
        assert "30000" in response.text
        assert "refreshMetrics" in response.text
