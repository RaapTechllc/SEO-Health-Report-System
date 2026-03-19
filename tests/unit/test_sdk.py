"""
Tests for SEO Health SDK.
"""

from datetime import datetime

import pytest

from packages.seo_health_sdk import (
    AsyncSEOHealthClient,
    SEOHealthClient,
)
from packages.seo_health_sdk.auth import RefreshableTokenAuth, TokenAuth
from packages.seo_health_sdk.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SEOHealthError,
    ValidationError,
    raise_for_status,
)
from packages.seo_health_sdk.models import (
    AuditRequest,
    AuditResponse,
    AuditResult,
    AuditStatus,
    AuditTier,
    Branding,
    TokenResponse,
    Webhook,
    WebhookEvent,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_seo_health_error_base(self):
        error = SEOHealthError("Test error")
        assert str(error) == "Test error"

    def test_seo_health_error_with_status_code(self):
        error = SEOHealthError("Test error", status_code=500)
        assert error.status_code == 500
        assert "[500]" in str(error)

    def test_authentication_error(self):
        error = AuthenticationError("Invalid token", status_code=401)
        assert error.status_code == 401
        assert "Invalid token" in str(error)

    def test_not_found_error(self):
        error = NotFoundError("Audit not found", status_code=404)
        assert error.status_code == 404

    def test_rate_limit_error(self):
        error = RateLimitError("Too many requests", retry_after=60)
        assert error.status_code == 429
        assert error.retry_after == 60

    def test_validation_error(self):
        error = ValidationError("Invalid URL format", status_code=422)
        assert error.status_code == 422

    def test_api_error(self):
        error = APIError("Server error", status_code=500, response_data={"code": "INTERNAL"})
        assert error.status_code == 500
        assert error.response_data == {"code": "INTERNAL"}

    def test_raise_for_status_401(self):
        with pytest.raises(AuthenticationError) as exc:
            raise_for_status(401, {"detail": "Unauthorized"})
        assert exc.value.status_code == 401

    def test_raise_for_status_404(self):
        with pytest.raises(NotFoundError) as exc:
            raise_for_status(404, {"detail": "Not found"})
        assert exc.value.status_code == 404

    def test_raise_for_status_429(self):
        with pytest.raises(RateLimitError) as exc:
            raise_for_status(429, {"detail": "Rate limited"}, {"Retry-After": "60"})
        assert exc.value.retry_after == 60

    def test_raise_for_status_500(self):
        with pytest.raises(APIError) as exc:
            raise_for_status(500, {"detail": "Server error"})
        assert exc.value.status_code == 500


class TestModels:
    """Test Pydantic models."""

    def test_audit_request(self):
        request = AuditRequest(
            url="https://example.com",
            company_name="Example Inc",
            tier=AuditTier.PREMIUM,
        )
        assert request.url == "https://example.com"
        assert request.company_name == "Example Inc"
        assert request.tier == AuditTier.PREMIUM

    def test_audit_request_default_tier(self):
        request = AuditRequest(
            url="https://example.com",
            company_name="Example Inc",
        )
        assert request.tier == AuditTier.FREE

    def test_audit_response(self):
        response = AuditResponse(
            id="audit_123",
            url="https://example.com",
            company_name="Example Inc",
            status=AuditStatus.COMPLETED,
            tier=AuditTier.FREE,
            created_at=datetime.utcnow(),
        )
        assert response.id == "audit_123"
        assert response.status == AuditStatus.COMPLETED

    def test_audit_result(self):
        result = AuditResult(
            id="audit_123",
            url="https://example.com",
            company_name="Example Inc",
            status=AuditStatus.COMPLETED,
            tier=AuditTier.FREE,
            created_at=datetime.utcnow(),
        )
        assert result.id == "audit_123"

    def test_token_response(self):
        token = TokenResponse(
            access_token="jwt.token.here",
            token_type="bearer",
        )
        assert token.access_token == "jwt.token.here"
        assert token.token_type == "bearer"

    def test_webhook_model(self):
        webhook = Webhook(
            id="webhook_123",
            url="https://hooks.example.com",
            events=[WebhookEvent.AUDIT_COMPLETED],
            created_at=datetime.utcnow(),
        )
        assert webhook.id == "webhook_123"
        assert WebhookEvent.AUDIT_COMPLETED in webhook.events

    def test_branding_model(self):
        branding = Branding(
            primary_color="#1E3A8A",
            secondary_color="#3B82F6",
        )
        assert branding.primary_color == "#1E3A8A"


class TestTokenAuth:
    """Test authentication classes."""

    def test_token_auth_init(self):
        auth = TokenAuth("test_token")
        assert auth._token == "test_token"

    def test_refreshable_token_auth(self):
        auth = RefreshableTokenAuth(
            token="initial_token",
            refresh_url="http://localhost/auth/refresh",
        )
        assert auth._token == "initial_token"
        assert auth._refresh_url == "http://localhost/auth/refresh"


class TestSEOHealthClient:
    """Test sync client."""

    def test_init_with_token(self):
        client = SEOHealthClient(
            base_url="http://localhost:8000",
            token="test_token",
        )
        assert client.base_url == "http://localhost:8000"
        assert client._auth._token == "test_token"
        client.close()

    def test_init_with_base_url(self):
        client = SEOHealthClient(base_url="http://api.example.com")
        assert client.base_url == "http://api.example.com"
        client.close()

    def test_context_manager(self):
        with SEOHealthClient(base_url="http://localhost:8000") as client:
            assert client.base_url == "http://localhost:8000"


class TestAsyncSEOHealthClient:
    """Test async client."""

    def test_init(self):
        client = AsyncSEOHealthClient(
            base_url="http://api.example.com",
            token="async_token",
        )
        assert client.base_url == "http://api.example.com"
        assert client._auth._token == "async_token"


class TestSDKExports:
    """Test public exports from SDK."""

    def test_main_exports(self):
        from packages.seo_health_sdk import (
            AsyncSEOHealthClient,
            SEOHealthClient,
            SEOHealthError,
        )

        assert SEOHealthClient is not None
        assert AsyncSEOHealthClient is not None
        assert SEOHealthError is not None

    def test_model_exports(self):
        from packages.seo_health_sdk.models import (
            AuditRequest,
            Webhook,
        )

        assert AuditRequest is not None
        assert Webhook is not None


class TestAuditTierEnum:
    """Test AuditTier enum."""

    def test_tier_values(self):
        assert AuditTier.FREE.value == "free"
        assert AuditTier.PREMIUM.value == "premium"
        assert AuditTier.ENTERPRISE.value == "enterprise"


class TestAuditStatusEnum:
    """Test AuditStatus enum."""

    def test_status_values(self):
        assert AuditStatus.PENDING.value == "pending"
        assert AuditStatus.IN_PROGRESS.value == "in_progress"
        assert AuditStatus.COMPLETED.value == "completed"
        assert AuditStatus.FAILED.value == "failed"
