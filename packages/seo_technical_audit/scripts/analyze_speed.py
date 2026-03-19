"""
Analyze Page Speed

PageSpeed Insights integration and Core Web Vitals analysis.
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional

# Add parent directory to path for config import
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from seo_health_report.config import get_config

# Get config
_config = get_config()
PAGESPEED_API_ENDPOINT = _config.pagespeed_api_endpoint
PAGESPEED_STRATEGY = _config.pagespeed_strategy
PAGESPEED_CATEGORIES = _config.pagespeed_categories

# Cache imports with fallback
try:
    from seo_health_report.scripts.cache import TTL_PAGESPEED, cached

    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False

    def cached(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    TTL_PAGESPEED = 0


@dataclass
class SpeedIssue:
    """A page speed issue found during analysis."""

    severity: str
    category: str
    description: str
    metric: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    recommendation: str = ""


# Core Web Vitals thresholds
CWV_THRESHOLDS = {
    "lcp": {  # Largest Contentful Paint
        "good": 2500,  # ms
        "needs_improvement": 4000,
        "unit": "ms",
    },
    "fid": {  # First Input Delay
        "good": 100,  # ms
        "needs_improvement": 300,
        "unit": "ms",
    },
    "cls": {  # Cumulative Layout Shift
        "good": 0.1,
        "needs_improvement": 0.25,
        "unit": "score",
    },
    "fcp": {  # First Contentful Paint
        "good": 1800,  # ms
        "needs_improvement": 3000,
        "unit": "ms",
    },
    "ttfb": {  # Time to First Byte
        "good": 800,  # ms
        "needs_improvement": 1800,
        "unit": "ms",
    },
    "inp": {  # Interaction to Next Paint (replacing FID)
        "good": 200,  # ms
        "needs_improvement": 500,
        "unit": "ms",
    },
}


@cached("pagespeed", TTL_PAGESPEED)
async def get_pagespeed_insights(
    url: str, strategy: str = "mobile", api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Fetch PageSpeed Insights data from Google.

    Args:
        url: URL to analyze
        strategy: "mobile" or "desktop"
        api_key: Optional API key (uses PAGESPEED_API_KEY env var if not provided)

    Returns:
        Dict with PageSpeed Insights data
    """
    # Support multiple env var names for flexibility
    api_key = (
        api_key
        or os.environ.get("PAGESPEED_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )

    result = {
        "url": url,
        "strategy": strategy,
        "success": False,
        "score": None,
        "metrics": {},
        "opportunities": [],
        "diagnostics": [],
        "error": None,
    }

    try:
        import httpx

        async with httpx.AsyncClient(timeout=60) as client:
            # Build API URL
            params = {"url": url, "strategy": strategy}

            # Add first category (primary is performance)
            params["category"] = (
                PAGESPEED_CATEGORIES[0] if PAGESPEED_CATEGORIES else "performance"
            )

            if api_key:
                params["key"] = api_key

            response = await client.get(PAGESPEED_API_ENDPOINT, params=params)

            if response.status_code == 429:
                result["error"] = "Rate limited - try again later or add API key"
                return result

            response.raise_for_status()
            data = response.json()

            result["success"] = True

            # Extract performance score
            lighthouse = data.get("lighthouseResult", {})
            categories = lighthouse.get("categories", {})
            performance = categories.get("performance", {})
            result["score"] = int(performance.get("score", 0) * 100)

            # Extract Core Web Vitals
            audits = lighthouse.get("audits", {})

            # LCP
            lcp_audit = audits.get("largest-contentful-paint", {})
            if lcp_audit:
                result["metrics"]["lcp"] = {
                    "value": lcp_audit.get("numericValue"),
                    "display": lcp_audit.get("displayValue"),
                    "score": lcp_audit.get("score"),
                }

            # FID (or INP)
            fid_audit = audits.get("max-potential-fid", {})
            if fid_audit:
                result["metrics"]["fid"] = {
                    "value": fid_audit.get("numericValue"),
                    "display": fid_audit.get("displayValue"),
                    "score": fid_audit.get("score"),
                }

            # CLS
            cls_audit = audits.get("cumulative-layout-shift", {})
            if cls_audit:
                result["metrics"]["cls"] = {
                    "value": cls_audit.get("numericValue"),
                    "display": cls_audit.get("displayValue"),
                    "score": cls_audit.get("score"),
                }

            # FCP
            fcp_audit = audits.get("first-contentful-paint", {})
            if fcp_audit:
                result["metrics"]["fcp"] = {
                    "value": fcp_audit.get("numericValue"),
                    "display": fcp_audit.get("displayValue"),
                    "score": fcp_audit.get("score"),
                }

            # TTFB
            ttfb_audit = audits.get("server-response-time", {})
            if ttfb_audit:
                result["metrics"]["ttfb"] = {
                    "value": ttfb_audit.get("numericValue"),
                    "display": ttfb_audit.get("displayValue"),
                    "score": ttfb_audit.get("score"),
                }

            # Speed Index
            si_audit = audits.get("speed-index", {})
            if si_audit:
                result["metrics"]["speed_index"] = {
                    "value": si_audit.get("numericValue"),
                    "display": si_audit.get("displayValue"),
                    "score": si_audit.get("score"),
                }

            # Total Blocking Time
            tbt_audit = audits.get("total-blocking-time", {})
            if tbt_audit:
                result["metrics"]["tbt"] = {
                    "value": tbt_audit.get("numericValue"),
                    "display": tbt_audit.get("displayValue"),
                    "score": tbt_audit.get("score"),
                }

            # Extract opportunities
            for audit_id, audit in audits.items():
                if audit.get("score") is not None and audit.get("score") < 0.9:
                    if audit.get("details", {}).get("type") == "opportunity":
                        result["opportunities"].append(
                            {
                                "id": audit_id,
                                "title": audit.get("title"),
                                "description": audit.get("description"),
                                "savings_ms": audit.get("details", {}).get(
                                    "overallSavingsMs"
                                ),
                                "savings_bytes": audit.get("details", {}).get(
                                    "overallSavingsBytes"
                                ),
                            }
                        )

            # Sort opportunities by potential savings
            result["opportunities"].sort(
                key=lambda x: x.get("savings_ms") or 0, reverse=True
            )

    except ImportError:
        result["error"] = "httpx package not installed. Install with: pip install httpx"
    except Exception as e:
        result["error"] = str(e)

    return result


async def get_pagespeed_insights_both(
    url: str, api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Fetch PageSpeed Insights for both mobile and desktop in parallel.

    Args:
        url: URL to analyze
        api_key: Optional API key (uses PAGESPEED_API_KEY env var if not provided)

    Returns:
        Dict with 'mobile' and 'desktop' keys containing their respective results
    """
    # Fetch both mobile and desktop in parallel
    mobile_result, desktop_result = await asyncio.gather(
        get_pagespeed_insights(url, "mobile", api_key),
        get_pagespeed_insights(url, "desktop", api_key),
        return_exceptions=True,
    )

    # Handle exceptions
    if isinstance(mobile_result, Exception):
        mobile_result = {
            "url": url,
            "strategy": "mobile",
            "success": False,
            "error": str(mobile_result),
        }

    if isinstance(desktop_result, Exception):
        desktop_result = {
            "url": url,
            "strategy": "desktop",
            "success": False,
            "error": str(desktop_result),
        }

    return {
        "url": url,
        "mobile": mobile_result,
        "desktop": desktop_result,
    }


def analyze_core_web_vitals(psi_data: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze Core Web Vitals from PageSpeed Insights data.

    Args:
        psi_data: Data from get_pagespeed_insights()

    Returns:
        Dict with CWV analysis and score
    """
    result = {
        "score": 0,
        "max": 25,
        "metrics": {},
        "issues": [],
        "findings": [],
        "all_pass": True,
    }

    if not psi_data.get("success"):
        result["issues"].append(
            {
                "severity": "high",
                "category": "speed",
                "description": f"Could not fetch PageSpeed data: {psi_data.get('error', 'Unknown error')}",
                "recommendation": "Verify URL is accessible and try again",
            }
        )
        result["score"] = 5  # Give minimal score if can't check
        return result

    metrics = psi_data.get("metrics", {})

    # Analyze each Core Web Vital
    cwv_metrics = ["lcp", "fid", "cls", "fcp", "ttfb"]

    for metric_name in cwv_metrics:
        metric_data = metrics.get(metric_name)
        if not metric_data:
            continue

        value = metric_data.get("value")
        if value is None:
            continue

        thresholds = CWV_THRESHOLDS.get(metric_name, {})
        good_threshold = thresholds.get("good")
        poor_threshold = thresholds.get("needs_improvement")
        thresholds.get("unit", "")

        # Determine status
        if metric_name == "cls":
            # CLS is a score, not milliseconds
            if value <= good_threshold:
                status = "good"
            elif value <= poor_threshold:
                status = "needs_improvement"
            else:
                status = "poor"
        else:
            if value <= good_threshold:
                status = "good"
            elif value <= poor_threshold:
                status = "needs_improvement"
            else:
                status = "poor"

        result["metrics"][metric_name] = {
            "value": value,
            "display": metric_data.get("display"),
            "status": status,
            "thresholds": thresholds,
        }

        # Generate findings and issues
        metric_labels = {
            "lcp": "Largest Contentful Paint",
            "fid": "First Input Delay",
            "cls": "Cumulative Layout Shift",
            "fcp": "First Contentful Paint",
            "ttfb": "Time to First Byte",
        }

        label = metric_labels.get(metric_name, metric_name.upper())

        if status == "good":
            result["findings"].append(f"{label}: {metric_data.get('display')} (Good)")
        elif status == "needs_improvement":
            result["findings"].append(
                f"{label}: {metric_data.get('display')} (Needs Improvement)"
            )
            result["all_pass"] = False
            result["issues"].append(
                {
                    "severity": "medium",
                    "category": "speed",
                    "metric": metric_name,
                    "description": f"{label} needs improvement: {metric_data.get('display')}",
                    "value": value,
                    "threshold": good_threshold,
                    "recommendation": get_metric_recommendation(metric_name),
                }
            )
        else:
            result["findings"].append(f"{label}: {metric_data.get('display')} (Poor)")
            result["all_pass"] = False
            result["issues"].append(
                {
                    "severity": "high",
                    "category": "speed",
                    "metric": metric_name,
                    "description": f"{label} is poor: {metric_data.get('display')}",
                    "value": value,
                    "threshold": good_threshold,
                    "recommendation": get_metric_recommendation(metric_name),
                }
            )

    # Calculate score based on PSI score and CWV status
    psi_score = psi_data.get("score") or 0  # Handle None explicitly

    if psi_score >= 90:
        result["score"] = 25
    elif psi_score >= 75:
        result["score"] = 20
    elif psi_score >= 50:
        result["score"] = 15
    elif psi_score >= 25:
        result["score"] = 10
    else:
        result["score"] = 5

    # Deduct for poor CWV
    for issue in result["issues"]:
        if issue["severity"] == "high":
            result["score"] = max(5, result["score"] - 3)
        elif issue["severity"] == "medium":
            result["score"] = max(5, result["score"] - 1)

    result["psi_score"] = psi_score
    result["findings"].append(f"PageSpeed Insights Score: {psi_score}/100")

    return result


def get_metric_recommendation(metric: str) -> str:
    """Get improvement recommendation for a specific metric."""
    recommendations = {
        "lcp": "Optimize images, use CDN, preload critical resources, reduce server response time",
        "fid": "Minimize JavaScript execution time, break up long tasks, use web workers",
        "cls": "Set explicit dimensions on images/videos, reserve space for dynamic content, avoid inserting content above existing content",
        "fcp": "Eliminate render-blocking resources, optimize critical rendering path, use preconnect for key origins",
        "ttfb": "Optimize server configuration, use CDN, implement caching, reduce server-side processing",
    }
    return recommendations.get(metric, "Review PageSpeed Insights recommendations")


def check_resource_optimization(psi_data: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze resource optimization opportunities.

    Args:
        psi_data: Data from get_pagespeed_insights()

    Returns:
        Dict with resource optimization analysis
    """
    result = {
        "opportunities": [],
        "total_savings_ms": 0,
        "total_savings_bytes": 0,
        "issues": [],
        "findings": [],
    }

    opportunities = psi_data.get("opportunities", [])

    for opp in opportunities:
        savings_ms = opp.get("savings_ms", 0)
        savings_bytes = opp.get("savings_bytes", 0)

        result["opportunities"].append(
            {
                "title": opp.get("title"),
                "description": opp.get("description"),
                "savings_ms": savings_ms,
                "savings_bytes": savings_bytes,
                "savings_display": format_savings(savings_ms, savings_bytes),
            }
        )

        result["total_savings_ms"] += savings_ms or 0
        result["total_savings_bytes"] += savings_bytes or 0

        # Convert significant opportunities to issues
        if savings_ms and savings_ms > 500:
            result["issues"].append(
                {
                    "severity": "medium" if savings_ms > 1000 else "low",
                    "category": "speed",
                    "description": f"{opp.get('title')}: Could save {savings_ms}ms",
                    "recommendation": opp.get(
                        "description", "Implement suggested optimization"
                    ),
                }
            )

    # Generate findings
    if result["opportunities"]:
        result["findings"].append(
            f"Found {len(result['opportunities'])} optimization opportunities"
        )
        result["findings"].append(
            f"Potential savings: {result['total_savings_ms']}ms, {format_bytes(result['total_savings_bytes'])}"
        )
    else:
        result["findings"].append("No major optimization opportunities found")

    return result


def format_savings(ms: Optional[float], bytes_saved: Optional[int]) -> str:
    """Format savings for display."""
    parts = []
    if ms:
        parts.append(f"{int(ms)}ms")
    if bytes_saved:
        parts.append(format_bytes(bytes_saved))
    return ", ".join(parts) if parts else "N/A"


def format_bytes(bytes_val: Optional[int]) -> str:
    """Format bytes for display."""
    if not bytes_val:
        return "0 B"
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.1f} MB"


async def analyze_speed(url: str, strategy: str = "mobile") -> dict[str, Any]:
    """
    Complete speed analysis for a URL.

    Args:
        url: URL to analyze
        strategy: "mobile" or "desktop"

    Returns:
        Dict with complete speed analysis
    """
    result = {
        "score": 0,
        "max": 25,
        "url": url,
        "strategy": strategy,
        "psi_score": None,
        "core_web_vitals": {},
        "opportunities": [],
        "issues": [],
        "findings": [],
    }

    # Get PageSpeed Insights data
    psi_data = await get_pagespeed_insights(url, strategy)

    if not psi_data.get("success"):
        result["issues"].append(
            {
                "severity": "high",
                "category": "speed",
                "description": f"Could not analyze page speed: {psi_data.get('error')}",
                "recommendation": "Verify URL is accessible",
            }
        )
        result["score"] = 5
        result["findings"].append("Page speed analysis failed")
        return result

    # Analyze Core Web Vitals
    cwv_result = analyze_core_web_vitals(psi_data)
    result["core_web_vitals"] = cwv_result.get("metrics", {})
    result["issues"].extend(cwv_result.get("issues", []))
    result["findings"].extend(cwv_result.get("findings", []))
    result["psi_score"] = psi_data.get("score")

    # Check resource optimization
    resource_result = check_resource_optimization(psi_data)
    result["opportunities"] = resource_result.get("opportunities", [])
    result["issues"].extend(resource_result.get("issues", []))
    result["findings"].extend(resource_result.get("findings", []))

    # Calculate final score
    result["score"] = cwv_result.get("score", 0)

    return result


def analyze_speed_sync(url: str, strategy: str = "mobile") -> dict[str, Any]:
    """
    Sync wrapper for analyze_speed for backwards compatibility.
    """
    return asyncio.run(analyze_speed(url, strategy))


def get_pagespeed_insights_sync(
    url: str, strategy: str = "mobile", api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Sync wrapper for get_pagespeed_insights for backwards compatibility.
    """
    return asyncio.run(get_pagespeed_insights(url, strategy, api_key))


def get_pagespeed_insights_both_sync(
    url: str, api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Sync wrapper for get_pagespeed_insights_both for backwards compatibility.
    """
    return asyncio.run(get_pagespeed_insights_both(url, api_key))


__all__ = [
    "SpeedIssue",
    "CWV_THRESHOLDS",
    "get_pagespeed_insights",
    "get_pagespeed_insights_sync",
    "get_pagespeed_insights_both",
    "get_pagespeed_insights_both_sync",
    "analyze_core_web_vitals",
    "check_resource_optimization",
    "analyze_speed",
    "analyze_speed_sync",
]
