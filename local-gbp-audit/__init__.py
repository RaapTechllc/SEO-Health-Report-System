"""
Local/GBP Audit Module

Analyze local SEO: Google Business Profile, citations, NAP consistency, and local keywords.
For mechanical trades: 60-70% of searches have local intent - this is critical.
"""

import sys
import os
from typing import Dict, Any, List, Optional

# Add scripts to path
scripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from scripts.check_gbp import GBPData, analyze_gbp_health
from scripts.check_citations import analyze_citations
from scripts.check_local_seo import analyze_local_seo


def run_audit(
    target_url: str,
    service_areas: List[str] = None,
    gbp_data: Optional[GBPData] = None,
) -> Dict[str, Any]:
    """
    Run complete local/GBP audit.

    Args:
        target_url: URL to audit
        service_areas: List of target service areas/cities
        gbp_data: Optional manual GBP data input

    Returns:
        Dict with audit results
    """
    result = {
        "score": 0,
        "max": 34,  # 12 (GBP website signals) + 12 (citations) + 10 (local SEO)
        "grade": "F",
        "gbp_claimed": None,
        "components": {
            "gbp": {},
            "citations": {},
            "local_seo": {},
        },
        "issues": [],
        "findings": [],
        "recommendations": [],
        "quick_wins": [],
        "manual_checklist": [],  # For GBP data collection
    }

    # If GBP data provided, adjust max score
    if gbp_data:
        result["max"] = 52  # 30 (full GBP) + 12 (citations) + 10 (local SEO)

    # Run GBP audit
    gbp_result = analyze_gbp_health(target_url, gbp_data)
    result["components"]["gbp"] = gbp_result
    result["score"] += gbp_result.get("score", 0)
    result["gbp_claimed"] = gbp_result.get("gbp_claimed")
    result["issues"].extend(gbp_result.get("issues", []))
    result["findings"].extend(gbp_result.get("findings", []))
    result["quick_wins"].extend(gbp_result.get("quick_wins", []))
    result["manual_checklist"] = gbp_result.get("manual_checklist", [])

    # Run citations audit
    citations_result = analyze_citations(target_url)
    result["components"]["citations"] = citations_result
    result["score"] += citations_result.get("score", 0)
    result["issues"].extend(citations_result.get("issues", []))
    result["findings"].extend(citations_result.get("findings", []))
    result["quick_wins"].extend(citations_result.get("quick_wins", []))

    # Run local SEO audit
    local_result = analyze_local_seo(target_url, service_areas)
    result["components"]["local_seo"] = local_result
    result["score"] += local_result.get("score", 0)
    result["issues"].extend(local_result.get("issues", []))
    result["findings"].extend(local_result.get("findings", []))
    result["quick_wins"].extend(local_result.get("quick_wins", []))

    # Calculate grade
    score_percent = (result["score"] / result["max"]) * 100 if result["max"] > 0 else 0
    if score_percent >= 90:
        result["grade"] = "A"
    elif score_percent >= 80:
        result["grade"] = "B"
    elif score_percent >= 70:
        result["grade"] = "C"
    elif score_percent >= 60:
        result["grade"] = "D"
    else:
        result["grade"] = "F"

    # Generate recommendations from issues
    for issue in result["issues"]:
        if issue.get("recommendation"):
            result["recommendations"].append({
                "text": issue["recommendation"],
                "priority": "high" if issue.get("severity") in ["critical", "high"] else "medium",
                "effort": "low" if "schema" in issue.get("description", "").lower() else "medium",
            })

    # Sort quick wins by impact
    impact_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    result["quick_wins"].sort(key=lambda x: impact_order.get(x.get("impact", "low"), 3))

    return result


async def run_audit_async(
    target_url: str,
    service_areas: List[str] = None,
    gbp_data: Optional[GBPData] = None,
) -> Dict[str, Any]:
    """
    Async wrapper for run_audit.
    """
    return run_audit(target_url, service_areas, gbp_data)


def create_gbp_data_from_dict(data: Dict[str, Any]) -> GBPData:
    """
    Create GBPData from a dictionary (e.g., from JSON input).

    Args:
        data: Dictionary with GBP data fields

    Returns:
        GBPData instance
    """
    return GBPData(
        claimed_verified=data.get("claimed_verified", False),
        categories_accurate=data.get("categories_accurate", False),
        primary_category=data.get("primary_category", ""),
        service_areas_configured=data.get("service_areas_configured", False),
        service_areas=data.get("service_areas", []),
        photos_count_90_days=data.get("photos_count_90_days", 0),
        photos_variety=data.get("photos_variety", False),
        posts_last_30_days=data.get("posts_last_30_days", False),
        qa_response_rate=data.get("qa_response_rate", 0.0),
        hours_accurate=data.get("hours_accurate", False),
        emergency_hours_match_claim=data.get("emergency_hours_match_claim", True),
        review_response_rate=data.get("review_response_rate", 0.0),
        review_count=data.get("review_count", 0),
        review_rating=data.get("review_rating", 0.0),
        review_recency_days=data.get("review_recency_days", 999),
    )


__all__ = [
    'run_audit',
    'run_audit_async',
    'GBPData',
    'create_gbp_data_from_dict',
    'analyze_gbp_health',
    'analyze_citations',
    'analyze_local_seo',
]
