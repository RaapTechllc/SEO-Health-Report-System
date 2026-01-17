"""
Business Type Profiles for SEO Health Report

Industry-specific scoring weights and blocker configurations.
For mechanical trades, phone placement matters more than backlinks.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class BlockerConfig:
    """Configuration for a scoring blocker."""
    id: str
    description: str
    max_score: int  # Maximum score allowed when blocker is active
    category: str  # Which audit category triggers this
    check_field: str  # Field to check in audit results
    threshold: Optional[Any] = None  # Threshold value for comparison
    comparison: str = "less_than"  # less_than, greater_than, equals, missing


@dataclass
class BusinessProfile:
    """Business type profile with industry-specific configuration."""
    name: str
    display_name: str
    description: str
    weights: Dict[str, float]
    blockers: List[BlockerConfig]
    benchmarks: Dict[str, float] = field(default_factory=dict)
    quick_win_templates: Dict[str, str] = field(default_factory=dict)


# Blocker definitions for mechanical trades
MECHANICAL_TRADES_BLOCKERS = [
    BlockerConfig(
        id="server_response_3s",
        description="Server response time exceeds 3 seconds",
        max_score=50,
        category="technical",
        check_field="server_response_time",
        threshold=3000,  # milliseconds
        comparison="greater_than"
    ),
    BlockerConfig(
        id="mobile_usability_under_90",
        description="Mobile usability score below 90",
        max_score=50,
        category="technical",
        check_field="mobile_usability_score",
        threshold=90,
        comparison="less_than"
    ),
    BlockerConfig(
        id="core_web_vitals_fail",
        description="Core Web Vitals assessment failed",
        max_score=60,
        category="technical",
        check_field="core_web_vitals_passed",
        threshold=False,
        comparison="equals"
    ),
    BlockerConfig(
        id="no_ssl",
        description="Site does not have SSL/HTTPS",
        max_score=40,
        category="technical",
        check_field="has_ssl",
        threshold=False,
        comparison="equals"
    ),
    BlockerConfig(
        id="gbp_not_claimed",
        description="Google Business Profile not claimed or verified",
        max_score=55,
        category="local_gbp",
        check_field="gbp_claimed",
        threshold=False,
        comparison="equals"
    ),
    BlockerConfig(
        id="phone_not_clickable_mobile",
        description="Phone number not click-to-call on mobile",
        max_score=65,
        category="lead_funnel",
        check_field="phone_click_to_call",
        threshold=False,
        comparison="equals"
    ),
    BlockerConfig(
        id="phone_not_visible",
        description="Phone number not visible above fold on mobile",
        max_score=70,
        category="lead_funnel",
        check_field="phone_above_fold_mobile",
        threshold=False,
        comparison="equals"
    ),
]

# Generic blockers (apply to all business types)
GENERIC_BLOCKERS = [
    BlockerConfig(
        id="server_response_5s",
        description="Server response time exceeds 5 seconds",
        max_score=50,
        category="technical",
        check_field="server_response_time",
        threshold=5000,
        comparison="greater_than"
    ),
    BlockerConfig(
        id="no_ssl",
        description="Site does not have SSL/HTTPS",
        max_score=40,
        category="technical",
        check_field="has_ssl",
        threshold=False,
        comparison="equals"
    ),
]


# Business profile definitions
BUSINESS_PROFILES: Dict[str, BusinessProfile] = {
    "mechanical_trades": BusinessProfile(
        name="mechanical_trades",
        display_name="Mechanical Trades & Construction",
        description="HVAC, sheet metal, plumbing, electrical contractors. Local intent is critical.",
        weights={
            "local_gbp": 0.30,        # 60-70% of trade searches have local intent
            "content_eeat": 0.25,     # Project photos, licensing, trust signals
            "technical": 0.20,        # Mobile + Core Web Vitals matter
            "lead_funnel": 0.15,      # Buried phone = lost revenue
            "authority": 0.10,        # Backlinks are secondary for local
        },
        blockers=MECHANICAL_TRADES_BLOCKERS,
        benchmarks={
            "local_gbp": 75,
            "content_eeat": 70,
            "technical": 80,
            "lead_funnel": 75,
            "authority": 50,
            "overall": 70,
        },
        quick_win_templates={
            "phone_not_clickable": (
                "You're likely losing 15-25% of potential calls because your "
                "phone number isn't click-to-call on mobile."
            ),
            "license_not_displayed": (
                "Your competitor shows their license number above the fold. You don't."
            ),
            "gbp_photos_stale": (
                "Your Google Business Profile has no photos from the last 90 days. "
                "Recent project photos signal activity to both Google and potential customers."
            ),
            "no_review_responses": (
                "Google rewards businesses that respond to reviews. "
                "You have {unresponded_count} unresponded reviews."
            ),
            "service_area_gaps": (
                "Your site doesn't mention {missing_areas}. "
                "Competitors ranking for these suburbs are getting calls you're missing."
            ),
        }
    ),

    "generic": BusinessProfile(
        name="generic",
        display_name="General Business",
        description="Default profile for general businesses without industry-specific needs.",
        weights={
            "technical": 0.30,
            "content_eeat": 0.35,
            "ai_visibility": 0.35,
        },
        blockers=GENERIC_BLOCKERS,
        benchmarks={
            "technical": 75,
            "content_eeat": 70,
            "ai_visibility": 50,
            "overall": 70,
        },
        quick_win_templates={
            "slow_site": "Your site takes {load_time}s to load. Each second of delay can reduce conversions by 7%.",
            "missing_meta": "Missing meta descriptions on {count} pages means Google is writing your search snippets for you.",
        }
    ),

    "professional_services": BusinessProfile(
        name="professional_services",
        display_name="Professional Services",
        description="Law firms, accountants, consultants. E-E-A-T and trust signals are critical.",
        weights={
            "content_eeat": 0.35,      # Expertise and trust are paramount
            "technical": 0.20,
            "local_gbp": 0.20,
            "lead_funnel": 0.15,
            "authority": 0.10,
        },
        blockers=[
            BlockerConfig(
                id="no_ssl",
                description="Site does not have SSL/HTTPS",
                max_score=35,  # Even more critical for professional services
                category="technical",
                check_field="has_ssl",
                threshold=False,
                comparison="equals"
            ),
            BlockerConfig(
                id="no_about_page",
                description="No about page or team information",
                max_score=60,
                category="content_eeat",
                check_field="has_about_page",
                threshold=False,
                comparison="equals"
            ),
        ],
        benchmarks={
            "content_eeat": 80,
            "technical": 75,
            "local_gbp": 70,
            "lead_funnel": 70,
            "authority": 60,
            "overall": 75,
        },
        quick_win_templates={
            "credentials_missing": (
                "Your team credentials aren't visible on your website. "
                "Professional certifications build trust with potential clients."
            ),
        }
    ),
}


def get_business_profile(profile_name: str) -> BusinessProfile:
    """
    Get a business profile by name.

    Args:
        profile_name: Name of the business profile

    Returns:
        BusinessProfile instance (falls back to 'generic' if not found)
    """
    return BUSINESS_PROFILES.get(profile_name, BUSINESS_PROFILES["generic"])


def list_available_profiles() -> List[Dict[str, str]]:
    """
    List all available business profiles.

    Returns:
        List of dicts with profile info
    """
    return [
        {
            "name": profile.name,
            "display_name": profile.display_name,
            "description": profile.description,
        }
        for profile in BUSINESS_PROFILES.values()
    ]


def get_profile_weights(profile_name: str) -> Dict[str, float]:
    """
    Get weights for a specific profile.

    Args:
        profile_name: Name of the business profile

    Returns:
        Dict of category weights
    """
    profile = get_business_profile(profile_name)
    return profile.weights.copy()


def get_profile_blockers(profile_name: str) -> List[BlockerConfig]:
    """
    Get blockers for a specific profile.

    Args:
        profile_name: Name of the business profile

    Returns:
        List of BlockerConfig instances
    """
    profile = get_business_profile(profile_name)
    return profile.blockers.copy()


def get_quick_win_template(profile_name: str, template_id: str) -> Optional[str]:
    """
    Get a quick win template for a specific profile.

    Args:
        profile_name: Name of the business profile
        template_id: ID of the quick win template

    Returns:
        Template string or None
    """
    profile = get_business_profile(profile_name)
    return profile.quick_win_templates.get(template_id)


__all__ = [
    "BlockerConfig",
    "BusinessProfile",
    "BUSINESS_PROFILES",
    "get_business_profile",
    "list_available_profiles",
    "get_profile_weights",
    "get_profile_blockers",
    "get_quick_win_template",
]
