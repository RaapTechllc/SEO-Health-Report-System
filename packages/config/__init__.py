"""
Centralized configuration package for the SEO Health Report System.

This package provides type-safe, validated configuration management using
Pydantic Settings with fail-fast startup validation.

Quick Start:
    >>> from packages.config import get_settings, validate_startup
    >>>
    >>> # Validate configuration at startup
    >>> validate_startup(require_database=True)
    >>>
    >>> # Access settings throughout your application
    >>> settings = get_settings()
    >>> print(settings.api_timeout)

Features:
    - Type-safe configuration with Pydantic v2
    - Environment variable support with fallback chains
    - Startup validation with clear error messages
    - Secrets management with feature-based validation
    - Multi-tenant configuration support
    - Custom exceptions for configuration errors

Environment Variables:
    See .env.example for a complete list of supported variables.
    Most SEO-specific settings use the SEO_HEALTH_ prefix.
"""

from .environments import (
    Environment,
    get_current_environment,
    is_development,
    is_production,
    is_test,
)
from .exceptions import (
    ConfigurationError,
    EnvironmentMismatchError,
    FeatureDisabledError,
    InvalidConfigurationError,
    MissingSecretError,
    ValidationError,
)
from .rbac import (
    ROLE_PERMISSIONS,
    Permission,
    Role,
    get_user_permissions,
    has_permission,
    require_permission,
)
from .secrets import (
    SECRET_REGISTRY,
    AISystem,
    Feature,
    SecretDefinition,
    SecretsManager,
    get_secrets_manager,
)
from .settings import (
    Settings,
    get_settings,
    reload_settings,
)
from .tenant import (
    TenantConfig,
    TenantRegistry,
    get_tenant_config,
    get_tenant_registry,
)
from .validators import (
    StartupValidator,
    quick_check,
    validate_startup,
)

# Package version
__version__ = "1.0.0"


# Public API
__all__ = [
    # Version
    "__version__",
    # Settings
    "Settings",
    "get_settings",
    "reload_settings",
    # Environments
    "Environment",
    "get_current_environment",
    "is_production",
    "is_development",
    "is_test",
    # Secrets
    "AISystem",
    "Feature",
    "SecretDefinition",
    "SECRET_REGISTRY",
    "SecretsManager",
    "get_secrets_manager",
    # Validators
    "StartupValidator",
    "validate_startup",
    "quick_check",
    # Tenant
    "TenantConfig",
    "TenantRegistry",
    "get_tenant_registry",
    "get_tenant_config",
    # Exceptions
    "ConfigurationError",
    "MissingSecretError",
    "InvalidConfigurationError",
    "EnvironmentMismatchError",
    "ValidationError",
    "FeatureDisabledError",
    # RBAC
    "Role",
    "Permission",
    "ROLE_PERMISSIONS",
    "has_permission",
    "require_permission",
    "get_user_permissions",
]
