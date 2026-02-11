"""
SEO Content & Authority Audit

Comprehensive content quality and authority analysis including E-E-A-T signals,
topical coverage, and link profile evaluation.
"""

import logging
import os
from datetime import datetime
from typing import Any, Optional

import requests

from .scripts.analyze_content import analyze_page_content, assess_content_quality
from .scripts.analyze_links import analyze_internal_links
from .scripts.check_eeat import analyze_eeat_signals
from .scripts.map_topics import analyze_topical_coverage
from .scripts.score_backlinks import analyze_backlink_profile, estimate_backlink_health

__version__ = "1.0.0"

logger = logging.getLogger(__name__)


def run_audit(
    target_url: str,
    primary_keywords: list[str],
    competitor_urls: Optional[list[str]] = None,
    crawl_depth: int = 30
) -> dict[str, Any]:
    """
    Run a complete content and authority audit.

    Args:
        target_url: Root domain to audit
        primary_keywords: 5-10 target keywords/topics
        competitor_urls: Optional competitor URLs for comparison
        crawl_depth: Number of pages to crawl

    Returns:
        Dict with complete audit results including:
        - score: Overall Authority Score (0-100)
        - grade: Letter grade (A-F)
        - components: Detailed scores per component
        - content_gaps: Identified content opportunities
        - recommendations: Prioritized action items
    """
    results = {
        "url": target_url,
        "timestamp": datetime.now().isoformat(),
        "score": 0,
        "grade": "F",
        "components": {},
        "content_gaps": [],
        "topic_opportunities": [],
        "recommendations": []
    }

    # Component 1: Content Quality (25 points)
    # Analyze sample pages
    import re
    from urllib.parse import urljoin, urlparse

    from .scripts.analyze_content import fetch_page

    # File extensions to skip (not content pages)
    SKIP_EXTENSIONS = {
        '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
        '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.zip', '.xml', '.json',
        '.mp3', '.mp4', '.avi', '.mov', '.webm', '.wav'
    }

    def is_content_url(url: str) -> bool:
        """Check if URL is likely a content page (not asset)."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        # Skip if has file extension that's not HTML
        if '.' in path.split('/')[-1]:
            ext = '.' + path.split('.')[-1]
            if ext in SKIP_EXTENSIONS:
                return False
        # Skip common asset paths
        if any(x in path for x in ['/wp-content/themes/', '/wp-content/plugins/',
                                    '/assets/', '/static/', '/dist/', '/build/']):
            return False
        return True

    # Crawl to find pages
    html = fetch_page(target_url)
    pages_to_analyze = [target_url]

    if html:
        # Extract internal links
        link_pattern = r'href=["\']([^"\']+)["\']'
        links = re.findall(link_pattern, html, re.IGNORECASE)
        parsed_base = urlparse(target_url)

        for link in links[:crawl_depth]:
            full_url = urljoin(target_url, link)
            parsed = urlparse(full_url)
            if parsed.netloc == parsed_base.netloc:
                if full_url not in pages_to_analyze and is_content_url(full_url):
                    pages_to_analyze.append(full_url)

    # Analyze pages
    page_analyses = []
    for page_url in pages_to_analyze[:20]:  # Limit for performance
        page_analysis = analyze_page_content(page_url)
        page_analyses.append(page_analysis)

    content_result = assess_content_quality(page_analyses)
    results["components"]["content_quality"] = {
        "score": content_result["score"],
        "max": content_result["max"],
        "data_source": "real_api",
        "avg_word_count": content_result.get("avg_word_count", 0),
        "thin_content_pages": content_result.get("thin_content_pages", 0),
        "issues": content_result.get("issues", []),
        "findings": content_result.get("findings", [])
    }

    # Component 2: E-E-A-T (20 points)
    eeat_result = analyze_eeat_signals(target_url)
    results["components"]["eeat"] = {
        "score": eeat_result["score"],
        "max": eeat_result["max"],
        "data_source": "real_api",
        "has_authors": eeat_result.get("authors", {}).get("has_authors", False),
        "has_about_page": eeat_result.get("about_page", {}).get("has_about_page", False),
        "issues": eeat_result.get("issues", []),
        "findings": eeat_result.get("findings", [])
    }

    # Component 3: Keyword Position (15 points)
    # Requires real ranking API (DataForSEO or Google Search Console) for data.
    # When no API key is configured, returns None (excluded from scoring).
    keyword_result = _check_keyword_rankings(target_url, primary_keywords)
    results["components"]["keyword_position"] = keyword_result

    # Component 4: Topical Authority (15 points)
    topic_result = analyze_topical_coverage(target_url, primary_keywords, crawl_depth)
    results["components"]["topical_authority"] = {
        "score": topic_result["score"],
        "max": topic_result["max"],
        "data_source": "real_api",
        "topics_covered": topic_result.get("topics_covered", 0),
        "clusters": topic_result.get("clusters", []),
        "issues": topic_result.get("issues", []),
        "findings": topic_result.get("findings", [])
    }

    # Store content gaps
    results["content_gaps"] = topic_result.get("content_gaps", [])

    # Component 5: Backlink Quality (15 points)
    # Uses real API data (Moz/Ahrefs/SEMrush) when key is available.
    # Falls back to heuristic estimation, never returns fake neutral score.
    backlink_result = analyze_backlink_profile(target_url)

    if backlink_result.get("score") is None and backlink_result.get("data_source") == "unavailable":
        # No API key — try heuristic estimation as last resort
        backlink_result = estimate_backlink_health(target_url)

    results["components"]["backlinks"] = {
        "score": backlink_result["score"],
        "max": backlink_result["max"],
        "data_source": backlink_result.get("data_source", "unknown"),
        "estimated": backlink_result.get("estimated", False),
        "issues": backlink_result.get("issues", []),
        "findings": backlink_result.get("findings", [])
    }

    # Component 6: Internal Linking (10 points)
    link_result = analyze_internal_links(target_url, crawl_depth)
    results["components"]["internal_links"] = {
        "score": link_result["score"],
        "max": link_result["max"],
        "data_source": "real_api",
        "orphan_pages": len(link_result.get("orphan_pages", [])),
        "total_links": link_result.get("total_links", 0),
        "issues": link_result.get("issues", []),
        "findings": link_result.get("findings", [])
    }

    # Calculate total score, skipping components with None (unavailable data)
    available_scores = [
        comp["score"] for comp in results["components"].values()
        if comp["score"] is not None
    ]
    available_max = [
        comp["max"] for comp in results["components"].values()
        if comp["score"] is not None
    ]
    unavailable_components = [
        name for name, comp in results["components"].items()
        if comp["score"] is None
    ]

    if available_scores and available_max:
        # Normalize: scale available scores to 100-point range
        raw_total = sum(available_scores)
        raw_max = sum(available_max)
        total_score = round((raw_total / raw_max) * 100) if raw_max > 0 else 0
    else:
        total_score = 0

    results["score"] = total_score
    results["max"] = 100

    if unavailable_components:
        results["unavailable_components"] = unavailable_components
        results["score_note"] = (
            f"Score based on {len(available_scores)} of "
            f"{len(results['components'])} components. "
            f"Unavailable: {', '.join(unavailable_components)}"
        )

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

    # Generate recommendations
    results["recommendations"] = generate_recommendations(results)

    return results


def _check_keyword_rankings(
    target_url: str,
    primary_keywords: list[str]
) -> dict[str, Any]:
    """
    Check keyword rankings using DataForSEO API or Google Search Console.

    When no API key is available, returns score=None with data_source="unavailable"
    instead of a fake neutral score.

    Args:
        target_url: Site URL to check rankings for
        primary_keywords: Keywords to check positions for

    Returns:
        Dict with keyword ranking data (0-15 score, or None if unavailable)
    """
    # Try DataForSEO first
    dataforseo_login = os.environ.get("DATAFORSEO_LOGIN")
    dataforseo_password = os.environ.get("DATAFORSEO_PASSWORD")

    if dataforseo_login and dataforseo_password:
        try:
            return _check_rankings_dataforseo(
                target_url, primary_keywords, dataforseo_login, dataforseo_password
            )
        except Exception as e:
            logger.warning(f"DataForSEO ranking check failed: {e}")

    # No ranking API available — return honest unavailable
    return {
        "score": None,
        "max": 15,
        "data_source": "unavailable",
        "rankings": {},
        "issues": [{
            "severity": "medium",
            "category": "keyword_position",
            "description": "Keyword ranking data unavailable — no ranking API configured",
            "recommendation": (
                "Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD for real ranking data"
            )
        }],
        "findings": [
            "Keyword ranking data requires external API (DataForSEO or Google Search Console)",
            "This component is excluded from scoring until real data is available"
        ]
    }


def _check_rankings_dataforseo(
    target_url: str,
    keywords: list[str],
    login: str,
    password: str
) -> dict[str, Any]:
    """
    Check keyword rankings using DataForSEO SERP API.

    Args:
        target_url: Site URL
        keywords: Keywords to check
        login: DataForSEO login
        password: DataForSEO password

    Returns:
        Dict with real ranking data and score
    """
    from urllib.parse import urlparse

    domain = urlparse(target_url).netloc

    # DataForSEO SERP API
    api_url = "https://api.dataforseo.com/v3/serp/google/organic/live/regular"

    rankings = {}
    total_position_score = 0
    keywords_checked = 0

    for keyword in keywords[:10]:  # Limit to control costs (~$0.002 per query)
        payload = [{
            "keyword": keyword,
            "location_code": 2840,  # US
            "language_code": "en",
            "depth": 100
        }]

        try:
            response = requests.post(
                api_url,
                json=payload,
                auth=(login, password),
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()

            tasks = data.get("tasks", [])
            if not tasks or not tasks[0].get("result"):
                continue

            items = tasks[0]["result"][0].get("items", [])
            position = None

            for item in items:
                item_domain = item.get("domain", "")
                if domain in item_domain or item_domain in domain:
                    position = item.get("rank_group")
                    break

            rankings[keyword] = {
                "position": position,
                "found": position is not None
            }

            if position is not None:
                keywords_checked += 1
                # Score contribution: top 3 = 3pts, top 10 = 2pts, top 20 = 1pt, else 0
                if position <= 3:
                    total_position_score += 3
                elif position <= 10:
                    total_position_score += 2
                elif position <= 20:
                    total_position_score += 1
            else:
                keywords_checked += 1
                # Not found in top 100 = 0 pts

        except (requests.RequestException, KeyError, IndexError) as e:
            logger.warning(f"DataForSEO check for '{keyword}' failed: {e}")
            continue

    if keywords_checked == 0:
        return {
            "score": None,
            "max": 15,
            "data_source": "real_api",
            "api_provider": "dataforseo",
            "rankings": rankings,
            "issues": [{
                "severity": "medium",
                "category": "keyword_position",
                "description": "Could not retrieve ranking data from DataForSEO",
                "recommendation": "Verify DataForSEO credentials and API access"
            }],
            "findings": ["DataForSEO API returned no usable ranking data"]
        }

    # Normalize: max possible is 3 pts * keywords_checked, scale to 15
    max_possible = 3 * keywords_checked
    score = round((total_position_score / max_possible) * 15) if max_possible > 0 else 0

    # Build findings
    findings = [f"Checked rankings for {keywords_checked} keywords via DataForSEO"]
    ranked_keywords = [k for k, v in rankings.items() if v.get("found")]
    unranked = [k for k, v in rankings.items() if not v.get("found")]

    if ranked_keywords:
        findings.append(f"Ranking for {len(ranked_keywords)} keywords in top 100")
    if unranked:
        findings.append(f"Not found in top 100 for: {', '.join(unranked[:5])}")

    issues = []
    if unranked:
        issues.append({
            "severity": "high" if len(unranked) > len(ranked_keywords) else "medium",
            "category": "keyword_position",
            "description": (
                f"Not ranking in top 100 for {len(unranked)} of "
                f"{keywords_checked} target keywords"
            ),
            "recommendation": "Create targeted content for unranked keywords"
        })

    return {
        "score": score,
        "max": 15,
        "data_source": "real_api",
        "api_provider": "dataforseo",
        "rankings": rankings,
        "keywords_checked": keywords_checked,
        "issues": issues,
        "findings": findings
    }


def generate_recommendations(results: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate prioritized recommendations based on audit results."""
    recommendations = []

    components = results.get("components", {})

    # Content quality recommendations
    content = components.get("content_quality", {})
    if content.get("thin_content_pages", 0) > 0:
        recommendations.append({
            "priority": "high",
            "category": "content_quality",
            "action": f"Expand thin content ({content['thin_content_pages']} pages)",
            "details": "Pages with <500 words should be expanded to 1000+ words",
            "impact": "high",
            "effort": "medium"
        })

    if content.get("score", 0) < 15:
        recommendations.append({
            "priority": "high",
            "category": "content_quality",
            "action": "Improve content quality",
            "details": "Add more comprehensive, media-rich content",
            "impact": "high",
            "effort": "high"
        })

    # E-E-A-T recommendations
    eeat = components.get("eeat", {})
    if not eeat.get("has_authors"):
        recommendations.append({
            "priority": "high",
            "category": "eeat",
            "action": "Add author attribution",
            "details": "Add author names and link to author bio pages with credentials",
            "impact": "high",
            "effort": "low"
        })

    if not eeat.get("has_about_page"):
        recommendations.append({
            "priority": "high",
            "category": "eeat",
            "action": "Create comprehensive About page",
            "details": "Add company history, team info, and credentials",
            "impact": "high",
            "effort": "low"
        })

    if eeat.get("score", 0) < 12:
        recommendations.append({
            "priority": "medium",
            "category": "eeat",
            "action": "Strengthen trust signals",
            "details": "Add testimonials, certifications, and social proof",
            "impact": "medium",
            "effort": "medium"
        })

    # Topical authority recommendations
    topics = components.get("topical_authority", {})
    if topics.get("topics_covered", 0) < len(results.get("content_gaps", [])):
        for gap in results.get("content_gaps", [])[:3]:
            recommendations.append({
                "priority": gap.get("priority", "medium"),
                "category": "topical_authority",
                "action": gap.get("recommendation", "Create content"),
                "details": f"Topic: {gap.get('topic', 'Unknown')}",
                "impact": "high",
                "effort": "high"
            })

    # Internal linking recommendations
    links = components.get("internal_links", {})
    if links.get("orphan_pages", 0) > 0:
        recommendations.append({
            "priority": "medium",
            "category": "internal_links",
            "action": f"Link orphan pages ({links['orphan_pages']} pages)",
            "details": "Add internal links to pages with no incoming links",
            "impact": "medium",
            "effort": "low"
        })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))

    return recommendations[:10]


def format_report(results: dict[str, Any]) -> str:
    """Format audit results as a readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("CONTENT & AUTHORITY AUDIT REPORT")
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

    if results.get("content_gaps"):
        lines.append("\n" + "-" * 60)
        lines.append("CONTENT GAPS")
        lines.append("-" * 60)
        for gap in results["content_gaps"][:5]:
            lines.append(f"\n  [{gap.get('priority', 'medium').upper()}] {gap.get('topic', 'Unknown')}")
            lines.append(f"  {gap.get('recommendation', '')}")

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
    'analyze_page_content',
    'assess_content_quality',
    'analyze_eeat_signals',
    'analyze_topical_coverage',
    'analyze_internal_links',
    'analyze_backlink_profile'
]
