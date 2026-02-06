"""
Tests for rate limit headers middleware.

Tests:
- X-RateLimit-* headers are added to responses
- Tier-based limits work correctly (basic/pro/enterprise)
- Per-tenant overrides work
- 429 responses include Retry-After header
- Authenticated and unauthenticated requests handled
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from apps.api.middleware.rate_limit import (
    SKIP_PATHS,
    RateLimitHeadersMiddleware,
    extract_auth_info,
)
from rate_limiter import (
    TIER_LIMITS,
    _request_counts,
    get_remaining_requests,
    get_reset_time,
    get_tenant_override,
    get_tier_limits,
    remove_tenant_override,
    set_tenant_override,
)


@pytest.fixture
def app():
    """Create test FastAPI app with rate limit middleware."""
    app = FastAPI()
    app.add_middleware(RateLimitHeadersMiddleware, default_tier="default", enabled=True)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Clear rate limit state before each test."""
    _request_counts.clear()
    yield
    _request_counts.clear()


class TestTierLimits:
    """Test tier-based rate limits."""

    def test_basic_tier_limits(self):
        limits = get_tier_limits("basic")
        assert limits["requests_per_minute"] == 100
        assert limits["audits_per_day"] == 5
        assert limits["concurrent_audits"] == 1

    def test_pro_tier_limits(self):
        limits = get_tier_limits("pro")
        assert limits["requests_per_minute"] == 500
        assert limits["audits_per_day"] == 25
        assert limits["concurrent_audits"] == 3

    def test_enterprise_tier_limits(self):
        limits = get_tier_limits("enterprise")
        assert limits["requests_per_minute"] == 2000
        assert limits["audits_per_day"] == 100
        assert limits["concurrent_audits"] == 10

    def test_unknown_tier_uses_default(self):
        limits = get_tier_limits("unknown_tier")
        assert limits == get_tier_limits("default")


class TestTenantOverrides:
    """Test per-tenant override support."""

    def test_set_tenant_override(self):
        set_tenant_override("tenant_123", {"requests_per_minute": 1000})
        override = get_tenant_override("tenant_123")
        assert override == {"requests_per_minute": 1000}

    def test_remove_tenant_override(self):
        set_tenant_override("tenant_456", {"requests_per_minute": 1500})
        remove_tenant_override("tenant_456")
        assert get_tenant_override("tenant_456") is None

    def test_tenant_override_applied_to_limits(self):
        set_tenant_override("tenant_789", {"requests_per_minute": 3000})
        limits = get_tier_limits("basic", tenant_id="tenant_789")
        assert limits["requests_per_minute"] == 3000
        assert limits["audits_per_day"] == 5  # unchanged
        remove_tenant_override("tenant_789")

    def test_tenant_override_without_base_tier(self):
        set_tenant_override("tenant_abc", {"concurrent_audits": 20})
        limits = get_tier_limits("default", tenant_id="tenant_abc")
        assert limits["concurrent_audits"] == 20
        remove_tenant_override("tenant_abc")


class TestRateLimitHeaders:
    """Test X-RateLimit-* headers in responses."""

    def test_headers_present_in_response(self, client):
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_limit_header_value(self, client):
        response = client.get("/test")
        limit = int(response.headers["X-RateLimit-Limit"])
        assert limit == TIER_LIMITS["default"]["requests_per_minute"]

    def test_remaining_decrements(self, client):
        response1 = client.get("/test")
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])

        response2 = client.get("/test")
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])

        assert remaining2 == remaining1 - 1

    def test_reset_header_is_positive(self, client):
        response = client.get("/test")
        reset = int(response.headers["X-RateLimit-Reset"])
        assert 0 <= reset <= 60

    def test_tier_header_present(self, client):
        response = client.get("/test")
        assert "X-RateLimit-Tier" in response.headers


class TestSkipPaths:
    """Test that certain paths skip rate limiting."""

    def test_health_endpoint_no_rate_limit_headers(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers

    def test_skip_paths_configured(self):
        assert "/health" in SKIP_PATHS
        assert "/" in SKIP_PATHS
        assert "/docs" in SKIP_PATHS
        assert "/openapi.json" in SKIP_PATHS


class TestRateLimitExceeded:
    """Test 429 responses when rate limit exceeded."""

    def test_429_includes_retry_after(self):
        app = FastAPI()
        app.add_middleware(RateLimitHeadersMiddleware, default_tier="default", enabled=True)

        @app.get("/limited")
        async def limited():
            return {"ok": True}

        client = TestClient(app)

        # Set a very low limit for testing
        with patch.dict(TIER_LIMITS, {"default": {"requests_per_minute": 2, "audits_per_day": 1, "concurrent_audits": 1}}):
            _request_counts.clear()

            # Make requests up to limit
            client.get("/limited")
            client.get("/limited")

            # Third request should be rate limited
            response = client.get("/limited")
            assert response.status_code == 429
            assert "Retry-After" in response.headers
            assert int(response.headers["Retry-After"]) >= 0

    def test_429_response_body(self):
        app = FastAPI()
        app.add_middleware(RateLimitHeadersMiddleware, default_tier="default", enabled=True)

        @app.get("/limited2")
        async def limited2():
            return {"ok": True}

        client = TestClient(app)

        with patch.dict(TIER_LIMITS, {"default": {"requests_per_minute": 1, "audits_per_day": 1, "concurrent_audits": 1}}):
            _request_counts.clear()

            client.get("/limited2")
            response = client.get("/limited2")

            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert "Rate limit exceeded" in data["detail"]


class TestAuthExtraction:
    """Test extraction of auth info from requests."""

    def test_extract_default_tier_unauthenticated(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        del request.state.user
        request.headers = {}

        tier, tenant_id = extract_auth_info(request)
        assert tier == "default"
        assert tenant_id is None

    def test_extract_tier_from_header(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        del request.state.user
        request.headers = {"X-Tier": "pro"}

        tier, tenant_id = extract_auth_info(request)
        assert tier == "pro"

    def test_extract_tenant_from_header(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        del request.state.user
        request.headers = {"X-Tenant-ID": "tenant_xyz"}

        tier, tenant_id = extract_auth_info(request)
        assert tenant_id == "tenant_xyz"

    def test_extract_from_user_state(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.user = MagicMock(tier="enterprise", tenant_id="tenant_abc")
        request.headers = {}

        tier, tenant_id = extract_auth_info(request)
        assert tier == "enterprise"
        assert tenant_id == "tenant_abc"


class TestHelperFunctions:
    """Test helper functions for getting rate limit info."""

    def test_get_remaining_requests(self):
        request = MagicMock(spec=Request)
        request.client = MagicMock(host="127.0.0.1")
        request.headers = {}

        _request_counts.clear()
        remaining = get_remaining_requests(request, "basic")
        assert remaining == 100  # basic tier limit

    def test_get_reset_time(self):
        request = MagicMock(spec=Request)
        request.client = MagicMock(host="127.0.0.1")
        request.headers = {}

        _request_counts.clear()
        reset = get_reset_time(request)
        assert reset == 60  # default window


class TestMiddlewareDisabled:
    """Test middleware can be disabled."""

    def test_disabled_middleware_passes_through(self):
        app = FastAPI()
        app.add_middleware(RateLimitHeadersMiddleware, enabled=False)

        @app.get("/test")
        async def test():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers
