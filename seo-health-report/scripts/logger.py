"""
Logger Configuration

Centralized logging configuration for SEO Health Report system.
Provides structured logging with file rotation and configurable levels.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def get_logger(
    name: str = "seo_health_report",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (default: "seo_health_report")
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Falls back to SEO_HEALTH_LOG_LEVEL env var, then INFO
        log_file: Log file path (default: logs/seo-health-report.log)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_level = _get_log_level(level)

    logger.setLevel(log_level)

    console_handler = _get_console_handler(log_level)
    logger.addHandler(console_handler)

    if log_file is None:
        log_file = _get_default_log_file()

    try:
        file_handler = _get_file_handler(log_file, log_level)
        logger.addHandler(file_handler)
    except (OSError, IOError) as e:
        logger.warning(f"Could not create log file handler: {e}")

    return logger


def _get_log_level(level: Optional[str]) -> int:
    """
    Get logging level from parameter, environment, or default.

    Args:
        level: Log level string or None

    Returns:
        Logging level constant
    """
    if level is None:
        level = os.environ.get("SEO_HEALTH_LOG_LEVEL", "INFO")

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    return level_map.get(level.upper(), logging.INFO)


def _get_default_log_file() -> str:
    """
    Get default log file path.

    Returns:
        Log file path
    """
    log_dir = os.environ.get("SEO_HEALTH_LOG_DIR", "logs")
    log_file = os.environ.get("SEO_HEALTH_LOG_FILE", "seo-health-report.log")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, log_file)


def _get_console_handler(level: int) -> logging.StreamHandler:
    """
    Create and configure console handler.

    Args:
        level: Logging level

    Returns:
        Configured console handler
    """
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


def _get_file_handler(log_file: str, level: int) -> RotatingFileHandler:
    """
    Create and configure file handler with rotation.

    Args:
        log_file: Path to log file
        level: Logging level

    Returns:
        Configured file handler with rotation
    """
    handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


def set_log_level(logger: logging.Logger, level: str) -> None:
    """
    Change log level for a logger.

    Args:
        logger: Logger instance
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    new_level = level_map.get(level.upper(), logging.INFO)
    logger.setLevel(new_level)

    for handler in logger.handlers:
        handler.setLevel(new_level)


__all__ = ["get_logger", "set_log_level"]
