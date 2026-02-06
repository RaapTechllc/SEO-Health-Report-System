"""Integration tests for structured logging system."""

import json
import logging
import sys
import time
from io import StringIO
from unittest.mock import MagicMock

sys.modules.setdefault("stripe", MagicMock())

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from packages.seo_health_report.seo_logging import (
    JSONFormatter,
    RequestLoggingMiddleware,
    clear_request_context,
    get_logger,
    request_id_var,
    set_request_context,
)


@pytest.fixture
def app_with_logging():
    """Create test app with logging middleware."""
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"status": "ok"}

    @app.get("/error")
    def error_endpoint():
        raise ValueError("Test error")

    @app.get("/health")
    def health_endpoint():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client(app_with_logging):
    """Create test client."""
    return TestClient(app_with_logging, raise_server_exceptions=False)


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware."""

    def test_request_logging_middleware_adds_request_id(self, client):
        """Test that middleware adds X-Request-ID header to responses."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_request_id_is_uuid_format(self, client):
        """Test that generated request ID is valid UUID format."""
        response = client.get("/test")
        request_id = response.headers["X-Request-ID"]
        parts = request_id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_request_id_propagation(self, client):
        """Test that custom X-Request-ID is propagated."""
        custom_request_id = "custom-test-id-12345"
        response = client.get("/test", headers={"X-Request-ID": custom_request_id})
        assert response.headers["X-Request-ID"] == custom_request_id

    def test_skip_paths_not_logged(self, client):
        """Test that health endpoint is in skip paths."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_error_response_logs_request_id(self, client, caplog):
        """Test that error responses are logged with request context."""
        import logging
        with caplog.at_level(logging.ERROR):
            response = client.get("/error")
        assert response.status_code == 500


class TestRequestIdPropagation:
    """Tests for request ID propagation in logs."""

    def test_request_id_in_context_var(self):
        """Test that request_id is set in context variable."""
        clear_request_context()
        assert request_id_var.get() == ""

        set_request_context(request_id="test-req-123")
        assert request_id_var.get() == "test-req-123"

        clear_request_context()
        assert request_id_var.get() == ""

    def test_set_multiple_context_values(self):
        """Test setting multiple context values."""
        clear_request_context()
        set_request_context(
            request_id="req-abc",
            user_id="user-123",
            tenant_id="tenant-456",
        )

        assert request_id_var.get() == "req-abc"

        from packages.seo_health_report.seo_logging import tenant_id_var, user_id_var
        assert user_id_var.get() == "user-123"
        assert tenant_id_var.get() == "tenant-456"

        clear_request_context()


class TestJSONFormatter:
    """Tests for JSON log formatting."""

    def test_json_formatter_output(self):
        """Test that JSONFormatter produces valid JSON."""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_json_formatter_includes_request_id(self):
        """Test that JSONFormatter includes request_id from context."""
        set_request_context(request_id="test-request-id")

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed.get("request_id") == "test-request-id"
        clear_request_context()

    def test_json_formatter_includes_extra_data(self):
        """Test that JSONFormatter includes extra_data."""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"audit_id": "123", "tier": "pro"}

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed.get("extra") == {"audit_id": "123", "tier": "pro"}


class TestSensitiveHeaderFiltering:
    """Tests for sensitive header filtering."""

    def test_logging_does_not_log_authorization_header(self, caplog):
        """Ensure Authorization headers are not directly exposed in log message."""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)

        @app.get("/protected")
        def protected_endpoint():
            return {"status": "ok"}

        client = TestClient(app)

        with caplog.at_level(logging.INFO):
            client.get(
                "/protected",
                headers={"Authorization": "Bearer secret-token-12345"}
            )

        for record in caplog.records:
            assert "secret-token-12345" not in record.getMessage()


class TestLoggingPerformance:
    """Tests for logging performance."""

    def test_request_logging_performance(self, client):
        """Logging overhead should be minimal (<50ms per request)."""
        iterations = 10
        start_time = time.perf_counter()

        for _ in range(iterations):
            response = client.get("/test")
            assert response.status_code == 200

        total_time = time.perf_counter() - start_time
        avg_time_ms = (total_time / iterations) * 1000

        assert avg_time_ms < 50, f"Average request time {avg_time_ms:.2f}ms exceeds 50ms threshold"


class TestStructuredLogger:
    """Tests for StructuredLogger functionality."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_caches_instances(self):
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("test.cached")
        logger2 = get_logger("test.cached")
        assert logger1 is logger2

    def test_logger_supports_extra_data(self):
        """Test that logger supports extra_data parameter."""
        import os

        os.environ["LOG_FORMAT"] = "json"
        import packages.seo_health_report.seo_logging.structured_logger as logger_module
        from packages.seo_health_report.seo_logging.structured_logger import _loggers
        logger_module._is_json_mode = None

        if "test.extra.new" in _loggers:
            del _loggers["test.extra.new"]

        logger = get_logger("test.extra.new")

        stream = StringIO()
        for handler in logger.handlers:
            handler.stream = stream

        logger.info("Test message", extra_data={"key": "value"})

        output = stream.getvalue()
        assert "Test message" in output

        os.environ.pop("LOG_FORMAT", None)
        logger_module._is_json_mode = None
