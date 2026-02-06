"""
Centralized tier configuration for the SEO Health Report System.

All tier-specific settings (pricing, rate limits, feature limits) are defined here.
Supports env var overrides for each tier setting.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TierDefinition:
    """Complete definition of a service tier."""
    name: str
    display_name: str
    # Pricing (in cents)
    price_cents: int
    stripe_price_id: Optional[str] = None
    # Rate limits
    requests_per_minute: int = 100
    audits_per_day: int = 5
    concurrent_audits: int = 1
    # Feature limits
    max_ai_queries: int = 5
    max_pages_per_audit: int = 50
    max_keywords: int = 5
    max_competitors: int = 0
    # Feature flags
    custom_branding: bool = False
    competitive_analysis: bool = False
    pdf_report: bool = False


def _env_int(key: str, default: int) -> int:
    """Get integer from env var with fallback."""
    return int(os.getenv(key, str(default)))


def _env_str(key: str, default: str = "") -> str:
    """Get string from env var with fallback."""
    return os.getenv(key, default)


DEFAULT_TIERS: dict[str, TierDefinition] = {
    "basic": TierDefinition(
        name="basic",
        display_name="Basic SEO Audit",
        price_cents=_env_int("TIER_BASIC_PRICE_CENTS", 80000),
        stripe_price_id=_env_str("TIER_BASIC_STRIPE_PRICE_ID"),
        requests_per_minute=_env_int("TIER_BASIC_RPM", 100),
        audits_per_day=_env_int("TIER_BASIC_AUDITS_PER_DAY", 5),
        concurrent_audits=_env_int("TIER_BASIC_CONCURRENT", 1),
        max_ai_queries=_env_int("TIER_BASIC_AI_QUERIES", 5),
        max_pages_per_audit=_env_int("TIER_BASIC_MAX_PAGES", 50),
        max_keywords=5,
        max_competitors=0,
        custom_branding=False,
        competitive_analysis=False,
        pdf_report=False,
    ),
    "pro": TierDefinition(
        name="pro",
        display_name="Pro SEO Audit",
        price_cents=_env_int("TIER_PRO_PRICE_CENTS", 250000),
        stripe_price_id=_env_str("TIER_PRO_STRIPE_PRICE_ID"),
        requests_per_minute=_env_int("TIER_PRO_RPM", 500),
        audits_per_day=_env_int("TIER_PRO_AUDITS_PER_DAY", 25),
        concurrent_audits=_env_int("TIER_PRO_CONCURRENT", 3),
        max_ai_queries=_env_int("TIER_PRO_AI_QUERIES", 15),
        max_pages_per_audit=_env_int("TIER_PRO_MAX_PAGES", 200),
        max_keywords=20,
        max_competitors=5,
        custom_branding=False,
        competitive_analysis=True,
        pdf_report=True,
    ),
    "enterprise": TierDefinition(
        name="enterprise",
        display_name="Enterprise SEO Audit",
        price_cents=_env_int("TIER_ENTERPRISE_PRICE_CENTS", 600000),
        stripe_price_id=_env_str("TIER_ENTERPRISE_STRIPE_PRICE_ID"),
        requests_per_minute=_env_int("TIER_ENTERPRISE_RPM", 2000),
        audits_per_day=_env_int("TIER_ENTERPRISE_AUDITS_PER_DAY", 100),
        concurrent_audits=_env_int("TIER_ENTERPRISE_CONCURRENT", 10),
        max_ai_queries=_env_int("TIER_ENTERPRISE_AI_QUERIES", 30),
        max_pages_per_audit=_env_int("TIER_ENTERPRISE_MAX_PAGES", 1000),
        max_keywords=50,
        max_competitors=10,
        custom_branding=True,
        competitive_analysis=True,
        pdf_report=True,
    ),
}


def get_tier(name: str) -> TierDefinition:
    """
    Get tier definition by name.

    Falls back to basic tier if name is not found.
    """
    # Normalize name
    name_map = {
        "low": "basic",
        "medium": "pro",
        "high": "enterprise",
        "budget": "basic",
        "balanced": "pro",
        "premium": "enterprise",
    }
    normalized = name_map.get(name.lower(), name.lower())
    return DEFAULT_TIERS.get(normalized, DEFAULT_TIERS["basic"])


def get_all_tiers() -> dict[str, TierDefinition]:
    """Get all tier definitions."""
    return DEFAULT_TIERS.copy()


__all__ = ["TierDefinition", "DEFAULT_TIERS", "get_tier", "get_all_tiers"]
