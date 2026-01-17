"""
Conversion UX Audit Module

Analyze conversion optimization: phone placement, CTAs, forms, and tracking.
For mechanical trades: Phone number placement matters more than backlinks.
"""

import sys
import os
from typing import Dict, Any, List, Optional

# Add scripts to path
scripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from scripts.check_phone import analyze_phone_optimization
from scripts.check_cta import analyze_cta_optimization
from scripts.check_forms import analyze_form_optimization
from scripts.check_tracking import analyze_tracking_setup


def run_audit(
    target_url: str,
    deep_check: bool = False,
) -> Dict[str, Any]:
    """
    Run complete conversion/UX audit.

    Args:
        target_url: URL to audit
        deep_check: Whether to check multiple pages (slower)

    Returns:
        Dict with audit results (0-22 score broken into components)
    """
    result = {
        "score": 0,
        "max": 22,
        "grade": "F",
        "phone_click_to_call": False,
        "phone_above_fold_mobile": False,
        "primary_cta_above_fold": False,
        "ga4_installed": False,
        "phone_click_tracking": False,
        "form_fields_count": 0,
        "components": {
            "phone": {},
            "cta": {},
            "forms": {},
            "tracking": {},
        },
        "issues": [],
        "findings": [],
        "recommendations": [],
        "quick_wins": [],
    }

    # Run phone optimization audit
    phone_result = analyze_phone_optimization(target_url)
    result["components"]["phone"] = phone_result
    result["score"] += phone_result.get("score", 0)
    result["phone_click_to_call"] = phone_result.get("phone_click_to_call", False)
    result["phone_above_fold_mobile"] = phone_result.get("phone_above_fold_mobile", False)
    result["issues"].extend(phone_result.get("issues", []))
    result["findings"].extend(phone_result.get("findings", []))
    result["quick_wins"].extend(phone_result.get("quick_wins", []))

    # Run CTA optimization audit
    cta_result = analyze_cta_optimization(target_url)
    result["components"]["cta"] = cta_result
    result["score"] += cta_result.get("score", 0)
    result["primary_cta_above_fold"] = cta_result.get("primary_cta_above_fold", False)
    result["issues"].extend(cta_result.get("issues", []))
    result["findings"].extend(cta_result.get("findings", []))
    result["quick_wins"].extend(cta_result.get("quick_wins", []))

    # Run form optimization audit
    form_result = analyze_form_optimization(target_url)
    result["components"]["forms"] = form_result
    result["score"] += form_result.get("score", 0)
    result["form_fields_count"] = form_result.get("form_fields_count", 0)
    result["issues"].extend(form_result.get("issues", []))
    result["findings"].extend(form_result.get("findings", []))
    result["quick_wins"].extend(form_result.get("quick_wins", []))

    # Run tracking audit
    tracking_result = analyze_tracking_setup(target_url)
    result["components"]["tracking"] = tracking_result
    result["score"] += tracking_result.get("score", 0)
    result["ga4_installed"] = tracking_result.get("ga4_installed", False)
    result["phone_click_tracking"] = tracking_result.get("phone_click_tracking", False)
    result["issues"].extend(tracking_result.get("issues", []))
    result["findings"].extend(tracking_result.get("findings", []))
    result["quick_wins"].extend(tracking_result.get("quick_wins", []))

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
                "impact": issue.get("impact_estimate", ""),
                "effort": "low",  # Most conversion fixes are quick
            })

    # Sort quick wins by impact
    impact_order = {"high": 0, "medium": 1, "low": 2}
    result["quick_wins"].sort(key=lambda x: impact_order.get(x.get("impact", "low"), 2))

    return result


async def run_audit_async(
    target_url: str,
    deep_check: bool = False,
) -> Dict[str, Any]:
    """
    Async wrapper for run_audit.
    """
    # For now, just call sync version since web requests are blocking anyway
    return run_audit(target_url, deep_check)


__all__ = [
    'run_audit',
    'run_audit_async',
    'analyze_phone_optimization',
    'analyze_cta_optimization',
    'analyze_form_optimization',
    'analyze_tracking_setup',
]
