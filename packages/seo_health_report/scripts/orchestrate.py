"""
Orchestrate Full Audit

Main workflow controller that runs all sub-audits and coordinates results.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Setup paths for package imports
_project_root = Path(__file__).resolve().parents[3]  # packages/seo_health_report/scripts -> root
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from packages.seo_health_report.scripts.logger import get_logger

logger = get_logger(__name__)


async def run_browser_crawl(target_url: str) -> Optional[dict[str, Any]]:
    """
    Run browser-based crawl to get rendered DOM data.

    Returns SEO data extracted from fully-rendered JavaScript pages.
    """
    try:
        from packages.seo_health_report.providers.browser_crawler import BrowserCrawler

        logger.info(f"[0/3] Running Browser Crawl for {target_url}...")

        async with BrowserCrawler(headless=True) as crawler:
            data = await crawler.crawl_page(target_url)

        if data.error:
            logger.warning(f"Browser crawl error: {data.error}")
            return None

        return {
            "title": data.title,
            "meta_description": data.meta_description,
            "meta_robots": data.meta_robots,
            "canonical_url": data.canonical_url,
            "h1_tags": data.h1_tags,
            "h2_tags": data.h2_tags,
            "og_title": data.og_title,
            "og_description": data.og_description,
            "og_image": data.og_image,
            "schema_json": data.schema_json,
            "internal_links": len(data.internal_links),
            "external_links": len(data.external_links),
            "images_total": data.total_images,
            "images_without_alt": data.images_without_alt,
            "page_load_time_ms": data.page_load_time_ms,
            "html_size_bytes": data.html_size_bytes,
        }
    except ImportError:
        logger.warning("Browser crawler not available (playwright not installed)")
        return None
    except Exception as e:
        logger.warning(f"Browser crawl failed: {e}")
        return None


async def run_full_audit(
    target_url: str,
    company_name: str,
    primary_keywords: list[str],
    competitor_urls: Optional[list[str]] = None,
    ground_truth: Optional[dict[str, Any]] = None,
    rate_limiter: Optional[Any] = None,
    tier: str = "medium",
) -> dict[str, Any]:
    """
    Run all three audits and compile results.

    Args:
        target_url: Root domain to audit
        company_name: Company name for AI queries
        primary_keywords: Target keywords
        competitor_urls: Optional competitor URLs
        ground_truth: Optional facts for accuracy checking
        rate_limiter: Optional RateLimiter instance for throttling HTTP requests
        tier: Report tier level (low, medium, high)

    Returns:
        Dict with all audit results
    """
    results = {
        "url": target_url,
        "company_name": company_name,
        "tier": tier,
        "timestamp": datetime.now().isoformat(),
        "audits": {"technical": None, "content": None, "ai_visibility": None},
        "browser_data": None,
        "warnings": [],
        "errors": [],
    }

    _rate_limiter = rate_limiter

    # Run browser crawl first to get rendered DOM data
    browser_data = await run_browser_crawl(target_url)
    if browser_data:
        results["browser_data"] = browser_data
        logger.info(f"      Browser Crawl: {browser_data.get('page_load_time_ms', 0):.0f}ms load time, {browser_data.get('images_total', 0)} images")

    async def run_technical():
        logger.info(f"[1/3] Running Technical Audit for {target_url}...")
        try:
            import packages.seo_technical_audit as seo_technical_audit
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
        logger.info("[2/3] Running Content & Authority Audit...")
        try:
            import packages.seo_content_authority as seo_content_authority
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
        logger.info("[3/3] Running AI Visibility Audit...")
        try:
            import packages.ai_visibility_audit as ai_visibility_audit
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


def handle_audit_failure(audit_type: str, error_message: str) -> dict[str, Any]:
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


def collect_all_issues(audit_results: dict[str, Any]) -> list[dict[str, Any]]:
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


def collect_all_recommendations(audit_results: dict[str, Any]) -> list[dict[str, Any]]:
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


def identify_quick_wins(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def identify_critical_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
    primary_keywords: list[str],
    competitor_urls: Optional[list[str]] = None,
    ground_truth: Optional[dict[str, Any]] = None,
    rate_limiter: Optional[Any] = None,
) -> dict[str, Any]:
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
            rate_limiter=rate_limiter,
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
