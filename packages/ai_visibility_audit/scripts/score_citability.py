"""
Score Citation Likelihood

Analyze website content for citation-worthy material that AI systems would reference.
"""

import re
from dataclasses import dataclass
from typing import Any, Optional

from .check_parseability import fetch_page


@dataclass
class CitableContent:
    """Content that could be cited by AI systems."""
    content_type: str  # "research", "statistics", "guide", "tool", "original"
    title: str
    url: str
    score: int  # 1-5 citation potential
    reason: str


def check_original_research(html: str, url: str) -> list[CitableContent]:
    """
    Check for original research, studies, and data.

    Args:
        html: HTML content
        url: Page URL

    Returns:
        List of citable research content found
    """
    citable = []

    # Patterns indicating original research
    research_patterns = [
        (r'(?:our|we|this)\s+(?:study|research|analysis|survey|report)\s+(?:found|shows|reveals|indicates)', 'research'),
        (r'(?:surveyed|analyzed|studied)\s+\d+[,\d]*\s+(?:people|users|customers|companies|respondents)', 'survey'),
        (r'(?:based on|according to)\s+(?:our|internal)\s+data', 'data'),
        (r'(?:original|proprietary|exclusive)\s+(?:data|research|findings)', 'original'),
    ]

    # Patterns indicating statistics
    stat_patterns = [
        (r'\d+(?:\.\d+)?%\s+of\s+(?:\w+\s+){1,3}(?:said|reported|indicated|prefer|use)', 'statistic'),
        (r'(?:increased|decreased|grew|dropped)\s+(?:by\s+)?\d+(?:\.\d+)?%', 'trend'),
        (r'\$\d+(?:[,\d]+)?(?:\.\d+)?\s*(?:billion|million|thousand|B|M|K)', 'financial'),
    ]

    html_lower = html.lower()

    for pattern, content_type in research_patterns:
        matches = re.findall(pattern, html_lower)
        if matches:
            citable.append(CitableContent(
                content_type=content_type,
                title=f"Original {content_type}",
                url=url,
                score=4,
                reason=f"Contains original {content_type} that AI would cite"
            ))
            break  # One match per category is enough

    stat_count = 0
    for pattern, _ in stat_patterns:
        stat_count += len(re.findall(pattern, html_lower))

    if stat_count >= 5:
        citable.append(CitableContent(
            content_type="statistics",
            title="Statistical data",
            url=url,
            score=4,
            reason=f"Contains {stat_count}+ statistics that AI systems reference"
        ))
    elif stat_count >= 2:
        citable.append(CitableContent(
            content_type="statistics",
            title="Statistical data",
            url=url,
            score=2,
            reason=f"Contains some statistics ({stat_count})"
        ))

    return citable


def check_comprehensive_guides(html: str, url: str) -> list[CitableContent]:
    """
    Check for comprehensive guides and definitive resources.

    Args:
        html: HTML content
        url: Page URL

    Returns:
        List of citable guide content found
    """
    citable = []

    # Check title patterns
    guide_title_patterns = [
        r'(?:complete|ultimate|definitive|comprehensive)\s+guide',
        r'everything\s+(?:you\s+need\s+to\s+know|about)',
        r'(?:\d+|how\s+to)[^<]*(?:guide|tutorial|tips)',
        r'(?:beginner|advanced|expert)[\'s]*\s+guide',
    ]

    html_lower = html.lower()

    for pattern in guide_title_patterns:
        if re.search(pattern, html_lower):
            citable.append(CitableContent(
                content_type="guide",
                title="Comprehensive guide",
                url=url,
                score=3,
                reason="Positioned as authoritative guide content"
            ))
            break

    # Check content depth (heading count, word count)
    h2_count = len(re.findall(r'<h2[^>]*>', html, re.IGNORECASE))
    len(re.findall(r'<h3[^>]*>', html, re.IGNORECASE))

    # Rough word count
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    word_count = len(text.split())

    if word_count > 3000 and h2_count >= 5:
        citable.append(CitableContent(
            content_type="guide",
            title="In-depth content",
            url=url,
            score=3,
            reason=f"Long-form content ({word_count} words, {h2_count} sections) - AI prefers comprehensive sources"
        ))

    return citable


def check_tools_and_resources(html: str, url: str) -> list[CitableContent]:
    """
    Check for tools, calculators, and interactive resources.

    Args:
        html: HTML content
        url: Page URL

    Returns:
        List of citable tool content found
    """
    citable = []

    # Check for interactive elements
    tool_patterns = [
        (r'<(?:form|input|select|button)[^>]*(?:calculator|tool|checker|analyzer|generator)', 'tool'),
        (r'(?:free|online)\s+(?:tool|calculator|checker|analyzer|generator)', 'tool'),
        (r'<canvas|<svg[^>]*chart|chart\.js|d3\.js', 'visualization'),
        (r'(?:template|worksheet|checklist)\s+(?:download|pdf|free)', 'template'),
    ]

    html_lower = html.lower()

    for pattern, content_type in tool_patterns:
        if re.search(pattern, html_lower):
            citable.append(CitableContent(
                content_type=content_type,
                title=f"Interactive {content_type}",
                url=url,
                score=4,
                reason=f"Contains interactive {content_type} - AI often references useful tools"
            ))
            break

    return citable


def check_expert_content(html: str, url: str) -> list[CitableContent]:
    """
    Check for expert-authored content with credentials.

    Args:
        html: HTML content
        url: Page URL

    Returns:
        List of citable expert content found
    """
    citable = []

    html_lower = html.lower()

    # Author credentials patterns
    credential_patterns = [
        r'(?:ph\.?d|m\.?d|j\.?d|cpa|cfa|mba)',
        r'(?:certified|licensed|registered)\s+(?:\w+\s+){1,2}(?:professional|expert|specialist)',
        r'(?:\d+\+?\s+)?years?\s+(?:of\s+)?experience',
        r'(?:professor|doctor|attorney|expert)\s+(?:at|of|in)',
    ]

    for pattern in credential_patterns:
        if re.search(pattern, html_lower):
            citable.append(CitableContent(
                content_type="expert",
                title="Expert-authored content",
                url=url,
                score=3,
                reason="Contains author credentials - increases AI trust signals"
            ))
            break

    # Check for citations/references
    citation_patterns = [
        r'(?:according\s+to|cited\s+by|referenced\s+in|source:|sources:)',
        r'\[\d+\]',  # Academic-style citations
        r'<(?:cite|blockquote)[^>]*>',
    ]

    citation_count = 0
    for pattern in citation_patterns:
        citation_count += len(re.findall(pattern, html_lower))

    if citation_count >= 3:
        citable.append(CitableContent(
            content_type="referenced",
            title="Well-cited content",
            url=url,
            score=2,
            reason=f"Contains {citation_count}+ citations - shows research rigor"
        ))

    return citable


def check_unique_perspectives(html: str, url: str) -> list[CitableContent]:
    """
    Check for unique perspectives, case studies, and original insights.

    Args:
        html: HTML content
        url: Page URL

    Returns:
        List of citable unique content found
    """
    citable = []

    html_lower = html.lower()

    # Case study patterns
    case_study_patterns = [
        r'case\s+study',
        r'(?:real|actual|true)\s+(?:story|example|case)',
        r'(?:how|why)\s+\w+\s+(?:achieved|increased|reduced|improved)',
        r'(?:success|failure)\s+story',
    ]

    for pattern in case_study_patterns:
        if re.search(pattern, html_lower):
            citable.append(CitableContent(
                content_type="case_study",
                title="Case study",
                url=url,
                score=4,
                reason="Contains case study - AI cites real-world examples"
            ))
            break

    # Unique perspective patterns
    perspective_patterns = [
        r'(?:contrary|unlike|different\s+from)\s+(?:popular|common|conventional)',
        r'(?:myth|misconception|mistake)s?\s+(?:about|in)',
        r'(?:unpopular|controversial|surprising)\s+(?:opinion|take|view)',
    ]

    for pattern in perspective_patterns:
        if re.search(pattern, html_lower):
            citable.append(CitableContent(
                content_type="perspective",
                title="Unique perspective",
                url=url,
                score=3,
                reason="Contains contrarian or unique viewpoint - stands out to AI"
            ))
            break

    return citable


def analyze_content_citability(url: str) -> dict[str, Any]:
    """
    Analyze website content for citation likelihood.

    Args:
        url: URL to analyze

    Returns:
        Dict with citation likelihood analysis including score
    """
    html = fetch_page(url)

    if not html:
        return {
            "score": 0,
            "max": 15,
            "findings": [f"Could not fetch {url}"],
            "citable_content": [],
            "error": "Failed to fetch page"
        }

    # Run all checks
    citable_content: list[CitableContent] = []
    citable_content.extend(check_original_research(html, url))
    citable_content.extend(check_comprehensive_guides(html, url))
    citable_content.extend(check_tools_and_resources(html, url))
    citable_content.extend(check_expert_content(html, url))
    citable_content.extend(check_unique_perspectives(html, url))

    # Generate findings
    findings = []

    if citable_content:
        findings.append(f"Found {len(citable_content)} citable content types:")
        for content in citable_content:
            findings.append(f"  - {content.content_type}: {content.reason}")

        # Calculate score based on content found
        total_score = sum(c.score for c in citable_content)
        score = min(15, total_score)

        # Categorize by type
        content_types = {c.content_type for c in citable_content}

        if "research" in content_types or "statistics" in content_types:
            findings.append("STRENGTH: Original research/data - highly citable by AI")

        if "tool" in content_types:
            findings.append("STRENGTH: Interactive tools - AI references useful resources")

        if "case_study" in content_types:
            findings.append("STRENGTH: Case studies - AI cites real-world examples")

    else:
        score = 2  # Minimal score for having a website
        findings.append("No highly citable content detected")
        findings.append("Recommendations to improve citation likelihood:")
        findings.append("  - Add original research or survey data")
        findings.append("  - Create comprehensive 'ultimate guide' content")
        findings.append("  - Build interactive tools or calculators")
        findings.append("  - Publish case studies with specific results")
        findings.append("  - Include expert credentials and citations")

    # Additional recommendations based on what's missing
    content_types = {c.content_type for c in citable_content}
    missing_recommendations = []

    if "research" not in content_types and "statistics" not in content_types:
        missing_recommendations.append("Add original research, surveys, or proprietary data")

    if "guide" not in content_types:
        missing_recommendations.append("Create comprehensive 'complete guide' content (3000+ words)")

    if "tool" not in content_types:
        missing_recommendations.append("Build free tools, calculators, or templates")

    if "expert" not in content_types:
        missing_recommendations.append("Highlight author credentials and expertise")

    if missing_recommendations:
        findings.append("Opportunities to increase citation likelihood:")
        for rec in missing_recommendations:
            findings.append(f"  - {rec}")

    return {
        "score": score,
        "max": 15,
        "findings": findings,
        "citable_content": [
            {
                "content_type": c.content_type,
                "title": c.title,
                "url": c.url,
                "score": c.score,
                "reason": c.reason
            }
            for c in citable_content
        ],
        "details": {
            "content_types_found": list(content_types) if citable_content else [],
            "total_citable_items": len(citable_content),
            "recommendations": missing_recommendations
        }
    }


def analyze_site_citability(
    target_url: str,
    additional_pages: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Analyze entire site's citation likelihood across multiple pages.

    Args:
        target_url: Main URL to analyze
        additional_pages: Optional list of additional page URLs

    Returns:
        Dict with site-wide citation analysis
    """
    pages_to_check = [target_url]
    if additional_pages:
        pages_to_check.extend(additional_pages[:5])  # Limit to 5 additional

    all_citable: list[CitableContent] = []
    page_results = []

    for page_url in pages_to_check:
        result = analyze_content_citability(page_url)
        page_results.append({
            "url": page_url,
            "score": result["score"],
            "citable_count": len(result.get("citable_content", []))
        })
        all_citable.extend([
            CitableContent(**c) for c in result.get("citable_content", [])
        ])

    # Calculate overall score
    if page_results:
        avg_score = sum(p["score"] for p in page_results) / len(page_results)
        # Bonus for having citable content across multiple pages
        diversity_bonus = min(3, len({c.content_type for c in all_citable}))
        score = min(15, int(avg_score + diversity_bonus))
    else:
        score = 0

    return {
        "score": score,
        "max": 15,
        "page_results": page_results,
        "all_citable_content": [
            {
                "content_type": c.content_type,
                "title": c.title,
                "url": c.url,
                "score": c.score
            }
            for c in all_citable
        ],
        "content_type_distribution": {
            ct: sum(1 for c in all_citable if c.content_type == ct)
            for ct in {c.content_type for c in all_citable}
        }
    }


__all__ = [
    'CitableContent',
    'check_original_research',
    'check_comprehensive_guides',
    'check_tools_and_resources',
    'check_expert_content',
    'check_unique_perspectives',
    'analyze_content_citability',
    'analyze_site_citability'
]
