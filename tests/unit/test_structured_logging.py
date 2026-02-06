"""
Tests for structured logging system.
"""

import json
import logging
import os
import sys
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.seo_health_report.seo_logging.structured_logger import (
    JSONFormatter,
    clear_request_context,
    get_log_level,
    get_logger,
    is_json_logging_enabled,
    request_id_var,
    set_request_context,
    tenant_id_var,
    user_id_var,
)


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def test_basic_format(self):
        """Test basic log message formatting."""
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
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")

    def test_format_with_args(self):
        """Test formatting with string arguments."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="User %s logged in",
            args=("alice",),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["message"] == "User alice logged in"

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert data["exception_type"] == "ValueError"

    def test_format_with_context(self):
        """Test formatting includes request context."""
        formatter = JSONFormatter()

        set_request_context(
            request_id="req-123",
            user_id="user-456",
            tenant_id="tenant-789",
        )

        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test",
                args=(),
                exc_info=None,
            )

            output = formatter.format(record)
            data = json.loads(output)

            assert data["request_id"] == "req-123"
            assert data["user_id"] == "user-456"
            assert data["tenant_id"] == "tenant-789"
        finally:
            clear_request_context()

    def test_warning_includes_location(self):
        """Test that WARNING+ logs include file location."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="/app/src/module.py",
            lineno=42,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        record.funcName = "process_data"

        output = formatter.format(record)
        data = json.loads(output)

        assert "location" in data
        assert ":42" in data["location"]
        assert data["function"] == "process_data"

    def test_info_excludes_location(self):
        """Test that INFO logs don't include file location."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/app/src/module.py",
            lineno=42,
            msg="Info message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "location" not in data


class TestRequestContext:
    """Tests for request context management."""

    def test_set_and_clear_context(self):
        """Test setting and clearing request context."""
        set_request_context(
            request_id="req-abc",
            user_id="user-def",
            tenant_id="tenant-ghi",
        )

        assert request_id_var.get() == "req-abc"
        assert user_id_var.get() == "user-def"
        assert tenant_id_var.get() == "tenant-ghi"

        clear_request_context()

        assert request_id_var.get() == ""
        assert user_id_var.get() == ""
        assert tenant_id_var.get() == ""

    def test_partial_context_set(self):
        """Test setting only some context values."""
        clear_request_context()

        set_request_context(request_id="req-only")

        assert request_id_var.get() == "req-only"
        assert user_id_var.get() == ""
        assert tenant_id_var.get() == ""

        clear_request_context()

    def test_context_isolation(self):
        """Test that context doesn't leak between tests."""
        assert request_id_var.get() == ""


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_logger_caching(self):
        """Test that same logger is returned for same name."""
        logger1 = get_logger("test.cached")
        logger2 = get_logger("test.cached")
        assert logger1 is logger2

    def test_logger_has_handler(self):
        """Test that logger has at least one handler."""
        logger = get_logger("test.handler")
        assert len(logger.handlers) > 0

    @patch.dict(os.environ, {"APP_ENV": "production", "LOG_FORMAT": ""})
    def test_json_in_production(self):
        """Test JSON formatting in production environment."""
        from packages.seo_health_report.seo_logging import structured_logger
        structured_logger._is_json_mode = None
        structured_logger._loggers.clear()

        assert is_json_logging_enabled() is True

        structured_logger._is_json_mode = None

    @patch.dict(os.environ, {"APP_ENV": "development", "LOG_FORMAT": ""})
    def test_text_in_development(self):
        """Test text formatting in development environment."""
        from packages.seo_health_report.seo_logging import structured_logger
        structured_logger._is_json_mode = None

        assert is_json_logging_enabled() is False

        structured_logger._is_json_mode = None

    @patch.dict(os.environ, {"APP_ENV": "development", "LOG_FORMAT": "json"})
    def test_force_json_format(self):
        """Test forcing JSON format via LOG_FORMAT."""
        from packages.seo_health_report.seo_logging import structured_logger
        structured_logger._is_json_mode = None

        assert is_json_logging_enabled() is True

        structured_logger._is_json_mode = None


class TestLogLevel:
    """Tests for log level configuration."""

    @patch.dict(os.environ, {"SEO_HEALTH_LOG_LEVEL": "DEBUG"})
    def test_debug_level(self):
        """Test DEBUG log level from environment."""
        assert get_log_level() == logging.DEBUG

    @patch.dict(os.environ, {"SEO_HEALTH_LOG_LEVEL": "WARNING"})
    def test_warning_level(self):
        """Test WARNING log level from environment."""
        assert get_log_level() == logging.WARNING

    @patch.dict(os.environ, {"SEO_HEALTH_LOG_LEVEL": "invalid"})
    def test_invalid_level_defaults_to_info(self):
        """Test invalid log level defaults to INFO."""
        assert get_log_level() == logging.INFO

    @patch.dict(os.environ, {}, clear=True)
    def test_default_level_is_info(self):
        """Test default log level is INFO."""
        if "SEO_HEALTH_LOG_LEVEL" in os.environ:
            del os.environ["SEO_HEALTH_LOG_LEVEL"]
        assert get_log_level() == logging.INFO


class TestLogOutput:
    """Integration tests for actual log output."""

    def test_log_message_output(self):
        """Test that log messages are actually output."""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())

        test_logger = logging.getLogger("test.output")
        test_logger.handlers = [handler]
        test_logger.setLevel(logging.INFO)
        test_logger.propagate = False

        test_logger.info("Test log message")

        output = stream.getvalue()
        assert output.strip()

        data = json.loads(output)
        assert data["message"] == "Test log message"
        assert data["level"] == "INFO"

    def test_extra_data_in_output(self):
        """Test that extra_data appears in log output."""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())

        test_logger = logging.getLogger("test.extra")
        test_logger.handlers = [handler]
        test_logger.setLevel(logging.INFO)
        test_logger.propagate = False

        record = test_logger.makeRecord(
            test_logger.name,
            logging.INFO,
            "test.py",
            1,
            "Test with extra",
            (),
            None,
        )
        record.extra_data = {"audit_id": "123", "tier": "pro"}
        test_logger.handle(record)

        output = stream.getvalue()
        data = json.loads(output)

        assert data["extra"]["audit_id"] == "123"
        assert data["extra"]["tier"] == "pro"
