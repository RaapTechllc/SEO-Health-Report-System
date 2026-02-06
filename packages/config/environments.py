"""
Environment definitions for the SEO Health Report System.

Provides an Environment enum and utilities for environment detection.
"""

import os
from enum import Enum


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

    @classmethod
    def from_string(cls, value: str) -> "Environment":
        """
        Convert a string to an Environment enum.

        Args:
            value: String value (case-insensitive)

        Returns:
            Environment enum value

        Raises:
            ValueError: If value doesn't match any environment
        """
        value_lower = value.lower().strip()

        # Handle common aliases
        aliases = {
            "dev": cls.DEVELOPMENT,
            "develop": cls.DEVELOPMENT,
            "local": cls.DEVELOPMENT,
            "stage": cls.STAGING,
            "stg": cls.STAGING,
            "prod": cls.PRODUCTION,
            "prd": cls.PRODUCTION,
            "live": cls.PRODUCTION,
            "testing": cls.TEST,
            "ci": cls.TEST,
        }

        if value_lower in aliases:
            return aliases[value_lower]

        try:
            return cls(value_lower)
        except ValueError:
            valid = [e.value for e in cls] + list(aliases.keys())
            raise ValueError(
                f"Invalid environment '{value}'. "
                f"Valid values: {', '.join(sorted(set(valid)))}"
            )

    @property
    def is_production(self) -> bool:
        """Check if this is a production environment."""
        return self == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if this is a development environment."""
        return self == Environment.DEVELOPMENT

    @property
    def is_test(self) -> bool:
        """Check if this is a test environment."""
        return self == Environment.TEST

    @property
    def is_staging(self) -> bool:
        """Check if this is a staging environment."""
        return self == Environment.STAGING

    @property
    def allows_debug(self) -> bool:
        """Check if debug features are allowed in this environment."""
        return self in (Environment.DEVELOPMENT, Environment.TEST)

    @property
    def requires_https(self) -> bool:
        """Check if HTTPS is required in this environment."""
        return self in (Environment.PRODUCTION, Environment.STAGING)

    @property
    def default_log_level(self) -> str:
        """Get the default log level for this environment."""
        if self == Environment.DEVELOPMENT:
            return "DEBUG"
        elif self == Environment.TEST:
            return "WARNING"
        else:
            return "INFO"


def get_current_environment() -> Environment:
    """
    Detect the current environment from environment variables.

    Checks these variables in order:
    1. APP_ENV
    2. ENVIRONMENT
    3. ENV

    Returns:
        Environment enum value (defaults to DEVELOPMENT)
    """
    env_value = (
        os.environ.get("APP_ENV")
        or os.environ.get("ENVIRONMENT")
        or os.environ.get("ENV")
        or "development"
    )

    try:
        return Environment.from_string(env_value)
    except ValueError:
        # Default to development if unknown
        return Environment.DEVELOPMENT


def is_production() -> bool:
    """Quick check if running in production."""
    return get_current_environment().is_production


def is_development() -> bool:
    """Quick check if running in development."""
    return get_current_environment().is_development


def is_test() -> bool:
    """Quick check if running in test mode."""
    return get_current_environment().is_test


__all__ = [
    "Environment",
    "get_current_environment",
    "is_production",
    "is_development",
    "is_test",
]
