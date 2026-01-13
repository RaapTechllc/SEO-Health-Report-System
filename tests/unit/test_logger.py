"""
Tests for logger module.
"""

import os
import logging
import pytest
from seo_health_report.scripts.logger import (
    get_logger,
    set_log_level,
    _get_log_level,
    _get_default_log_file,
    _get_console_handler,
    _get_file_handler,
)


class TestLogLevel:
    """Test log level configuration."""

    def test_default_log_level(self):
        """Test default log level is INFO."""
        logger = get_logger("test_default")
        assert logger.level == logging.INFO

    def test_custom_log_level_debug(self):
        """Test custom DEBUG log level."""
        logger = get_logger("test_debug", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_custom_log_level_warning(self):
        """Test custom WARNING log level."""
        logger = get_logger("test_warning", level="WARNING")
        assert logger.level == logging.WARNING

    def test_environment_variable_log_level(self, monkeypatch):
        """Test log level from environment variable."""
        monkeypatch.setenv("SEO_HEALTH_LOG_LEVEL", "ERROR")
        logger = get_logger("test_env")
        assert logger.level == logging.ERROR

    def test_invalid_log_level_fallback(self):
        """Test invalid log level falls back to INFO."""
        logger = get_logger("test_invalid", level="INVALID")
        assert logger.level == logging.INFO


class TestGetLogLevel:
    """Test _get_log_level function."""

    def test_get_log_level_none(self):
        """Test _get_log_level with None uses environment."""
        level = _get_log_level(None)
        assert level == logging.INFO  # Default from env

    def test_get_log_level_debug(self):
        """Test _get_log_level with DEBUG."""
        level = _get_log_level("DEBUG")
        assert level == logging.DEBUG

    def test_get_log_level_info(self):
        """Test _get_log_level with INFO."""
        level = _get_log_level("INFO")
        assert level == logging.INFO

    def test_get_log_level_warning(self):
        """Test _get_log_level with WARNING."""
        level = _get_log_level("WARNING")
        assert level == logging.WARNING

    def test_get_log_level_error(self):
        """Test _get_log_level with ERROR."""
        level = _get_log_level("ERROR")
        assert level == logging.ERROR

    def test_get_log_level_critical(self):
        """Test _get_log_level with CRITICAL."""
        level = _get_log_level("CRITICAL")
        assert level == logging.CRITICAL

    def test_get_log_level_case_insensitive(self):
        """Test _get_log_level is case insensitive."""
        level1 = _get_log_level("debug")
        level2 = _get_log_level("DEBUG")
        level3 = _get_log_level("DeBuG")
        assert level1 == level2 == level3 == logging.DEBUG


class TestLogFile:
    """Test log file configuration."""

    def test_default_log_file(self):
        """Test default log file path."""
        log_file = _get_default_log_file()
        assert "logs" in log_file
        assert "seo-health-report.log" in log_file

    def test_log_file_created(self, tmp_path, monkeypatch):
        """Test log file is created when needed."""
        import uuid

        # Set temp directory as log dir
        log_dir = str(tmp_path / "logs")
        os.makedirs(log_dir, exist_ok=True)

        monkeypatch.setenv("SEO_HEALTH_LOG_DIR", log_dir)

        # Use unique logger name to avoid caching issues
        unique_name = f"test_file_{uuid.uuid4().hex[:8]}"

        # Get logger which should create log file
        logger = get_logger(unique_name)

        # Write a log message
        logger.info("Test message")

        # Check log file exists
        log_file = os.path.join(log_dir, "seo-health-report.log")
        assert os.path.exists(log_file)


class TestLoggerHandlers:
    """Test logger handlers."""

    def test_logger_has_console_handler(self):
        """Test logger has console handler."""
        logger = get_logger("test_console")
        handlers = logger.handlers
        assert len(handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    def test_logger_formatting(self, caplog):
        """Test log message formatting."""
        logger = get_logger("test_format")
        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert "Test message" in caplog.text
        assert "test_format" in caplog.text


class TestSetLogLevel:
    """Test set_log_level function."""

    def test_set_log_level_debug(self):
        """Test changing log level to DEBUG."""
        logger = get_logger("test_set_debug", level="INFO")
        assert logger.level == logging.INFO

        set_log_level(logger, "DEBUG")
        assert logger.level == logging.DEBUG

    def test_set_log_level_error(self):
        """Test changing log level to ERROR."""
        logger = get_logger("test_set_error", level="DEBUG")
        assert logger.level == logging.DEBUG

        set_log_level(logger, "ERROR")
        assert logger.level == logging.ERROR

    def test_set_log_level_updates_handlers(self):
        """Test set_log_level updates handler levels."""
        logger = get_logger("test_set_handlers", level="INFO")

        initial_handler_level = logger.handlers[0].level
        assert initial_handler_level == logging.INFO

        set_log_level(logger, "ERROR")
        assert logger.handlers[0].level == logging.ERROR


class TestLoggerNamespaces:
    """Test logger namespaces."""

    def test_different_logger_names(self):
        """Test different logger names create different loggers."""
        logger1 = get_logger("namespace1")
        logger2 = get_logger("namespace2")

        assert logger1.name == "namespace1"
        assert logger2.name == "namespace2"
        assert logger1 is not logger2

    def test_same_logger_name_returns_same_instance(self):
        """Test same logger name returns same instance."""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")

        assert logger1 is logger2

    def test_logger_name_preserved(self, caplog):
        """Test logger name is preserved in messages."""
        logger = get_logger("test_name")

        with caplog.at_level(logging.ERROR):
            logger.error("Test error")

        # Check that logger name is in the output
        assert "test_name" in caplog.text
        assert "Test error" in caplog.text


class TestLoggingOutput:
    """Test actual logging output."""

    def test_debug_logging(self, caplog):
        """Test debug level logging."""
        logger = get_logger("test_debug_output", level="DEBUG")
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text

    def test_info_logging(self, caplog):
        """Test info level logging."""
        logger = get_logger("test_info_output", level="INFO")
        with caplog.at_level(logging.INFO):
            logger.info("Info message")
            logger.debug("Debug message")

        assert "Info message" in caplog.text
        assert "Debug message" not in caplog.text  # Below INFO level

    def test_error_logging(self, caplog):
        """Test error level logging."""
        logger = get_logger("test_error_output")
        with caplog.at_level(logging.ERROR):
            logger.error("Error message")

        assert "Error message" in caplog.text
