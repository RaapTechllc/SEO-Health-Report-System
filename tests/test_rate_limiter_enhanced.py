"""
Tests for enhanced rate limiting functionality.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from rate_limiter import (
    ENDPOINT_LIMITS,
    TIER_LIMITS,
    _audit_counts,
    _endpoint_counts,
    _request_counts,
    add_rate_limit_headers,
    check_audit_limit,
    check_endpoint_limit,
    check_rate_limit,
    get_client_ip,
    get_rate_limit_status,
    get_tier_limits,
)


@pytest.fixture(autouse=True)
def clear_rate_limit_state():
    """Clear rate limit state before each test."""
    _request_counts.clear()
    _audit_counts.clear()
    _endpoint_counts.clear()


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers = {}
    request.url.path = "/audit"
    return request


class TestTierLimits:
    """Tests for tier-based rate limits."""

    def test_tier_limits_exist(self):
        """Test that all tiers have limits defined."""
        assert "basic" in TIER_LIMITS
        assert "pro" in TIER_LIMITS
        assert "enterprise" in TIER_LIMITS
        assert "default" in TIER_LIMITS

    def test_tier_hierarchy(self):
        """Test that higher tiers have higher limits."""
        basic = TIER_LIMITS["basic"]
        pro = TIER_LIMITS["pro"]
        enterprise = TIER_LIMITS["enterprise"]

        assert pro["requests_per_minute"] > basic["requests_per_minute"]
        assert enterprise["requests_per_minute"] > pro["requests_per_minute"]

        assert pro["audits_per_day"] > basic["audits_per_day"]
        assert enterprise["audits_per_day"] > pro["audits_per_day"]

    def test_get_tier_limits_valid(self):
        """Test getting limits for valid tier."""
        limits = get_tier_limits("pro")
        assert limits["requests_per_minute"] == 500
        assert limits["audits_per_day"] == 25

    def test_get_tier_limits_invalid(self):
        """Test getting limits for invalid tier returns default."""
        limits = get_tier_limits("invalid_tier")
        assert limits == TIER_LIMITS["default"]

    def test_all_tiers_have_required_fields(self):
        """Test that all tiers have required limit fields."""
        required_fields = ["requests_per_minute", "audits_per_day", "concurrent_audits"]

        for tier, limits in TIER_LIMITS.items():
            for field in required_fields:
                assert field in limits, f"Tier {tier} missing field {field}"


class TestEndpointLimits:
    """Tests for per-endpoint rate limits."""

    def test_endpoint_limits_exist(self):
        """Test that endpoint limits are defined."""
        assert "/audit" in ENDPOINT_LIMITS
        assert "/checkout/create" in ENDPOINT_LIMITS
        assert "/auth/register" in ENDPOINT_LIMITS
        assert "/auth/login" in ENDPOINT_LIMITS

    def test_check_endpoint_limit_applies(self, mock_request):
        """Test that endpoint limits are applied."""
        mock_request.url.path = "/audit"

        result = check_endpoint_limit(mock_request)

        assert result is not None
        assert "endpoint_limit" in result
        assert result["endpoint_limit"] == ENDPOINT_LIMITS["/audit"]

    def test_check_endpoint_limit_no_match(self, mock_request):
        """Test that non-matching paths return None."""
        mock_request.url.path = "/some/other/path"

        result = check_endpoint_limit(mock_request)

        assert result is None

    def test_endpoint_limit_exceeded(self, mock_request):
        """Test that endpoint limit raises 429 when exceeded."""
        mock_request.url.path = "/checkout/create"
        limit = ENDPOINT_LIMITS["/checkout/create"]

        # Make requests up to the limit
        for _ in range(limit):
            check_endpoint_limit(mock_request)

        # Next request should fail
        with pytest.raises(HTTPException) as exc_info:
            check_endpoint_limit(mock_request)

        assert exc_info.value.status_code == 429


class TestRateLimitHeaders:
    """Tests for rate limit headers."""

    def test_add_rate_limit_headers(self):
        """Test that headers are added correctly."""
        response = MagicMock()
        response.headers = {}

        rate_info = {
            "limit": 100,
            "remaining": 50,
            "reset": 3600,
            "tier": "basic",
        }

        add_rate_limit_headers(response, rate_info)

        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "50"
        assert response.headers["X-RateLimit-Reset"] == "3600"
        assert response.headers["X-RateLimit-Tier"] == "basic"


class TestCheckRateLimit:
    """Tests for the check_rate_limit function."""

    def test_check_rate_limit_returns_info(self, mock_request):
        """Test that check_rate_limit returns rate info."""
        result = check_rate_limit(mock_request, "basic")

        assert "limit" in result
        assert "remaining" in result
        assert "reset" in result
        assert "tier" in result

    def test_check_rate_limit_decrements_remaining(self, mock_request):
        """Test that remaining count decrements."""
        result1 = check_rate_limit(mock_request, "basic")
        result2 = check_rate_limit(mock_request, "basic")

        assert result2["remaining"] < result1["remaining"]

    def test_check_rate_limit_exceeded(self, mock_request):
        """Test that 429 is raised when limit exceeded."""
        tier = "basic"
        limit = TIER_LIMITS[tier]["requests_per_minute"]

        # Make requests up to the limit
        for _ in range(limit):
            check_rate_limit(mock_request, tier)

        # Next request should fail
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(mock_request, tier)

        assert exc_info.value.status_code == 429
        assert "X-RateLimit-Limit" in exc_info.value.headers
        assert "Retry-After" in exc_info.value.headers


class TestCheckAuditLimit:
    """Tests for the check_audit_limit function."""

    def test_check_audit_limit_returns_info(self):
        """Test that check_audit_limit returns audit info."""
        result = check_audit_limit("user_123", "basic")

        assert "limit" in result
        assert "remaining" in result
        assert "reset" in result
        assert "tier" in result

    def test_check_audit_limit_tier_specific(self):
        """Test that different tiers have different limits."""
        basic_result = check_audit_limit("user_basic", "basic")
        pro_result = check_audit_limit("user_pro", "pro")

        assert pro_result["limit"] > basic_result["limit"]

    def test_check_audit_limit_exceeded(self):
        """Test that 429 is raised when audit limit exceeded."""
        tier = "basic"
        limit = TIER_LIMITS[tier]["audits_per_day"]
        user_id = "user_audit_test"

        # Make audits up to the limit
        for _ in range(limit):
            check_audit_limit(user_id, tier)

        # Next audit should fail
        with pytest.raises(HTTPException) as exc_info:
            check_audit_limit(user_id, tier)

        assert exc_info.value.status_code == 429
        assert "X-RateLimit-Audit-Limit" in exc_info.value.headers


class TestRateLimitStatus:
    """Tests for get_rate_limit_status function."""

    def test_get_rate_limit_status(self, mock_request):
        """Test getting rate limit status."""
        status = get_rate_limit_status(mock_request, "pro")

        assert status["tier"] == "pro"
        assert "requests" in status
        assert "limits" in status
        assert status["requests"]["limit"] == TIER_LIMITS["pro"]["requests_per_minute"]


class TestClientIPExtraction:
    """Tests for client IP extraction."""

    def test_get_client_ip_direct(self, mock_request):
        """Test getting IP from direct connection."""
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"

        ip = get_client_ip(mock_request)

        assert ip == "192.168.1.1"

    def test_get_client_ip_forwarded(self, mock_request):
        """Test getting IP from X-Forwarded-For header."""
        mock_request.headers = {"x-forwarded-for": "10.0.0.1, 192.168.1.1"}

        ip = get_client_ip(mock_request)

        assert ip == "10.0.0.1"

    def test_get_client_ip_no_client(self):
        """Test handling when client is None."""
        request = MagicMock()
        request.headers = {}
        request.client = None

        ip = get_client_ip(request)

        assert ip == "unknown"
