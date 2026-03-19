"""
Custom exceptions for configuration management.

These exceptions provide clear, actionable error messages for configuration issues.
"""

from typing import Optional


class ConfigurationError(Exception):
    """Base exception for all configuration-related errors."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        msg = f"Configuration Error: {self.message}"
        if self.suggestion:
            msg += f"\n  Suggestion: {self.suggestion}"
        return msg


class MissingSecretError(ConfigurationError):
    """Raised when a required secret/API key is not configured."""

    def __init__(
        self,
        secret_name: str,
        feature: Optional[str] = None,
        alternatives: Optional[list[str]] = None,
    ):
        self.secret_name = secret_name
        self.feature = feature
        self.alternatives = alternatives or []

        message = f"Missing required secret: {secret_name}"
        if feature:
            message += f" (required for {feature})"

        suggestion = f"Set the {secret_name} environment variable"
        if self.alternatives:
            suggestion += f" or one of: {', '.join(self.alternatives)}"

        super().__init__(message, suggestion)


class InvalidConfigurationError(ConfigurationError):
    """Raised when a configuration value is invalid."""

    def __init__(
        self,
        field: str,
        value: str,
        expected: str,
        suggestion: Optional[str] = None,
    ):
        self.field = field
        self.value = value
        self.expected = expected

        message = f"Invalid value for {field}: '{value}' (expected: {expected})"
        super().__init__(message, suggestion)


class EnvironmentMismatchError(ConfigurationError):
    """Raised when configuration doesn't match the expected environment."""

    def __init__(self, environment: str, issue: str):
        self.environment = environment
        self.issue = issue

        message = f"Environment mismatch in {environment}: {issue}"
        suggestion = "Ensure environment variables are set correctly for this environment"
        super().__init__(message, suggestion)


class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""

    def __init__(self, errors: list[str], warnings: Optional[list[str]] = None):
        self.errors = errors
        self.warnings = warnings or []

        message = f"Configuration validation failed with {len(errors)} error(s)"
        if self.warnings:
            message += f" and {len(self.warnings)} warning(s)"

        error_list = "\n  - ".join([""] + errors)
        suggestion = f"Fix the following errors:{error_list}"

        super().__init__(message, suggestion)


class FeatureDisabledError(ConfigurationError):
    """Raised when attempting to use a feature that's not configured."""

    def __init__(self, feature: str, required_secrets: list[str]):
        self.feature = feature
        self.required_secrets = required_secrets

        message = f"Feature '{feature}' is disabled due to missing configuration"
        suggestion = f"Configure the following: {', '.join(required_secrets)}"
        super().__init__(message, suggestion)


__all__ = [
    "ConfigurationError",
    "MissingSecretError",
    "InvalidConfigurationError",
    "EnvironmentMismatchError",
    "ValidationError",
    "FeatureDisabledError",
]
