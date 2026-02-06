"""
Multi-tenant configuration support.

Provides per-tenant configuration overrides for the SEO Health Report System.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from .settings import Settings, get_settings


@dataclass
class TenantConfig:
    """
    Per-tenant configuration overrides.

    Allows customization of settings on a per-tenant basis
    while inheriting defaults from the base Settings.
    """

    # Tenant identification
    tenant_id: str
    tenant_name: str

    # Brand customization
    brand_colors: dict[str, str] = field(default_factory=dict)
    logo_url: Optional[str] = None
    company_name: Optional[str] = None

    # Scoring customization
    custom_weights: Optional[dict[str, float]] = None
    custom_thresholds: Optional[dict[str, int]] = None

    # Feature flags
    features_enabled: list[str] = field(default_factory=lambda: [
        "technical_audit",
        "content_audit",
        "ai_visibility",
    ])

    # API limits
    max_audits_per_day: int = 10
    max_pages_per_audit: int = 100
    max_competitors: int = 5

    # Output customization
    report_template: Optional[str] = None
    include_branding: bool = True

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_effective_settings(self, base_settings: Optional[Settings] = None) -> dict[str, Any]:
        """
        Get effective settings with tenant overrides applied.

        Args:
            base_settings: Base Settings instance to override

        Returns:
            Dict with effective settings values
        """
        settings = base_settings or get_settings()

        # Start with base settings
        effective = {
            "api_timeout": settings.api_timeout,
            "cache_ttl_pagespeed": settings.cache_ttl_pagespeed,
            "cache_ttl_ai_response": settings.cache_ttl_ai_response,
            "crawl_max_depth": min(settings.crawl_max_depth, self.max_pages_per_audit),
            "output_format": settings.output_format,
        }

        # Apply custom weights if provided
        if self.custom_weights:
            if "technical" in self.custom_weights:
                effective["score_weight_technical"] = self.custom_weights["technical"]
            if "content" in self.custom_weights:
                effective["score_weight_content"] = self.custom_weights["content"]
            if "ai" in self.custom_weights:
                effective["score_weight_ai"] = self.custom_weights["ai"]
        else:
            effective["score_weight_technical"] = settings.score_weight_technical
            effective["score_weight_content"] = settings.score_weight_content
            effective["score_weight_ai"] = settings.score_weight_ai

        # Apply custom thresholds if provided
        if self.custom_thresholds:
            effective["grade_a_threshold"] = self.custom_thresholds.get(
                "A", settings.grade_a_threshold
            )
            effective["grade_b_threshold"] = self.custom_thresholds.get(
                "B", settings.grade_b_threshold
            )
            effective["grade_c_threshold"] = self.custom_thresholds.get(
                "C", settings.grade_c_threshold
            )
            effective["grade_d_threshold"] = self.custom_thresholds.get(
                "D", settings.grade_d_threshold
            )
        else:
            effective["grade_a_threshold"] = settings.grade_a_threshold
            effective["grade_b_threshold"] = settings.grade_b_threshold
            effective["grade_c_threshold"] = settings.grade_c_threshold
            effective["grade_d_threshold"] = settings.grade_d_threshold

        return effective

    def get_brand_colors(self, base_settings: Optional[Settings] = None) -> dict[str, str]:
        """
        Get brand colors with tenant overrides.

        Args:
            base_settings: Base Settings instance

        Returns:
            Dict of color names to hex values
        """
        settings = base_settings or get_settings()

        # Start with default colors
        colors = dict(settings.default_colors)

        # Apply tenant overrides
        colors.update(self.brand_colors)

        return colors

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled for this tenant.

        Args:
            feature: Feature name to check

        Returns:
            True if feature is enabled
        """
        return feature in self.features_enabled

    def can_run_audit(self, audits_today: int) -> bool:
        """
        Check if tenant can run another audit today.

        Args:
            audits_today: Number of audits already run today

        Returns:
            True if audit limit not exceeded
        """
        return audits_today < self.max_audits_per_day

    def to_dict(self) -> dict[str, Any]:
        """
        Convert tenant config to dictionary.

        Returns:
            Dict representation
        """
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "brand_colors": self.brand_colors,
            "logo_url": self.logo_url,
            "company_name": self.company_name,
            "custom_weights": self.custom_weights,
            "custom_thresholds": self.custom_thresholds,
            "features_enabled": self.features_enabled,
            "max_audits_per_day": self.max_audits_per_day,
            "max_pages_per_audit": self.max_pages_per_audit,
            "max_competitors": self.max_competitors,
            "report_template": self.report_template,
            "include_branding": self.include_branding,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenantConfig":
        """
        Create TenantConfig from dictionary.

        Args:
            data: Dict with tenant configuration

        Returns:
            TenantConfig instance
        """
        return cls(
            tenant_id=data["tenant_id"],
            tenant_name=data["tenant_name"],
            brand_colors=data.get("brand_colors", {}),
            logo_url=data.get("logo_url"),
            company_name=data.get("company_name"),
            custom_weights=data.get("custom_weights"),
            custom_thresholds=data.get("custom_thresholds"),
            features_enabled=data.get("features_enabled", [
                "technical_audit",
                "content_audit",
                "ai_visibility",
            ]),
            max_audits_per_day=data.get("max_audits_per_day", 10),
            max_pages_per_audit=data.get("max_pages_per_audit", 100),
            max_competitors=data.get("max_competitors", 5),
            report_template=data.get("report_template"),
            include_branding=data.get("include_branding", True),
            metadata=data.get("metadata", {}),
        )


class TenantRegistry:
    """
    Registry for managing tenant configurations.

    Provides lookup and caching of tenant configs.
    """

    def __init__(self):
        self._tenants: dict[str, TenantConfig] = {}
        self._default_tenant: Optional[TenantConfig] = None

    def register(self, tenant: TenantConfig) -> None:
        """
        Register a tenant configuration.

        Args:
            tenant: TenantConfig to register
        """
        self._tenants[tenant.tenant_id] = tenant

    def get(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        Get tenant configuration by ID.

        Args:
            tenant_id: Tenant ID to look up

        Returns:
            TenantConfig or None if not found
        """
        return self._tenants.get(tenant_id)

    def get_or_default(self, tenant_id: Optional[str] = None) -> TenantConfig:
        """
        Get tenant config or return default.

        Args:
            tenant_id: Optional tenant ID

        Returns:
            TenantConfig (tenant-specific or default)
        """
        if tenant_id and tenant_id in self._tenants:
            return self._tenants[tenant_id]

        if self._default_tenant is None:
            self._default_tenant = TenantConfig(
                tenant_id="default",
                tenant_name="Default Tenant",
            )

        return self._default_tenant

    def set_default(self, tenant: TenantConfig) -> None:
        """
        Set the default tenant configuration.

        Args:
            tenant: TenantConfig to use as default
        """
        self._default_tenant = tenant

    def list_tenants(self) -> list[str]:
        """
        List all registered tenant IDs.

        Returns:
            List of tenant IDs
        """
        return list(self._tenants.keys())

    def remove(self, tenant_id: str) -> bool:
        """
        Remove a tenant from the registry.

        Args:
            tenant_id: Tenant ID to remove

        Returns:
            True if tenant was removed
        """
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            return True
        return False


# Global tenant registry instance
_tenant_registry: Optional[TenantRegistry] = None


def get_tenant_registry() -> TenantRegistry:
    """
    Get the global tenant registry.

    Returns:
        TenantRegistry instance
    """
    global _tenant_registry
    if _tenant_registry is None:
        _tenant_registry = TenantRegistry()
    return _tenant_registry


def get_tenant_config(tenant_id: Optional[str] = None) -> TenantConfig:
    """
    Get tenant configuration.

    Args:
        tenant_id: Optional tenant ID

    Returns:
        TenantConfig for the tenant or default
    """
    return get_tenant_registry().get_or_default(tenant_id)


__all__ = [
    "TenantConfig",
    "TenantRegistry",
    "get_tenant_registry",
    "get_tenant_config",
]
