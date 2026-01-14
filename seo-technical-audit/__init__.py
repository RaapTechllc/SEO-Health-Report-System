"""
SEO Technical Audit

Comprehensive technical SEO analysis covering crawlability, page speed,
mobile optimization, security, and structured data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .scripts.crawl_site import analyze_crawlability, check_robots, check_sitemaps
from .scripts.analyze_speed import analyze_speed, get_pagespeed_insights
from .scripts.check_security import analyze_security
from .scripts.validate_schema import validate_structured_data


__version__ = "1.0.0"


async def run_audit(
    target_url: str,
    depth: int = 50,
    competitor_urls: Optional[List[str]] = None,
    strategy: str = "mobile"
) -> Dict[str, Any]:
    """
    Run a complete technical SEO audit.

    Args:
        target_url: Root domain to audit
        depth: Maximum pages to crawl (default: 50)
        competitor_urls: Optional competitor URLs for comparison
        strategy: PageSpeed strategy - "mobile" or "desktop"

    Returns:
        Dict with complete audit results including:
        - score: Overall Technical Health Score (0-100)
        - grade: Letter grade (A-F)
        - components: Detailed scores per component
        - critical_issues: List of critical issues
        - recommendations: Prioritized action items
    """
    results = {
        "url": target_url,
        "timestamp": datetime.now().isoformat(),
        "score": 0,
        "grade": "F",
        "components": {},
        "critical_issues": [],
        "recommendations": []
    }

    # Component 1: Crawlability (20 points)
    crawl_result = analyze_crawlability(target_url, depth=depth)
    results["components"]["crawlability"] = {
        "score": crawl_result["score"],
        "max": crawl_result["max"],
        "issues": crawl_result.get("issues", []),
        "findings": crawl_result.get("findings", [])
    }

    # Component 2: Indexing (15 points) - Part of crawlability
    indexing_score = min(15, crawl_result.get("sitemaps", {}).get("score", 0))
    results["components"]["indexing"] = {
        "score": indexing_score,
        "max": 15,
        "issues": crawl_result.get("sitemaps", {}).get("issues", []),
        "findings": [f"Sitemap URLs: {crawl_result.get('sitemaps', {}).get('total_urls', 0)}"]
    }

    # Component 3: Speed (25 points)
    speed_result = await analyze_speed(target_url, strategy=strategy)
    results["components"]["speed"] = {
        "score": speed_result["score"],
        "max": speed_result["max"],
        "psi_score": speed_result.get("psi_score"),
        "core_web_vitals": speed_result.get("core_web_vitals", {}),
        "issues": speed_result.get("issues", []),
        "findings": speed_result.get("findings", []),
        "opportunities": speed_result.get("opportunities", [])
    }

    # Component 4: Mobile (15 points) - Derived from mobile PSI
    mobile_result = await analyze_speed(target_url, strategy="mobile")
    mobile_psi = mobile_result.get("psi_score") or 0
    mobile_score = 15 if mobile_psi >= 90 else \
                   12 if mobile_psi >= 75 else \
                   9 if mobile_psi >= 50 else \
                   6 if mobile_psi >= 25 else 3
    results["components"]["mobile"] = {
        "score": mobile_score,
        "max": 15,
        "psi_score": mobile_result.get("psi_score"),
        "issues": mobile_result.get("issues", []),
        "findings": [f"Mobile PageSpeed Score: {mobile_result.get('psi_score', 'N/A')}"]
    }

    # Component 5: Security (10 points)
    security_result = analyze_security(target_url)
    results["components"]["security"] = {
        "score": security_result["score"],
        "max": security_result["max"],
        "https": security_result.get("https", {}),
        "headers": security_result.get("headers", {}),
        "issues": security_result.get("issues", []),
        "findings": security_result.get("findings", [])
    }

    # Component 6: Structured Data (15 points)
    schema_result = validate_structured_data(target_url)
    results["components"]["structured_data"] = {
        "score": schema_result["score"],
        "max": schema_result["max"],
        "schema_types": schema_result.get("schema_types", []),
        "rich_results": schema_result.get("rich_results", {}),
        "issues": schema_result.get("issues", []),
        "findings": schema_result.get("findings", [])
    }

    # Calculate total score
    total_score = sum(
        comp["score"] for comp in results["components"].values()
    )
    results["score"] = total_score

    # Assign grade
    if total_score >= 90:
        results["grade"] = "A"
    elif total_score >= 80:
        results["grade"] = "B"
    elif total_score >= 70:
        results["grade"] = "C"
    elif total_score >= 60:
        results["grade"] = "D"
    else:
        results["grade"] = "F"

    # Collect critical issues
    for comp_name, comp_data in results["components"].items():
        for issue in comp_data.get("issues", []):
            # Handle both dict and dataclass issues
            severity = issue.get("severity") if isinstance(issue, dict) else getattr(issue, "severity", None)
            description = issue.get("description") if isinstance(issue, dict) else getattr(issue, "description", "")
            recommendation = issue.get("recommendation") if isinstance(issue, dict) else getattr(issue, "recommendation", "")
            
            if severity == "critical":
                results["critical_issues"].append({
                    "component": comp_name,
                    "description": description,
                    "recommendation": recommendation
                })

    # Generate recommendations
    results["recommendations"] = generate_recommendations(results)

    # Run competitor comparison if provided
    if competitor_urls:
        results["competitor_comparison"] = run_competitor_comparison(
            target_url, results["score"], competitor_urls, strategy
        )

    return results


def _get_issue_attr(issue, attr, default=""):
    """Get attribute from issue (handles both dict and dataclass)."""
    if isinstance(issue, dict):
        return issue.get(attr, default)
    return getattr(issue, attr, default)


def generate_recommendations(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate prioritized recommendations based on audit results."""
    recommendations = []

    components = results.get("components", {})

    # Security recommendations (highest priority)
    security = components.get("security", {})
    if security.get("score", 0) < 8:
        for issue in security.get("issues", []):
            if _get_issue_attr(issue, "severity") in ["critical", "high"]:
                recommendations.append({
                    "priority": "high",
                    "category": "security",
                    "action": _get_issue_attr(issue, "description", "Fix security issue"),
                    "details": _get_issue_attr(issue, "recommendation", ""),
                    "impact": "high",
                    "effort": "medium"
                })

    # Speed recommendations
    speed = components.get("speed", {})
    if speed.get("score", 0) < 20:
        # Add top opportunities
        for opp in speed.get("opportunities", [])[:3]:
            recommendations.append({
                "priority": "high" if _get_issue_attr(opp, "savings_ms", 0) > 1000 else "medium",
                "category": "speed",
                "action": _get_issue_attr(opp, "title", "Optimize performance"),
                "details": f"Potential savings: {_get_issue_attr(opp, 'savings_display', 'N/A')}",
                "impact": "high",
                "effort": "medium"
            })

    # Crawlability recommendations
    crawl = components.get("crawlability", {})
    if crawl.get("score", 0) < 15:
        for issue in crawl.get("issues", []):
            if _get_issue_attr(issue, "severity") in ["critical", "high"]:
                recommendations.append({
                    "priority": "high",
                    "category": "crawlability",
                    "action": _get_issue_attr(issue, "description", "Fix crawlability issue"),
                    "details": _get_issue_attr(issue, "recommendation", ""),
                    "impact": "high",
                    "effort": "low"
                })

    # Structured data recommendations
    schema = components.get("structured_data", {})
    if schema.get("score", 0) < 10:
        if not schema.get("schema_types"):
            recommendations.append({
                "priority": "medium",
                "category": "structured_data",
                "action": "Add structured data",
                "details": "Implement JSON-LD for Organization and relevant content types",
                "impact": "medium",
                "effort": "low"
            })
        else:
            for issue in schema.get("issues", []):
                if _get_issue_attr(issue, "severity") == "high":
                    recommendations.append({
                        "priority": "medium",
                        "category": "structured_data",
                        "action": _get_issue_attr(issue, "description", "Fix schema issue"),
                        "details": _get_issue_attr(issue, "recommendation", ""),
                        "impact": "medium",
                        "effort": "low"
                    })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))

    return recommendations[:10]  # Top 10 recommendations


def run_competitor_comparison(
    target_url: str,
    target_score: int,
    competitor_urls: List[str],
    strategy: str = "mobile"
) -> Dict[str, Any]:
    """
    Run quick comparison against competitors.

    Args:
        target_url: Your URL
        target_score: Your calculated score
        competitor_urls: Competitor URLs to compare
        strategy: PageSpeed strategy

    Returns:
        Dict with comparison data
    """
    comparison = {
        "your_score": target_score,
        "competitor_scores": {},
        "component_comparison": {}
    }

    for comp_url in competitor_urls[:3]:  # Limit to 3 competitors
        try:
            # Quick check - just speed for comparison
            speed = analyze_speed(comp_url, strategy=strategy)
            psi_score = speed.get("psi_score", 0)

            # Rough estimate of total score based on PSI
            estimated_score = int(psi_score * 0.7)  # PSI correlates roughly

            from urllib.parse import urlparse
            domain = urlparse(comp_url).netloc
            comparison["competitor_scores"][domain] = estimated_score

            if "speed" not in comparison["component_comparison"]:
                comparison["component_comparison"]["speed"] = {}
            comparison["component_comparison"]["speed"][domain] = speed.get("score", 0)

        except Exception:
            pass

    return comparison


def format_report(results: Dict[str, Any]) -> str:
    """Format audit results as a readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("TECHNICAL SEO AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"\nURL: {results['url']}")
    lines.append(f"Date: {results['timestamp']}")
    lines.append(f"\nOVERALL SCORE: {results['score']}/100 (Grade: {results['grade']})")

    lines.append("\n" + "-" * 60)
    lines.append("COMPONENT SCORES")
    lines.append("-" * 60)

    for name, data in results.get("components", {}).items():
        score = data.get("score", 0)
        max_score = data.get("max", 0)
        status = "GOOD" if score >= max_score * 0.8 else \
                 "FAIR" if score >= max_score * 0.5 else "POOR"
        lines.append(f"  {name.replace('_', ' ').title()}: {score}/{max_score} [{status}]")

    if results.get("critical_issues"):
        lines.append("\n" + "-" * 60)
        lines.append("CRITICAL ISSUES")
        lines.append("-" * 60)
        for issue in results["critical_issues"]:
            lines.append(f"\n  [{issue['component'].upper()}]")
            lines.append(f"  {issue['description']}")
            if issue.get('recommendation'):
                lines.append(f"  Fix: {issue['recommendation']}")

    lines.append("\n" + "-" * 60)
    lines.append("TOP RECOMMENDATIONS")
    lines.append("-" * 60)

    for rec in results.get("recommendations", [])[:5]:
        priority = rec.get("priority", "").upper()
        lines.append(f"\n[{priority}] {rec['action']}")
        if rec.get('details'):
            lines.append(f"  {rec['details']}")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)


__all__ = [
    'run_audit',
    'generate_recommendations',
    'format_report',
    'analyze_crawlability',
    'analyze_speed',
    'analyze_security',
    'validate_structured_data'
]
