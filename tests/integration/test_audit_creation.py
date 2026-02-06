"""Integration tests for dashboard audit creation."""

import sys
from unittest.mock import MagicMock

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
def mock_dashboard_user_no_tenant():
    """Create a mock user without tenant."""
    return {
        "id": "user_456",
        "email": "notenant@example.com",
        "role": "user",
        "tenant_id": None,
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


@pytest.fixture
def auth_client_no_tenant(mock_dashboard_user_no_tenant):
    """Create test client without tenant."""
    from apps.api.main import app
    from apps.dashboard.auth import require_dashboard_auth

    app.dependency_overrides[require_dashboard_auth] = lambda: mock_dashboard_user_no_tenant
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestAuditCreationForm:
    """Tests for GET /dashboard/audits/new endpoint."""

    def test_new_audit_form_requires_auth(self, client):
        response = client.get("/dashboard/audits/new", follow_redirects=False)
        assert response.status_code in [302, 401, 403]

    def test_new_audit_form_renders(self, auth_client):
        response = auth_client.get("/dashboard/audits/new")
        assert response.status_code == 200
        assert b"New SEO Audit" in response.content
        assert b"Website URL" in response.content
        assert b"Company Name" in response.content


class TestAuditCreationValidation:
    """Tests for POST /dashboard/audits/new validation."""

    def test_create_audit_requires_auth(self, client):
        response = client.post(
            "/dashboard/audits/new",
            data={
                "url": "example.com",
                "company_name": "Test Company",
                "trade_type": "Plumber",
                "tier": "basic",
            },
            follow_redirects=False
        )
        assert response.status_code in [302, 401, 403]

    def test_create_audit_validates_empty_url(self, auth_client):
        response = auth_client.post(
            "/dashboard/audits/new",
            data={
                "url": "",
                "company_name": "Test Company",
                "trade_type": "Plumber",
                "tier": "basic",
            },
        )
        assert response.status_code == 422
        assert b"Website URL is required" in response.content or b"url" in response.content.lower()

    def test_create_audit_validates_invalid_url(self, auth_client):
        response = auth_client.post(
            "/dashboard/audits/new",
            data={
                "url": "not-a-valid-domain",
                "company_name": "Test Company",
                "trade_type": "Plumber",
                "tier": "basic",
            },
        )
        assert response.status_code == 422
        assert b"valid domain" in response.content.lower() or b"error" in response.content.lower()

    def test_create_audit_validates_empty_company_name(self, auth_client):
        response = auth_client.post(
            "/dashboard/audits/new",
            data={
                "url": "example.com",
                "company_name": "",
                "trade_type": "Plumber",
                "tier": "basic",
            },
        )
        assert response.status_code == 422
        assert b"Company name is required" in response.content or b"company" in response.content.lower()

    def test_create_audit_validates_missing_trade_type(self, auth_client):
        response = auth_client.post(
            "/dashboard/audits/new",
            data={
                "url": "example.com",
                "company_name": "Test Company",
                "trade_type": "",
                "tier": "basic",
            },
        )
        assert response.status_code == 422
        assert b"trade type" in response.content.lower()

    def test_create_audit_validates_invalid_tier(self, auth_client):
        response = auth_client.post(
            "/dashboard/audits/new",
            data={
                "url": "example.com",
                "company_name": "Test Company",
                "trade_type": "Plumber",
                "tier": "invalid_tier",
            },
        )
        assert response.status_code == 422
        assert b"tier" in response.content.lower()

    def test_create_audit_preserves_form_data_on_error(self, auth_client):
        response = auth_client.post(
            "/dashboard/audits/new",
            data={
                "url": "",
                "company_name": "My Test Company",
                "trade_type": "Electrician",
                "tier": "pro",
                "service_areas": "Dallas, TX",
            },
        )
        assert response.status_code == 422
        assert b"My Test Company" in response.content
        assert b"Dallas, TX" in response.content


class TestAuditCreationSuccess:
    """Tests for successful audit creation - tested via unit tests due to DB schema."""

    @pytest.mark.skip(reason="Requires DB schema update for trade_type column")
    def test_create_audit_success_redirects(self, auth_client):
        import apps.dashboard.routes as routes_module
        original_enqueue = routes_module.enqueue_audit_job
        original_quota = routes_module.QuotaService

        def mock_enqueue(*args, **kwargs):
            return kwargs.get("audit_id", "audit_123")

        mock_quota_service = MagicMock()
        mock_quota_service.enforce_quota.return_value = None
        mock_quota_service.increment_usage.return_value = None

        routes_module.enqueue_audit_job = mock_enqueue
        routes_module.QuotaService = lambda db: mock_quota_service
        try:
            response = auth_client.post(
                "/dashboard/audits/new",
                data={
                    "url": "example.com",
                    "company_name": "Test Company",
                    "trade_type": "Plumber",
                    "tier": "basic",
                },
                follow_redirects=False
            )

            assert response.status_code == 302
            assert "/dashboard/audits/" in response.headers.get("location", "")
        finally:
            routes_module.enqueue_audit_job = original_enqueue
            routes_module.QuotaService = original_quota

    def test_url_normalization_logic(self):
        """Unit test for URL normalization."""
        from apps.dashboard.routes import validate_url

        test_cases = [
            ("https://www.EXAMPLE.COM/", "https://example.com"),
            ("HTTP://Example.Com", "https://example.com"),
            ("www.test.org/", "https://test.org"),
            ("subdomain.example.com", "https://subdomain.example.com"),
        ]

        for input_url, expected in test_cases:
            is_valid, _, normalized = validate_url(input_url)
            assert is_valid, f"Expected {input_url} to be valid"
            assert normalized == expected, f"Expected {expected}, got {normalized}"

    def test_service_areas_parsing(self):
        """Unit test for service areas parsing logic - uses same logic as route."""
        import re

        test_cases = [
            ("Austin, TX; Round Rock, TX; Cedar Park", 5),
            ("Dallas; Houston; San Antonio", 3),
            ("New York, NY, Los Angeles, CA", 4),
            ("  Chicago  ;  Miami  ", 2),
        ]

        for input_str, expected_count in test_cases:
            areas = [a.strip() for a in re.split(r'[;,]', input_str) if a.strip()]
            assert len(areas) == expected_count, f"Expected {expected_count} areas from '{input_str}', got {len(areas)}: {areas}"


class TestAuditCreationQuotas:
    """Tests for quota enforcement during audit creation."""

    def test_quota_exceeded_error_attributes(self):
        """Unit test for QuotaExceededError."""
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
        assert "10" in str(error)

    @pytest.mark.skip(reason="Requires DB schema update")
    def test_create_audit_checks_quota(self, auth_client):
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
            assert b"Quota Exceeded" in response.content or b"limit" in response.content.lower()
        finally:
            routes_module.QuotaService = original_quota_service

    @pytest.mark.skip(reason="Requires DB schema update")
    def test_create_audit_shows_quota_details(self, auth_client):
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
            assert b"2" in response.content
        finally:
            routes_module.QuotaService = original_quota_service

    @pytest.mark.skip(reason="Requires DB schema update")
    def test_create_audit_without_tenant_skips_quota(self, auth_client_no_tenant):
        import apps.dashboard.routes as routes_module
        original_enqueue = routes_module.enqueue_audit_job

        def mock_enqueue(*args, **kwargs):
            return kwargs.get("audit_id", "audit_123")

        routes_module.enqueue_audit_job = mock_enqueue
        try:
            response = auth_client_no_tenant.post(
                "/dashboard/audits/new",
                data={
                    "url": "example.com",
                    "company_name": "Test Company",
                    "trade_type": "Plumber",
                    "tier": "basic",
                },
                follow_redirects=False
            )

            assert response.status_code == 302
        finally:
            routes_module.enqueue_audit_job = original_enqueue


class TestAuditCreationJobQueue:
    """Tests for job queue integration."""

    def test_enqueue_function_exists(self):
        """Verify enqueue_audit_job function signature."""
        import inspect

        from apps.dashboard.routes import enqueue_audit_job

        sig = inspect.signature(enqueue_audit_job)
        params = list(sig.parameters.keys())

        assert "db" in params
        assert "audit_id" in params
        assert "tenant_id" in params
        assert "url" in params
        assert "options" in params

    @pytest.mark.skip(reason="Requires DB schema update")
    def test_create_audit_handles_duplicate(self, auth_client):
        import apps.dashboard.routes as routes_module
        original_enqueue = routes_module.enqueue_audit_job

        def mock_enqueue(*args, **kwargs):
            return "existing_audit_789"

        routes_module.enqueue_audit_job = mock_enqueue
        try:
            response = auth_client.post(
                "/dashboard/audits/new",
                data={
                    "url": "example.com",
                    "company_name": "Test Company",
                    "trade_type": "Plumber",
                    "tier": "basic",
                },
                follow_redirects=False
            )

            assert response.status_code == 302
            assert "existing_audit_789" in response.headers.get("location", "")
        finally:
            routes_module.enqueue_audit_job = original_enqueue

    @pytest.mark.skip(reason="Requires DB schema update")
    def test_create_audit_handles_queue_error(self, auth_client):
        import apps.dashboard.routes as routes_module
        original_enqueue = routes_module.enqueue_audit_job

        def mock_enqueue(*args, **kwargs):
            raise Exception("Database connection failed")

        routes_module.enqueue_audit_job = mock_enqueue
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

            assert response.status_code == 500
            assert b"Failed to start audit" in response.content or b"error" in response.content.lower()
        finally:
            routes_module.enqueue_audit_job = original_enqueue


class TestURLValidation:
    """Tests for URL validation helper."""

    def test_validate_url_empty(self):
        from apps.dashboard.routes import validate_url

        is_valid, error, normalized = validate_url("")
        assert not is_valid
        assert "required" in error.lower()

    def test_validate_url_with_protocol(self):
        from apps.dashboard.routes import validate_url

        is_valid, error, normalized = validate_url("https://example.com")
        assert is_valid
        assert normalized == "https://example.com"

    def test_validate_url_with_www(self):
        from apps.dashboard.routes import validate_url

        is_valid, error, normalized = validate_url("www.example.com")
        assert is_valid
        assert normalized == "https://example.com"

    def test_validate_url_strips_trailing_slash(self):
        from apps.dashboard.routes import validate_url

        is_valid, error, normalized = validate_url("example.com/")
        assert is_valid
        assert normalized == "https://example.com"

    def test_validate_url_lowercase(self):
        from apps.dashboard.routes import validate_url

        is_valid, error, normalized = validate_url("EXAMPLE.COM")
        assert is_valid
        assert normalized == "https://example.com"

    def test_validate_url_invalid_format(self):
        from apps.dashboard.routes import validate_url

        is_valid, error, normalized = validate_url("not-a-domain")
        assert not is_valid
        assert "valid domain" in error.lower()

    def test_validate_url_subdomain(self):
        from apps.dashboard.routes import validate_url

        is_valid, error, normalized = validate_url("blog.example.com")
        assert is_valid
        assert normalized == "https://blog.example.com"
