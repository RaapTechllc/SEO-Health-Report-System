"""Integration tests for quota enforcement."""

import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

sys.modules.setdefault("stripe", MagicMock())

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_dashboard_user():
    """Create a mock authenticated dashboard user with tenant."""
    return {
        "id": "user_123",
        "email": "test@example.com",
        "role": "user",
        "tenant_id": "tenant_123",
    }


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    from apps.api.main import app
    return TestClient(app)


@pytest.fixture
def auth_client(mock_dashboard_user):
    """Create test client with mocked dashboard authentication."""
    from apps.api.main import app
    from apps.dashboard.auth import require_dashboard_auth

    app.dependency_overrides[require_dashboard_auth] = lambda: mock_dashboard_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestQuotaExceededReturns429:
    """Tests that quota exceeded returns HTTP 429."""

    def test_monthly_quota_exceeded_returns_429(self, auth_client):
        """When monthly audit limit is reached, return 429."""
        import apps.dashboard.routes as routes_module
        from packages.seo_health_report.quotas.service import QuotaExceededError

        original_quota_service = routes_module.QuotaService

        mock_service = MagicMock()
        mock_service.enforce_quota.side_effect = QuotaExceededError(
            "Monthly audit limit reached (10)",
            "monthly_audits",
            10,
            10
        )

        routes_module.QuotaService = lambda db: mock_service
        try:
            response = auth_client.post(
                "/dashboard/audits/new",
                data={
                    "url": "example.com",
                    "company_name": "Test Company",
                    "trade_type": "Plumber",
                    "tier": "basic",
                },
            )

            assert response.status_code == 429
            assert b"limit" in response.content.lower() or b"quota" in response.content.lower()
        finally:
            routes_module.QuotaService = original_quota_service

    def test_quota_exceeded_error_contains_details(self):
        """QuotaExceededError contains quota type and limits."""
        from packages.seo_health_report.quotas.service import QuotaExceededError

        error = QuotaExceededError(
            "Monthly audit limit reached (10)",
            "monthly_audits",
            10,
            10
        )

        assert error.quota_type == "monthly_audits"
        assert error.limit == 10
        assert error.used == 10
        assert str(error) == "Monthly audit limit reached (10)"


class TestConcurrentLimitBlocksNewAudits:
    """Tests that concurrent limit blocks new audits."""

    def test_concurrent_quota_exceeded_returns_429(self, auth_client):
        """When concurrent audit limit is reached, return 429."""
        import apps.dashboard.routes as routes_module
        from packages.seo_health_report.quotas.service import QuotaExceededError

        original_quota_service = routes_module.QuotaService

        mock_service = MagicMock()
        mock_service.enforce_quota.side_effect = QuotaExceededError(
            "Concurrent audit limit reached (2)",
            "concurrent_audits",
            2,
            2
        )

        routes_module.QuotaService = lambda db: mock_service
        try:
            response = auth_client.post(
                "/dashboard/audits/new",
                data={
                    "url": "example.com",
                    "company_name": "Test Company",
                    "trade_type": "Plumber",
                    "tier": "basic",
                },
            )

            assert response.status_code == 429
            assert b"concurrent" in response.content.lower() or b"limit" in response.content.lower()
        finally:
            routes_module.QuotaService = original_quota_service

    def test_concurrent_limit_calculated_from_running_audits(self):
        """Concurrent count should be based on pending/running audits."""
        from unittest.mock import MagicMock

        from packages.seo_health_report.quotas.service import QuotaService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
            tenant_id="tenant_123",
            monthly_audits_limit=10,
            monthly_audits_used=5,
            billing_cycle_start=datetime.now(timezone.utc),
            max_concurrent_audits=2,
            max_pages_per_audit=50,
            max_ai_prompts_per_audit=10,
        )
        mock_db.query.return_value.filter.return_value.scalar.return_value = 2

        service = QuotaService(mock_db)

        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
            monthly_audits_limit=10,
            monthly_audits_used=5,
            billing_cycle_start=datetime.now(timezone.utc),
            max_concurrent_audits=2,
        )

        with patch.object(service, '_get_concurrent_audit_count', return_value=2):
            status = service.check_quota("tenant_123")
            assert status.concurrent_audits == 2
            assert not status.can_start_audit
            assert "concurrent" in status.quota_exceeded_reason.lower()


class TestMonthlyResetWorks:
    """Tests for monthly quota reset functionality."""

    def test_reset_monthly_usage_clears_count(self):
        """reset_monthly_usage should set monthly_audits_used to 0."""
        from unittest.mock import MagicMock

        from packages.seo_health_report.quotas.service import QuotaService

        mock_quota = MagicMock()
        mock_quota.monthly_audits_used = 10
        mock_quota.billing_cycle_start = datetime.now(timezone.utc) - timedelta(days=35)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quota

        service = QuotaService(mock_db)
        service.reset_monthly_usage("tenant_123")

        assert mock_quota.monthly_audits_used == 0
        assert mock_quota.billing_cycle_start is not None
        mock_db.commit.assert_called()

    def test_reset_date_calculation(self):
        """Reset date should be the next month from billing cycle start."""
        from packages.seo_health_report.quotas.service import QuotaService

        mock_db = MagicMock()
        service = QuotaService(mock_db)

        billing_start = datetime(2025, 1, 15, tzinfo=timezone.utc)
        with patch('packages.seo_health_report.quotas.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 20, tzinfo=timezone.utc)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            reset_date = service._calculate_reset_date(billing_start)

            assert reset_date.month == 2
            assert reset_date.year == 2025

    def test_reset_date_handles_year_boundary(self):
        """Reset date should handle December to January transition."""
        from packages.seo_health_report.quotas.service import QuotaService

        mock_db = MagicMock()
        service = QuotaService(mock_db)

        billing_start = datetime(2024, 12, 15, tzinfo=timezone.utc)

        with patch('packages.seo_health_report.quotas.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 12, 20, tzinfo=timezone.utc)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            reset_date = service._calculate_reset_date(billing_start)

            assert reset_date.month == 1
            assert reset_date.year == 2025


class TestQuotaAPIEndpoint:
    """Tests for the GET /dashboard/quota endpoint."""

    def test_quota_endpoint_requires_auth(self, client):
        """Quota endpoint should require authentication."""
        response = client.get("/dashboard/quota", follow_redirects=False)
        assert response.status_code in [302, 401, 403]

    def test_quota_endpoint_returns_json(self, auth_client):
        """Quota endpoint should return JSON with quota details."""
        import apps.dashboard.routes as routes_module
        from packages.seo_health_report.quotas.service import QuotaStatus

        original_quota_service = routes_module.QuotaService

        mock_service = MagicMock()
        mock_service.check_quota.return_value = QuotaStatus(
            monthly_audits_used=5,
            monthly_audits_limit=10,
            monthly_audits_remaining=5,
            concurrent_audits=1,
            max_concurrent=2,
            can_start_audit=True,
            quota_exceeded_reason=None,
            reset_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
        )

        routes_module.QuotaService = lambda db: mock_service
        try:
            response = auth_client.get("/dashboard/quota")

            assert response.status_code == 200
            data = response.json()

            assert data["monthly_audits_used"] == 5
            assert data["monthly_audits_limit"] == 10
            assert data["monthly_audits_remaining"] == 5
            assert data["concurrent_audits"] == 1
            assert data["max_concurrent"] == 2
            assert data["can_start_audit"] is True
            assert data["reset_date"] is not None
        finally:
            routes_module.QuotaService = original_quota_service

    def test_quota_endpoint_handles_no_tenant(self):
        """Quota endpoint should handle users without tenant."""
        from apps.api.main import app
        from apps.dashboard.auth import require_dashboard_auth

        user_no_tenant = {
            "id": "user_456",
            "email": "notenant@example.com",
            "role": "user",
            "tenant_id": None,
        }

        app.dependency_overrides[require_dashboard_auth] = lambda: user_no_tenant
        client = TestClient(app)

        try:
            response = client.get("/dashboard/quota")
            assert response.status_code == 200
            data = response.json()

            assert data["monthly_audits_limit"] == -1
            assert data["can_start_audit"] is True
        finally:
            app.dependency_overrides.clear()


class TestUnlimitedQuota:
    """Tests for enterprise/unlimited quota tier."""

    def test_unlimited_monthly_quota(self):
        """Enterprise tier (-1 limit) should allow unlimited audits."""
        from unittest.mock import MagicMock

        from packages.seo_health_report.quotas.service import QuotaService

        mock_quota = MagicMock()
        mock_quota.monthly_audits_limit = -1
        mock_quota.monthly_audits_used = 1000
        mock_quota.billing_cycle_start = datetime.now(timezone.utc)
        mock_quota.max_concurrent_audits = 20

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quota

        service = QuotaService(mock_db)

        with patch.object(service, '_get_concurrent_audit_count', return_value=0):
            status = service.check_quota("tenant_123")

            assert status.monthly_audits_remaining == -1
            assert status.can_start_audit is True


class TestQuotaServiceEnforcement:
    """Tests for QuotaService.enforce_quota() method."""

    def test_enforce_quota_raises_on_monthly_exceeded(self):
        """enforce_quota should raise QuotaExceededError when monthly limit reached."""
        from unittest.mock import MagicMock

        from packages.seo_health_report.quotas.service import QuotaExceededError, QuotaService

        mock_quota = MagicMock()
        mock_quota.monthly_audits_limit = 10
        mock_quota.monthly_audits_used = 10
        mock_quota.billing_cycle_start = datetime.now(timezone.utc)
        mock_quota.max_concurrent_audits = 2

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quota

        service = QuotaService(mock_db)

        with patch.object(service, '_get_concurrent_audit_count', return_value=0):
            with pytest.raises(QuotaExceededError) as exc_info:
                service.enforce_quota("tenant_123")

            assert exc_info.value.quota_type == "monthly_audits"
            assert exc_info.value.limit == 10

    def test_enforce_quota_raises_on_concurrent_exceeded(self):
        """enforce_quota should raise QuotaExceededError when concurrent limit reached."""
        from unittest.mock import MagicMock

        from packages.seo_health_report.quotas.service import QuotaExceededError, QuotaService

        mock_quota = MagicMock()
        mock_quota.monthly_audits_limit = 10
        mock_quota.monthly_audits_used = 5
        mock_quota.billing_cycle_start = datetime.now(timezone.utc)
        mock_quota.max_concurrent_audits = 2

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quota

        service = QuotaService(mock_db)

        with patch.object(service, '_get_concurrent_audit_count', return_value=2):
            with pytest.raises(QuotaExceededError) as exc_info:
                service.enforce_quota("tenant_123")

            assert exc_info.value.quota_type == "concurrent_audits"
            assert exc_info.value.limit == 2

    def test_enforce_quota_returns_status_when_ok(self):
        """enforce_quota should return QuotaStatus when quota is available."""
        from unittest.mock import MagicMock

        from packages.seo_health_report.quotas.service import QuotaService, QuotaStatus

        mock_quota = MagicMock()
        mock_quota.monthly_audits_limit = 10
        mock_quota.monthly_audits_used = 5
        mock_quota.billing_cycle_start = datetime.now(timezone.utc)
        mock_quota.max_concurrent_audits = 2

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quota

        service = QuotaService(mock_db)

        with patch.object(service, '_get_concurrent_audit_count', return_value=1):
            status = service.enforce_quota("tenant_123")

            assert isinstance(status, QuotaStatus)
            assert status.can_start_audit is True
            assert status.monthly_audits_remaining == 5
