"""
Secrets management for SEO Health Report System.

Provides centralized access to API keys with fallback chains and validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .exceptions import FeatureDisabledError, MissingSecretError
from .settings import Settings, get_settings


class AISystem(str, Enum):
    """Supported AI systems for querying."""

    CLAUDE = "claude"
    OPENAI = "openai"
    PERPLEXITY = "perplexity"
    GEMINI = "gemini"
    GROK = "grok"


class Feature(str, Enum):
    """Features that require specific secrets."""

    AI_VISIBILITY = "ai_visibility"
    PAGESPEED = "pagespeed"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    IMAGE_GENERATION = "image_generation"
    PAYMENTS = "payments"
    AUTHENTICATION = "authentication"
    DATABASE = "database"


@dataclass
class SecretDefinition:
    """Definition of a secret with its properties."""

    name: str
    env_var: str
    description: str
    required_for: list[Feature] = field(default_factory=list)
    fallback_vars: list[str] = field(default_factory=list)
    is_sensitive: bool = True


# Registry of all secrets with their definitions
SECRET_REGISTRY: dict[str, SecretDefinition] = {
    "anthropic": SecretDefinition(
        name="Anthropic API Key",
        env_var="ANTHROPIC_API_KEY",
        description="API key for Claude AI",
        required_for=[Feature.AI_VISIBILITY],
    ),
    "openai": SecretDefinition(
        name="OpenAI API Key",
        env_var="OPENAI_API_KEY",
        description="API key for ChatGPT",
        required_for=[Feature.AI_VISIBILITY],
    ),
    "perplexity": SecretDefinition(
        name="Perplexity API Key",
        env_var="PERPLEXITY_API_KEY",
        description="API key for Perplexity AI",
        required_for=[Feature.AI_VISIBILITY],
    ),
    "xai": SecretDefinition(
        name="xAI API Key",
        env_var="XAI_API_KEY",
        description="API key for Grok",
        required_for=[Feature.AI_VISIBILITY],
    ),
    "google": SecretDefinition(
        name="Google API Key",
        env_var="GOOGLE_API_KEY",
        description="Google API key (fallback for Google services)",
        required_for=[Feature.PAGESPEED, Feature.KNOWLEDGE_GRAPH],
    ),
    "google_gemini": SecretDefinition(
        name="Google Gemini API Key",
        env_var="GOOGLE_GEMINI_API_KEY",
        description="Google Gemini API key for image generation",
        required_for=[Feature.IMAGE_GENERATION, Feature.AI_VISIBILITY],
        fallback_vars=["GOOGLE_API_KEY"],
    ),
    "google_kg": SecretDefinition(
        name="Google Knowledge Graph API Key",
        env_var="GOOGLE_KG_API_KEY",
        description="Google Knowledge Graph API key",
        required_for=[Feature.KNOWLEDGE_GRAPH],
        fallback_vars=["GOOGLE_API_KEY"],
    ),
    "pagespeed": SecretDefinition(
        name="PageSpeed API Key",
        env_var="PAGESPEED_API_KEY",
        description="Google PageSpeed Insights API key",
        required_for=[Feature.PAGESPEED],
        fallback_vars=["GOOGLE_API_KEY"],
    ),
    "stripe_secret": SecretDefinition(
        name="Stripe Secret Key",
        env_var="STRIPE_SECRET_KEY",
        description="Stripe secret key for payments",
        required_for=[Feature.PAYMENTS],
    ),
    "stripe_webhook": SecretDefinition(
        name="Stripe Webhook Secret",
        env_var="STRIPE_WEBHOOK_SECRET",
        description="Stripe webhook signing secret",
        required_for=[Feature.PAYMENTS],
    ),
    "jwt_secret": SecretDefinition(
        name="JWT Secret Key",
        env_var="JWT_SECRET_KEY",
        description="Secret key for JWT token signing",
        required_for=[Feature.AUTHENTICATION],
    ),
    "database": SecretDefinition(
        name="Database URL",
        env_var="DATABASE_URL",
        description="Database connection URL",
        required_for=[Feature.DATABASE],
        is_sensitive=True,
    ),
}


class SecretsManager:
    """
    Manages secrets and API keys with validation and fallback support.

    Provides a centralized way to access and validate secrets,
    check feature availability, and get status reports.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize SecretsManager.

        Args:
            settings: Optional Settings instance. If not provided,
                     uses the global singleton.
        """
        self._settings = settings or get_settings()

    @property
    def settings(self) -> Settings:
        """Get the Settings instance."""
        return self._settings

    def get_secret(self, name: str) -> Optional[str]:
        """
        Get a secret value by name.

        Args:
            name: Secret name from the registry

        Returns:
            Secret value or None if not configured
        """
        definition = SECRET_REGISTRY.get(name)
        if not definition:
            return None

        # Map secret names to settings attributes
        attr_map = {
            "anthropic": "anthropic_api_key",
            "openai": "openai_api_key",
            "perplexity": "perplexity_api_key",
            "xai": "xai_api_key",
            "google": "google_api_key",
            "google_gemini": "effective_gemini_api_key",
            "google_kg": "effective_kg_api_key",
            "pagespeed": "effective_pagespeed_api_key",
            "stripe_secret": "stripe_secret_key",
            "stripe_webhook": "stripe_webhook_secret",
            "jwt_secret": "jwt_secret_key",
            "database": "database_url",
        }

        attr = attr_map.get(name)
        if attr:
            return getattr(self._settings, attr, None)
        return None

    def require_secret(self, name: str, feature: Optional[str] = None) -> str:
        """
        Get a secret value, raising an error if not configured.

        Args:
            name: Secret name from the registry
            feature: Optional feature name for error message

        Returns:
            Secret value

        Raises:
            MissingSecretError: If secret is not configured
        """
        value = self.get_secret(name)
        if not value:
            definition = SECRET_REGISTRY.get(name)
            raise MissingSecretError(
                secret_name=definition.env_var if definition else name,
                feature=feature,
                alternatives=definition.fallback_vars if definition else None,
            )
        return value

    def is_configured(self, name: str) -> bool:
        """
        Check if a secret is configured.

        Args:
            name: Secret name from the registry

        Returns:
            True if secret has a value
        """
        return bool(self.get_secret(name))

    def validate_for_feature(self, feature: Feature, raise_error: bool = True) -> bool:
        """
        Validate that required secrets are configured for a feature.

        Args:
            feature: Feature to validate
            raise_error: If True, raises FeatureDisabledError on failure

        Returns:
            True if all required secrets are configured

        Raises:
            FeatureDisabledError: If required secrets are missing and raise_error=True
        """
        missing = []

        for name, definition in SECRET_REGISTRY.items():
            if feature in definition.required_for:
                if not self.is_configured(name):
                    # Check if any fallback is configured
                    has_fallback = any(
                        self.get_secret(fb.lower().replace("_api_key", "").replace("_", "_"))
                        for fb in definition.fallback_vars
                    )
                    if not has_fallback:
                        missing.append(definition.env_var)

        if missing and raise_error:
            raise FeatureDisabledError(feature.value, missing)

        return len(missing) == 0

    def get_available_ai_systems(self) -> list[AISystem]:
        """
        Get list of AI systems that are configured.

        Returns:
            List of available AI systems
        """
        available = []

        if self.is_configured("anthropic"):
            available.append(AISystem.CLAUDE)
        if self.is_configured("openai"):
            available.append(AISystem.OPENAI)
        if self.is_configured("perplexity"):
            available.append(AISystem.PERPLEXITY)
        if self.is_configured("google_gemini") or self.is_configured("google"):
            available.append(AISystem.GEMINI)
        if self.is_configured("xai"):
            available.append(AISystem.GROK)

        return available

    def get_available_features(self) -> set[Feature]:
        """
        Get set of features that are fully configured.

        Returns:
            Set of available features
        """
        available = set()

        for feature in Feature:
            try:
                if self.validate_for_feature(feature, raise_error=False):
                    available.add(feature)
            except Exception:
                pass

        return available

    def get_status_report(self, include_values: bool = False) -> dict[str, dict]:
        """
        Get a status report of all secrets.

        Args:
            include_values: If True, includes masked values (first 4 chars + ***)

        Returns:
            Dict with secret status information
        """
        report = {}

        for name, definition in SECRET_REGISTRY.items():
            value = self.get_secret(name)
            is_configured = bool(value)

            status = {
                "name": definition.name,
                "env_var": definition.env_var,
                "configured": is_configured,
                "required_for": [f.value for f in definition.required_for],
                "has_fallback": len(definition.fallback_vars) > 0,
            }

            if include_values and value:
                # Mask the value for safety
                if len(value) > 8:
                    status["value_preview"] = value[:4] + "***" + value[-4:]
                else:
                    status["value_preview"] = "***"

            report[name] = status

        return report

    def get_summary(self) -> dict[str, any]:
        """
        Get a summary of secrets configuration.

        Returns:
            Dict with configuration summary
        """
        configured_count = sum(1 for name in SECRET_REGISTRY if self.is_configured(name))
        total_count = len(SECRET_REGISTRY)
        ai_systems = self.get_available_ai_systems()
        available_features = self.get_available_features()

        return {
            "configured_secrets": configured_count,
            "total_secrets": total_count,
            "configuration_percent": round(configured_count / total_count * 100, 1),
            "available_ai_systems": [s.value for s in ai_systems],
            "available_features": [f.value for f in available_features],
            "missing_for_full_functionality": [
                name
                for name, defn in SECRET_REGISTRY.items()
                if not self.is_configured(name) and defn.required_for
            ],
        }


# Module-level convenience function
def get_secrets_manager(settings: Optional[Settings] = None) -> SecretsManager:
    """
    Get a SecretsManager instance.

    Args:
        settings: Optional Settings instance

    Returns:
        SecretsManager instance
    """
    return SecretsManager(settings)


__all__ = [
    "AISystem",
    "Feature",
    "SecretDefinition",
    "SECRET_REGISTRY",
    "SecretsManager",
    "get_secrets_manager",
]
