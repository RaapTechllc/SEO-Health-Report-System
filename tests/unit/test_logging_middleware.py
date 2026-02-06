"""
Tests for logging middleware.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.seo_health_report.seo_logging.middleware import (
    RequestLoggingMiddleware,
    UserContextMiddleware,
)
from packages.seo_health_report.seo_logging.structured_logger import (
    clear_request_context,
    request_id_var,
    tenant_id_var,
    user_id_var,
)


class MockRequest:
    """Mock Starlette Request for testing."""

    def __init__(
        self,
        method: str = "GET",
        path: str = "/test",
        query_params: dict = None,
        headers: dict = None,
        client_host: str = "127.0.0.1",
    ):
        self.method = method
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.client = MagicMock()
        self.client.host = client_host
        self.url = MagicMock()
        self.url.path = path
        self.state = MagicMock()
        self.state.user_id = None
        self.state.tenant_id = None


class MockResponse:
    """Mock Starlette Response for testing."""

    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.headers = {}


@pytest.fixture
def clear_context():
    """Clear request context before and after each test."""
    clear_request_context()
    yield
    clear_request_context()


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware."""

    @pytest.mark.asyncio
    async def test_generates_request_id(self, clear_context):
        """Test that middleware generates request ID if not present."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest()
        response = MockResponse()

        async def call_next(req):
            assert request_id_var.get() != ""
            return response

        result = await middleware.dispatch(request, call_next)

        assert "X-Request-ID" in result.headers
        assert len(result.headers["X-Request-ID"]) == 36

    @pytest.mark.asyncio
    async def test_propagates_existing_request_id(self, clear_context):
        """Test that middleware propagates existing X-Request-ID."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest(headers={"X-Request-ID": "existing-id-123"})
        response = MockResponse()

        async def call_next(req):
            assert request_id_var.get() == "existing-id-123"
            return response

        result = await middleware.dispatch(request, call_next)

        assert result.headers["X-Request-ID"] == "existing-id-123"

    @pytest.mark.asyncio
    async def test_skips_health_endpoint(self, clear_context):
        """Test that /health endpoint is not logged."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest(path="/health")
        response = MockResponse()


        async def call_next(req):
            return response

        with patch("packages.seo_health_report.seo_logging.middleware.logger") as mock_logger:
            await middleware.dispatch(request, call_next)
            mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_logs_regular_endpoint(self, clear_context):
        """Test that regular endpoints are logged."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest(path="/api/audit", method="POST")
        response = MockResponse(status_code=201)

        async def call_next(req):
            return response

        with patch("packages.seo_health_report.seo_logging.middleware.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            assert mock_logger.info.call_count == 2

            start_call = mock_logger.info.call_args_list[0]
            assert start_call[0][0] == "request_started"

            end_call = mock_logger.info.call_args_list[1]
            assert end_call[0][0] == "request_completed"

    @pytest.mark.asyncio
    async def test_logs_warning_on_4xx(self, clear_context):
        """Test that 4xx responses are logged as warnings."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest(path="/api/test")
        response = MockResponse(status_code=404)

        async def call_next(req):
            return response

        with patch("packages.seo_health_report.seo_logging.middleware.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_exception(self, clear_context):
        """Test that exceptions are logged."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest(path="/api/test")

        async def call_next(req):
            raise ValueError("Test error")

        with patch("packages.seo_health_report.seo_logging.middleware.logger") as mock_logger:
            with pytest.raises(ValueError):
                await middleware.dispatch(request, call_next)

            mock_logger.exception.assert_called_once()
            call_kwargs = mock_logger.exception.call_args[1]
            assert call_kwargs["extra_data"]["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_clears_context_after_request(self, clear_context):
        """Test that context is cleared after request completes."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest()
        response = MockResponse()

        async def call_next(req):
            assert request_id_var.get() != ""
            return response

        await middleware.dispatch(request, call_next)

        assert request_id_var.get() == ""

    @pytest.mark.asyncio
    async def test_clears_context_on_exception(self, clear_context):
        """Test that context is cleared even when exception occurs."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest()

        async def call_next(req):
            raise RuntimeError("Test")

        with pytest.raises(RuntimeError):
            await middleware.dispatch(request, call_next)

        assert request_id_var.get() == ""

    @pytest.mark.asyncio
    async def test_extracts_forwarded_ip(self, clear_context):
        """Test extraction of client IP from X-Forwarded-For."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(app)

        request = MockRequest(
            headers={"X-Forwarded-For": "203.0.113.50, 70.41.3.18"},
            client_host="10.0.0.1",
        )
        response = MockResponse()

        async def call_next(req):
            return response

        with patch("packages.seo_health_report.seo_logging.middleware.logger") as mock_logger:
            await middleware.dispatch(request, call_next)

            start_call = mock_logger.info.call_args_list[0]
            extra_data = start_call[1]["extra_data"]
            assert extra_data["client_ip"] == "203.0.113.50"

    @pytest.mark.asyncio
    async def test_custom_skip_paths(self, clear_context):
        """Test custom skip paths configuration."""
        app = MagicMock()
        middleware = RequestLoggingMiddleware(
            app,
            skip_paths={"/custom", "/internal"}
        )

        request = MockRequest(path="/custom")
        response = MockResponse()

        async def call_next(req):
            return response

        with patch("packages.seo_health_report.seo_logging.middleware.logger") as mock_logger:
            await middleware.dispatch(request, call_next)
            mock_logger.info.assert_not_called()


class TestUserContextMiddleware:
    """Tests for UserContextMiddleware."""

    @pytest.mark.asyncio
    async def test_sets_user_context(self, clear_context):
        """Test that user context is set from request.state."""
        app = MagicMock()
        middleware = UserContextMiddleware(app)

        request = MockRequest()
        request.state.user = MagicMock()
        request.state.user.id = "user-123"
        request.state.user.tenant_id = "tenant-456"

        response = MockResponse()

        async def call_next(req):
            assert user_id_var.get() == "user-123"
            assert tenant_id_var.get() == "tenant-456"
            return response

        await middleware.dispatch(request, call_next)

    @pytest.mark.asyncio
    async def test_no_user_no_context(self, clear_context):
        """Test that missing user doesn't cause error."""
        app = MagicMock()
        middleware = UserContextMiddleware(app)

        request = MockRequest()
        del request.state.user

        response = MockResponse()

        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 200


class TestClientIPExtraction:
    """Tests for client IP extraction."""

    def test_get_client_ip_from_forwarded(self):
        """Test IP extraction from X-Forwarded-For."""
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MockRequest(headers={"X-Forwarded-For": "1.2.3.4"})
        assert middleware._get_client_ip(request) == "1.2.3.4"

    def test_get_client_ip_from_real_ip(self):
        """Test IP extraction from X-Real-IP."""
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MockRequest(headers={"X-Real-IP": "5.6.7.8"})
        assert middleware._get_client_ip(request) == "5.6.7.8"

    def test_get_client_ip_from_client(self):
        """Test IP extraction from request.client."""
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MockRequest(client_host="9.10.11.12")
        assert middleware._get_client_ip(request) == "9.10.11.12"

    def test_get_client_ip_multiple_forwarded(self):
        """Test IP extraction with multiple forwarded IPs."""
        middleware = RequestLoggingMiddleware(MagicMock())

        request = MockRequest(
            headers={"X-Forwarded-For": "1.1.1.1, 2.2.2.2, 3.3.3.3"}
        )
        assert middleware._get_client_ip(request) == "1.1.1.1"
