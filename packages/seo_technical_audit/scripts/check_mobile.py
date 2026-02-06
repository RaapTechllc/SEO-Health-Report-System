"""
Check Mobile Optimization Configuration

Analyze viewport settings and mobile-specific meta tags.
"""

import re
from dataclasses import dataclass
from typing import Any

from .crawl_site import fetch_url


@dataclass
class MobileIssue:
    severity: str
    description: str
    recommendation: str

def check_viewport_tag(html: str) -> dict[str, Any]:
    """
    Check if the viewport meta tag is present and correctly configured.
    """
    issues = []
    viewport_pattern = r'<meta[^>]*name=["\']viewport["\'][^>]*content=["\']([^"\']+)["\']'
    match = re.search(viewport_pattern, html, re.IGNORECASE)

    if not match:
        # Check reverse order of attributes
        viewport_pattern_alt = r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']viewport["\']'
        match = re.search(viewport_pattern_alt, html, re.IGNORECASE)

    if not match:
        # Critical for mobile
        issues.append(MobileIssue(
            severity="critical",
            description="No viewport meta tag found",
            recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1'> to the <head>"
        ))
        return {"valid": False, "content": None, "issues": issues}

    content = match.group(1).lower()

    # Check for width=device-width
    if "width=device-width" not in content:
        issues.append(MobileIssue(
            severity="high",
            description="Viewport does not set width=device-width",
            recommendation="Include width=device-width in viewport content"
        ))

    # Check for initial-scale
    if "initial-scale=1" not in content and "initial-scale=1.0" not in content:
        issues.append(MobileIssue(
            severity="medium",
            description="Viewport does not set initial-scale=1",
            recommendation="Include initial-scale=1 in viewport content"
        ))

    # Check for user-scalable=no (accessibility issue)
    if "user-scalable=no" in content or "user-scalable=0" in content:
        issues.append(MobileIssue(
            severity="medium",
            description="Viewport prevents user zooming (user-scalable=no)",
            recommendation="Allow users to zoom for better accessibility"
        ))

    return {
        "valid": len(issues) == 0,
        "content": content,
        "issues": issues
    }

def analyze_mobile_config(url: str) -> dict[str, Any]:
    """
    Analyze mobile configuration (viewport, tap targets, etc.)
    Note: Tap targets are usually best checked via dynamic analysis (Lighthouse),
    but we can check static configuration here.
    """
    html = fetch_url(url)

    result = {
        "score": 0,
        "max": 10,
        "has_viewport": False,
        "issues": [],
        "findings": []
    }

    if not html:
        result["issues"].append({
            "severity": "high",
            "description": "Could not fetch page for mobile analysis",
            "recommendation": "Verify URL accessibility"
        })
        return result

    # Check Viewport
    viewport_check = check_viewport_tag(html)
    result["has_viewport"] = viewport_check["valid"]

    for issue in viewport_check["issues"]:
        result["issues"].append({
            "severity": issue.severity,
            "category": "mobile",
            "description": issue.description,
            "recommendation": issue.recommendation
        })

    # Calculate Score
    score = 10
    has_critical = False

    for issue in result["issues"]:
        if issue["severity"] == "critical":
            score -= 10
            has_critical = True
        elif issue["severity"] == "high":
            score -= 5
        elif issue["severity"] == "medium":
            score -= 2

    result["score"] = max(0, score)

    if result["has_viewport"]:
        result["findings"].append("Viewport meta tag configured correctly")
    elif has_critical:
        result["findings"].append("Missing valid viewport meta tag")

    return result
