"""
Startup validation for SEO Health Report System.

Provides fail-fast validation to catch configuration issues at startup.
"""

import logging
import sys
from typing import Optional

from .environments import get_current_environment
from .exceptions import (
    FeatureDisabledError,
    ValidationError,
)
from .secrets import Feature, SecretsManager, get_secrets_manager
from .settings import Settings, get_settings

logger = logging.getLogger(__name__)


class StartupValidator:
    """
    Validates configuration at application startup.

    Performs comprehensive checks and provides clear error messages.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        secrets_manager: Optional[SecretsManager] = None,
    ):
        self._settings = settings
        self._secrets_manager = secrets_manager

    @property
    def settings(self) -> Settings:
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def secrets(self) -> SecretsManager:
        if self._secrets_manager is None:
            self._secrets_manager = get_secrets_manager(self.settings)
        return self._secrets_manager

    def validate_all(
        self,
        require_ai: bool = False,
        require_database: bool = False,
        require_payments: bool = False,
        require_auth: bool = False,
        required_features: Optional[set[Feature]] = None,
    ) -> dict:
        """
        Run all validation checks.

        Args:
            require_ai: Require at least one AI system configured
            require_database: Require database configuration
            require_payments: Require Stripe configuration
            require_auth: Require JWT configuration
            required_features: Set of features that must be available

        Returns:
            Dict with validation results

        Raises:
            ValidationError: If critical validation fails
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Environment check
        env = get_current_environment()
        logger.info(f"Validating configuration for environment: {env.value}")

        # Feature validation
        if require_ai:
            ai_systems = self.secrets.get_available_ai_systems()
            if not ai_systems:
                errors.append(
                    "At least one AI system must be configured. "
                    "Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or PERPLEXITY_API_KEY"
                )
            else:
                logger.info(f"Available AI systems: {[s.value for s in ai_systems]}")

        if require_database:
            if not self.secrets.is_configured("database"):
                errors.append("DATABASE_URL is required but not configured")

        if require_payments:
            if not self.secrets.is_configured("stripe_secret"):
                errors.append("STRIPE_SECRET_KEY is required for payments")
            if not self.secrets.is_configured("stripe_webhook"):
                warnings.append("STRIPE_WEBHOOK_SECRET not configured - webhooks disabled")

        if require_auth:
            if not self.secrets.is_configured("jwt_secret"):
                if env.is_production:
                    errors.append("JWT_SECRET_KEY is required in production")
                else:
                    warnings.append(
                        "JWT_SECRET_KEY not configured - using insecure default"
                    )

        # Check required features
        if required_features:
            for feature in required_features:
                try:
                    self.secrets.validate_for_feature(feature, raise_error=True)
                except FeatureDisabledError as e:
                    errors.append(str(e))

        # Production-specific checks
        if env.is_production:
            prod_warnings = self._validate_production()
            warnings.extend(prod_warnings)

        # Configuration warnings (non-blocking)
        config_warnings = self._get_configuration_warnings()
        warnings.extend(config_warnings)

        if errors:
            raise ValidationError(errors, warnings)

        if warnings:
            for warning in warnings:
                logger.warning(f"Configuration warning: {warning}")

        return {
            "status": "valid",
            "environment": env.value,
            "errors": errors,
            "warnings": warnings,
            "available_features": [f.value for f in self.secrets.get_available_features()],
        }

    def _validate_production(self) -> list[str]:
        """
        Perform production-specific validation.

        Returns:
            List of warning messages
        """
        warnings = []

        # Check for development-only settings in production
        settings = self.settings

        if settings.log_level == "DEBUG":
            warnings.append("DEBUG log level in production may expose sensitive data")

        if not settings.base_url:
            warnings.append("BASE_URL not set - callbacks may not work correctly")

        # Check for weak JWT configuration
        if settings.jwt_secret_key and len(settings.jwt_secret_key) < 32:
            warnings.append("JWT_SECRET_KEY should be at least 32 characters")

        return warnings

    def _get_configuration_warnings(self) -> list[str]:
        """
        Get general configuration warnings.

        Returns:
            List of warning messages
        """
        warnings = []
        settings = self.settings

        # Check AI configuration
        if not self.secrets.is_configured("anthropic"):
            warnings.append(
                "ANTHROPIC_API_KEY not configured - AI visibility audit will be limited"
            )

        # Check Google services
        if not any([
            self.secrets.is_configured("google"),
            self.secrets.is_configured("pagespeed"),
        ]):
            warnings.append(
                "No Google API key configured - PageSpeed insights unavailable"
            )

        # Check cache configuration
        if settings.cache_ttl_ai_response == 0:
            warnings.append("AI response caching disabled - may increase API costs")

        return warnings


def validate_startup(
    require_ai: bool = False,
    require_database: bool = False,
    require_payments: bool = False,
    require_auth: bool = False,
    required_features: Optional[set[Feature]] = None,
    exit_on_error: bool = True,
) -> dict:
    """
    Validate configuration at startup.

    This is the main entry point for startup validation.
    Call this early in your application startup.

    Args:
        require_ai: Require at least one AI system configured
        require_database: Require database configuration
        require_payments: Require Stripe configuration
        require_auth: Require JWT configuration
        required_features: Set of features that must be available
        exit_on_error: If True, exits the process on validation failure

    Returns:
        Dict with validation results

    Raises:
        ValidationError: If validation fails and exit_on_error=False

    Example:
        >>> from packages.config import validate_startup
        >>> validate_startup(require_database=True)
        {'status': 'valid', 'environment': 'development', ...}
    """
    validator = StartupValidator()

    try:
        result = validator.validate_all(
            require_ai=require_ai,
            require_database=require_database,
            require_payments=require_payments,
            require_auth=require_auth,
            required_features=required_features,
        )
        logger.info(f"Configuration validated successfully for {result['environment']}")
        return result

    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        if exit_on_error:
            print(f"\n{'='*60}", file=sys.stderr)
            print("CONFIGURATION ERROR - Application cannot start", file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)
            print(str(e), file=sys.stderr)
            print(f"\n{'='*60}\n", file=sys.stderr)
            sys.exit(1)
        raise


def quick_check() -> bool:
    """
    Quick check if basic configuration is valid.

    Does not raise exceptions, just returns True/False.

    Returns:
        True if basic configuration is valid
    """
    try:
        get_settings()
        return True
    except Exception as e:
        logger.error(f"Configuration check failed: {e}")
        return False


__all__ = [
    "StartupValidator",
    "validate_startup",
    "quick_check",
]
