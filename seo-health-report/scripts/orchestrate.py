"""
Orchestrate Full Audit

Main workflow controller that runs all sub-audits and coordinates results.
"""

import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_full_audit(
    target_url: str,
    company_name: str,
    primary_keywords: List[str],
    competitor_urls: Optional[List[str]] = None,
    ground_truth: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run all three audits and compile results.

    Args:
        target_url: Root domain to audit
        company_name: Company name for AI queries
        primary_keywords: Target keywords
        competitor_urls: Optional competitor URLs
        ground_truth: Optional facts for accuracy checking

    Returns:
        Dict with all audit results
    """
    results = {
        "url": target_url,
        "company_name": company_name,
        "timestamp": datetime.now().isoformat(),
        "audits": {
            "technical": None,
            "content": None,
            "ai_visibility": None
        },
        "warnings": [],
        "errors": []
    }

    # Run Technical Audit
    print(f"[1/3] Running Technical Audit for {target_url}...")
    try:
        from seo_technical_audit import run_audit as run_technical_audit
        results["audits"]["technical"] = run_technical_audit(
            target_url=target_url,
            depth=50,
            competitor_urls=competitor_urls
        )
        print(f"      Technical Score: {results['audits']['technical'].get('score', 'N/A')}/100")
    except ImportError as e:
        results["warnings"].append(f"Technical audit module not found: {e}")
        results["audits"]["technical"] = create_placeholder_result("technical")
    except Exception as e:
        results["errors"].append(f"Technical audit failed: {e}")
        results["audits"]["technical"] = create_placeholder_result("technical")

    # Run Content & Authority Audit
    print(f"[2/3] Running Content & Authority Audit...")
    try:
        from seo_content_authority import run_audit as run_content_audit
        results["audits"]["content"] = run_content_audit(
            target_url=target_url,
            primary_keywords=primary_keywords,
            competitor_urls=competitor_urls
        )
        print(f"      Content Score: {results['audits']['content'].get('score', 'N/A')}/100")
    except ImportError as e:
        results["warnings"].append(f"Content audit module not found: {e}")
        results["audits"]["content"] = create_placeholder_result("content")
    except Exception as e:
        results["errors"].append(f"Content audit failed: {e}")
        results["audits"]["content"] = create_placeholder_result("content")

    # Run AI Visibility Audit
    print(f"[3/3] Running AI Visibility Audit...")
    try:
        from ai_visibility_audit import run_audit as run_ai_audit
        results["audits"]["ai_visibility"] = run_ai_audit(
            brand_name=company_name,
            target_url=target_url,
            products_services=primary_keywords,
            competitor_names=[extract_domain(url) for url in (competitor_urls or [])],
            ground_truth=ground_truth
        )
        print(f"      AI Visibility Score: {results['audits']['ai_visibility'].get('score', 'N/A')}/100")
    except ImportError as e:
        results["warnings"].append(f"AI visibility audit module not found: {e}")
        results["audits"]["ai_visibility"] = create_placeholder_result("ai_visibility")
    except Exception as e:
        results["errors"].append(f"AI visibility audit failed: {e}")
        results["audits"]["ai_visibility"] = create_placeholder_result("ai_visibility")

    return results


def create_placeholder_result(audit_type: str) -> Dict[str, Any]:
    """
    Create a placeholder result when an audit fails.

    Args:
        audit_type: Type of audit that failed

    Returns:
        Dict with placeholder data
    """
    return {
        "score": 50,  # Neutral score
        "grade": "?",
        "components": {},
        "issues": [],
        "findings": ["Audit could not be completed"],
        "recommendations": [],
        "_placeholder": True
    }


def extract_domain(url: str) -> str:
    """Extract domain name from URL for competitor comparison."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def collect_all_issues(audit_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collect and deduplicate all issues from all audits.

    Args:
        audit_results: Combined audit results

    Returns:
        List of all issues sorted by severity
    """
    all_issues = []

    audits = audit_results.get("audits", {})

    for audit_name, audit_data in audits.items():
        if not audit_data:
            continue

        # Get issues from main audit
        for issue in audit_data.get("issues", []):
            issue_copy = issue.copy()
            issue_copy["source"] = audit_name
            all_issues.append(issue_copy)

        # Get issues from components
        for comp_name, comp_data in audit_data.get("components", {}).items():
            if isinstance(comp_data, dict):
                for issue in comp_data.get("issues", []):
                    issue_copy = issue.copy()
                    issue_copy["source"] = f"{audit_name}/{comp_name}"
                    all_issues.append(issue_copy)

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 99))

    return all_issues


def collect_all_recommendations(audit_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collect all recommendations from all audits.

    Args:
        audit_results: Combined audit results

    Returns:
        List of recommendations sorted by priority
    """
    all_recs = []

    audits = audit_results.get("audits", {})

    for audit_name, audit_data in audits.items():
        if not audit_data:
            continue

        for rec in audit_data.get("recommendations", []):
            rec_copy = rec.copy()
            rec_copy["source"] = audit_name
            all_recs.append(rec_copy)

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_recs.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))

    return all_recs


def identify_quick_wins(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify quick wins (high impact, low effort).

    Args:
        recommendations: All recommendations

    Returns:
        List of quick win recommendations
    """
    quick_wins = []

    for rec in recommendations:
        impact = rec.get("impact", "medium")
        effort = rec.get("effort", "medium")

        if impact in ["high", "medium"] and effort == "low":
            quick_wins.append(rec)

    return quick_wins[:10]  # Top 10 quick wins


def identify_critical_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify critical issues that need immediate attention.

    Args:
        issues: All issues

    Returns:
        List of critical issues
    """
    critical = []

    for issue in issues:
        if issue.get("severity") in ["critical", "high"]:
            critical.append(issue)

    return critical[:10]  # Top 10 critical issues


__all__ = [
    'run_full_audit',
    'create_placeholder_result',
    'extract_domain',
    'collect_all_issues',
    'collect_all_recommendations',
    'identify_quick_wins',
    'identify_critical_issues'
]
