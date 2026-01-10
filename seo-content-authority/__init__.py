"""
SEO Content & Authority Audit

Comprehensive content quality and authority analysis including E-E-A-T signals,
topical coverage, and link profile evaluation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .scripts.analyze_content import analyze_page_content, assess_content_quality
from .scripts.check_eeat import analyze_eeat_signals
from .scripts.map_topics import analyze_topical_coverage
from .scripts.analyze_links import analyze_internal_links
from .scripts.score_backlinks import analyze_backlink_profile, estimate_backlink_health


__version__ = "1.0.0"


def run_audit(
    target_url: str,
    primary_keywords: List[str],
    competitor_urls: Optional[List[str]] = None,
    crawl_depth: int = 30
) -> Dict[str, Any]:
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
    from .scripts.analyze_content import fetch_page
    import re
    from urllib.parse import urlparse, urljoin

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
                if full_url not in pages_to_analyze:
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
        "has_authors": eeat_result.get("authors", {}).get("has_authors", False),
        "has_about_page": eeat_result.get("about_page", {}).get("has_about_page", False),
        "issues": eeat_result.get("issues", []),
        "findings": eeat_result.get("findings", [])
    }

    # Component 3: Keyword Position (15 points)
    # Without ranking API, score based on keyword optimization
    keyword_score = 7  # Neutral without ranking data
    results["components"]["keyword_position"] = {
        "score": keyword_score,
        "max": 15,
        "note": "Requires ranking API for full analysis",
        "issues": [],
        "findings": ["Keyword ranking data requires external API"]
    }

    # Component 4: Topical Authority (15 points)
    topic_result = analyze_topical_coverage(target_url, primary_keywords, crawl_depth)
    results["components"]["topical_authority"] = {
        "score": topic_result["score"],
        "max": topic_result["max"],
        "topics_covered": topic_result.get("topics_covered", 0),
        "clusters": topic_result.get("clusters", []),
        "issues": topic_result.get("issues", []),
        "findings": topic_result.get("findings", [])
    }

    # Store content gaps
    results["content_gaps"] = topic_result.get("content_gaps", [])

    # Component 5: Backlink Quality (15 points)
    backlink_result = analyze_backlink_profile(target_url)

    if backlink_result.get("score") == 0 or "error" in backlink_result:
        # Fall back to estimation
        backlink_result = estimate_backlink_health(target_url)

    results["components"]["backlinks"] = {
        "score": backlink_result["score"],
        "max": backlink_result["max"],
        "estimated": backlink_result.get("estimated", False),
        "issues": backlink_result.get("issues", []),
        "findings": backlink_result.get("findings", [])
    }

    # Component 6: Internal Linking (10 points)
    link_result = analyze_internal_links(target_url, crawl_depth)
    results["components"]["internal_links"] = {
        "score": link_result["score"],
        "max": link_result["max"],
        "orphan_pages": len(link_result.get("orphan_pages", [])),
        "total_links": link_result.get("total_links", 0),
        "issues": link_result.get("issues", []),
        "findings": link_result.get("findings", [])
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

    # Generate recommendations
    results["recommendations"] = generate_recommendations(results)

    return results


def generate_recommendations(results: Dict[str, Any]) -> List[Dict[str, Any]]:
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


def format_report(results: Dict[str, Any]) -> str:
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
