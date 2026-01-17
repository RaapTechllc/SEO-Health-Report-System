"""
Orchestrate Full Audit

Main workflow controller that runs all sub-audits and coordinates results.
"""

import sys
import os
import asyncio
import importlib.util
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for sibling imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Register seo_health_report module so sub-modules can import from it
seo_health_report_path = os.path.join(project_root, "seo-health-report")
if seo_health_report_path not in sys.path:
    sys.path.insert(0, seo_health_report_path)

# Register as seo_health_report in sys.modules
if "seo_health_report" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "seo_health_report",
        os.path.join(seo_health_report_path, "__init__.py"),
        submodule_search_locations=[seo_health_report_path]
    )
    seo_health_report_module = importlib.util.module_from_spec(spec)
    sys.modules["seo_health_report"] = seo_health_report_module
    try:
        spec.loader.exec_module(seo_health_report_module)
    except Exception:
        pass  # Module may have circular imports, but we just need it registered

from .logger import get_logger


class AuditError(Exception):
    """Base exception for audit operations."""
    pass

class APIError(AuditError):
    """API-related errors."""
    pass

class ValidationError(AuditError):
    """Data validation errors."""
    pass

logger = get_logger(__name__)


async def run_full_audit(
    target_url: str,
    company_name: str,
    primary_keywords: List[str],
    competitor_urls: Optional[List[str]] = None,
    ground_truth: Optional[Dict[str, Any]] = None,
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
        "audits": {"technical": None, "content": None, "ai_visibility": None},
        "warnings": [],
        "errors": [],
    }

    async def run_technical():
        logger.info(f"[1/3] Running Technical Audit for {target_url}...")
        try:
            import importlib.util
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            module_path = os.path.join(project_root, "seo-technical-audit")
            
            # Add to sys.path for submodule imports
            if module_path not in sys.path:
                sys.path.insert(0, module_path)
            
            # Import from hyphenated folder
            spec = importlib.util.spec_from_file_location(
                "seo_technical_audit",
                os.path.join(module_path, "__init__.py"),
                submodule_search_locations=[module_path]
            )
            seo_technical_audit = importlib.util.module_from_spec(spec)
            sys.modules["seo_technical_audit"] = seo_technical_audit
            spec.loader.exec_module(seo_technical_audit)
            
            return await seo_technical_audit.run_audit(
                target_url=target_url, depth=50, competitor_urls=competitor_urls
            )
        except ImportError as e:
            results["warnings"].append(f"Technical audit module not found: {e}")
            return handle_audit_failure("technical", f"Module not found: {e}")
        except Exception as e:
            results["errors"].append(f"Technical audit failed: {e}")
            return handle_audit_failure("technical", str(e))

    async def run_content():
        logger.info(f"[2/3] Running Content & Authority Audit...")
        try:
            import importlib.util
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            module_path = os.path.join(project_root, "seo-content-authority")
            
            # Add to sys.path for submodule imports
            if module_path not in sys.path:
                sys.path.insert(0, module_path)
            
            # Import from hyphenated folder
            spec = importlib.util.spec_from_file_location(
                "seo_content_authority",
                os.path.join(module_path, "__init__.py"),
                submodule_search_locations=[module_path]
            )
            seo_content_authority = importlib.util.module_from_spec(spec)
            sys.modules["seo_content_authority"] = seo_content_authority
            spec.loader.exec_module(seo_content_authority)
            
            return seo_content_authority.run_audit(
                target_url=target_url,
                primary_keywords=primary_keywords,
                competitor_urls=competitor_urls,
            )
        except ImportError as e:
            results["warnings"].append(f"Content audit module not found: {e}")
            return handle_audit_failure("content", f"Module not found: {e}")
        except Exception as e:
            results["errors"].append(f"Content audit failed: {e}")
            return handle_audit_failure("content", str(e))

    async def run_ai():
        logger.info(f"[3/3] Running AI Visibility Audit...")
        try:
            import importlib.util
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            module_path = os.path.join(project_root, "ai-visibility-audit")
            
            # Add to sys.path for submodule imports
            if module_path not in sys.path:
                sys.path.insert(0, module_path)
            
            # Import from hyphenated folder
            spec = importlib.util.spec_from_file_location(
                "ai_visibility_audit",
                os.path.join(module_path, "__init__.py"),
                submodule_search_locations=[module_path]
            )
            ai_visibility_audit = importlib.util.module_from_spec(spec)
            sys.modules["ai_visibility_audit"] = ai_visibility_audit
            spec.loader.exec_module(ai_visibility_audit)
            
            return await ai_visibility_audit.run_audit(
                brand_name=company_name,
                target_url=target_url,
                products_services=primary_keywords,
                competitor_names=[
                    extract_domain(url) for url in (competitor_urls or [])
                ],
                ground_truth=ground_truth,
            )
        except ImportError as e:
            results["warnings"].append(f"AI visibility audit module not found: {e}")
            return handle_audit_failure("ai_visibility", f"Module not found: {e}")
        except Exception as e:
            results["errors"].append(f"AI visibility audit failed: {e}")
            return handle_audit_failure("ai_visibility", str(e))

    # Run all three audits in parallel
    audit_results = await asyncio.gather(
        run_technical(), run_content(), run_ai(), return_exceptions=True
    )

    results["audits"]["technical"] = audit_results[0]
    results["audits"]["content"] = audit_results[1]
    results["audits"]["ai_visibility"] = audit_results[2]

    # Log scores
    logger.info(
        f"      Technical Score: {results['audits']['technical'].get('score', 'N/A')}/100"
    )
    logger.info(
        f"      Content Score: {results['audits']['content'].get('score', 'N/A')}/100"
    )
    logger.info(
        f"      AI Visibility Score: {results['audits']['ai_visibility'].get('score', 'N/A')}/100"
    )

    return results


def handle_audit_failure(audit_type: str, error_message: str) -> Dict[str, Any]:
    """
    Handle audit failure with transparent error reporting.

    Args:
        audit_type: Type of audit that failed
        error_message: Specific error that occurred

    Returns:
        Dict with honest failure information
    """
    logger.warning(f"{audit_type} audit failed: {error_message}")
    
    return {
        "score": None,
        "grade": "N/A", 
        "status": "unavailable",
        "error_type": "system_unavailable",
        "message": f"{audit_type.title()} analysis temporarily unavailable",
        "reason": "Technical issue - manual analysis recommended",
        "components": {},
        "issues": [],
        "findings": [
            f"{audit_type.title()} audit could not be completed",
            "This does not affect other audit components",
            "Manual analysis available upon request"
        ],
        "recommendations": [
            f"Contact RaapTech for manual {audit_type} analysis",
            "Review available audit sections for actionable insights",
            "Schedule follow-up audit when systems restored"
        ],
        "next_steps": [
            "Focus on available audit results",
            "Contact support for detailed consultation", 
            "Request manual analysis for missing components"
        ]
    }


def extract_domain(url: str) -> str:
    """Extract domain name from URL for competitor comparison."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc
    # Remove port number if present
    if ":" in domain:
        domain = domain.split(":")[0]
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

    audits = audit_results.get("audits") or {}

    for audit_name, audit_data in audits.items():
        if not audit_data:
            continue

        # Get issues from main audit
        issues = audit_data.get("issues") or []
        for issue in issues:
            issue_copy = issue.copy()
            issue_copy["source"] = audit_name
            all_issues.append(issue_copy)

        # Get issues from components
        components = audit_data.get("components") or {}
        for comp_name, comp_data in components.items():
            if isinstance(comp_data, dict):
                comp_issues = comp_data.get("issues") or []
                for issue in comp_issues:
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

    audits = audit_results.get("audits") or {}

    for audit_name, audit_data in audits.items():
        if not audit_data:
            continue

        recs = audit_data.get("recommendations") or []
        for rec in recs:
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


def run_full_audit_sync(
    target_url: str,
    company_name: str,
    primary_keywords: List[str],
    competitor_urls: Optional[List[str]] = None,
    ground_truth: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Sync wrapper for run_full_audit for backwards compatibility.
    """
    return asyncio.run(
        run_full_audit(
            target_url=target_url,
            company_name=company_name,
            primary_keywords=primary_keywords,
            competitor_urls=competitor_urls,
            ground_truth=ground_truth,
        )
    )


__all__ = [
    "run_full_audit",
    "run_full_audit_sync", 
    "handle_audit_failure",
    "extract_domain",
    "collect_all_issues",
    "collect_all_recommendations",
    "identify_quick_wins",
    "identify_critical_issues",
]
