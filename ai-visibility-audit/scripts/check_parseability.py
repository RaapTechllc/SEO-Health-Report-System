"""
Check LLM Parseability

Analyze website structure for LLM consumption - semantic HTML, structured data,
clean content extraction.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import json


@dataclass
class ParseabilityIssue:
    """An issue affecting LLM parseability."""
    category: str
    description: str
    severity: str  # "critical", "high", "medium", "low"
    element: Optional[str] = None
    recommendation: str = ""


def fetch_page(url: str, timeout: int = 30) -> Optional[str]:
    """
    Fetch a web page's HTML content.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content or None if fetch failed
    """
    try:
        import requests

        headers = {
            'User-Agent': 'SEO-Health-Report-Bot/1.0 (AI Visibility Audit)'
        }

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text

    except ImportError:
        print("Warning: requests package not installed. Run: pip install requests")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def check_semantic_html(html: str) -> Dict[str, Any]:
    """
    Check for proper semantic HTML structure.

    Args:
        html: HTML content to analyze

    Returns:
        Dict with score, findings, and issues
    """
    issues: List[ParseabilityIssue] = []
    findings = []
    score = 15  # Start with max, deduct for issues

    # Check for semantic elements
    semantic_elements = {
        '<header': 'header',
        '<nav': 'nav',
        '<main': 'main',
        '<article': 'article',
        '<section': 'section',
        '<aside': 'aside',
        '<footer': 'footer'
    }

    found_semantic = []
    for tag, name in semantic_elements.items():
        if tag in html.lower():
            found_semantic.append(name)

    if len(found_semantic) >= 5:
        findings.append(f"Good: Uses semantic elements: {', '.join(found_semantic)}")
    elif len(found_semantic) >= 3:
        findings.append(f"Fair: Uses some semantic elements: {', '.join(found_semantic)}")
        score -= 2
    else:
        findings.append(f"Poor: Limited semantic HTML (only: {', '.join(found_semantic) or 'none'})")
        issues.append(ParseabilityIssue(
            category="semantic_html",
            description="Missing semantic HTML elements",
            severity="medium",
            recommendation="Add <main>, <article>, <section>, <nav>, <header>, <footer> elements"
        ))
        score -= 5

    # Check heading hierarchy
    h1_count = len(re.findall(r'<h1[^>]*>', html, re.IGNORECASE))
    h2_count = len(re.findall(r'<h2[^>]*>', html, re.IGNORECASE))
    h3_count = len(re.findall(r'<h3[^>]*>', html, re.IGNORECASE))

    if h1_count == 1:
        findings.append("Good: Single H1 tag (proper hierarchy)")
    elif h1_count == 0:
        findings.append("Issue: No H1 tag found")
        issues.append(ParseabilityIssue(
            category="heading_hierarchy",
            description="Missing H1 tag",
            severity="high",
            recommendation="Add a single H1 tag for the main page title"
        ))
        score -= 3
    else:
        findings.append(f"Issue: Multiple H1 tags ({h1_count})")
        issues.append(ParseabilityIssue(
            category="heading_hierarchy",
            description=f"Multiple H1 tags ({h1_count})",
            severity="medium",
            recommendation="Use only one H1 tag per page"
        ))
        score -= 2

    if h2_count > 0 and h3_count > 0:
        findings.append(f"Good: Proper heading hierarchy (H2: {h2_count}, H3: {h3_count})")
    elif h2_count > 0:
        findings.append(f"Fair: Has H2 tags ({h2_count}) but no H3")
    else:
        findings.append("Issue: Missing subheading structure")
        score -= 2

    # Check for excessive div nesting (makes parsing harder)
    div_count = html.lower().count('<div')
    semantic_count = len(found_semantic)

    if div_count > 0 and semantic_count > 0:
        ratio = div_count / (semantic_count + 1)
        if ratio > 20:
            findings.append(f"Warning: Heavy div usage ({div_count} divs) - consider more semantic markup")
            issues.append(ParseabilityIssue(
                category="div_soup",
                description=f"Excessive div elements ({div_count})",
                severity="low",
                recommendation="Replace generic divs with semantic elements where appropriate"
            ))
            score -= 1

    return {
        "score": max(0, score),
        "max": 15,
        "findings": findings,
        "issues": [
            {
                "category": i.category,
                "description": i.description,
                "severity": i.severity,
                "recommendation": i.recommendation
            }
            for i in issues
        ]
    }


def check_structured_data(html: str) -> Dict[str, Any]:
    """
    Check for structured data (JSON-LD, microdata, RDFa).

    Args:
        html: HTML content to analyze

    Returns:
        Dict with findings about structured data presence
    """
    findings = []
    structured_data = []
    score_bonus = 0

    # Check for JSON-LD
    json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    json_ld_matches = re.findall(json_ld_pattern, html, re.DOTALL | re.IGNORECASE)

    if json_ld_matches:
        findings.append(f"Found {len(json_ld_matches)} JSON-LD block(s)")
        score_bonus += 3

        for match in json_ld_matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict):
                    schema_type = data.get('@type', 'Unknown')
                    structured_data.append({"format": "JSON-LD", "type": schema_type})
                    findings.append(f"  - JSON-LD: {schema_type}")
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_type = item.get('@type', 'Unknown')
                            structured_data.append({"format": "JSON-LD", "type": schema_type})
                            findings.append(f"  - JSON-LD: {schema_type}")
            except json.JSONDecodeError:
                findings.append("  - JSON-LD: Parse error (invalid JSON)")

    # Check for microdata
    itemscope_count = len(re.findall(r'itemscope', html, re.IGNORECASE))
    if itemscope_count > 0:
        findings.append(f"Found {itemscope_count} microdata itemscope attribute(s)")
        score_bonus += 2

        # Try to extract itemtype
        itemtype_matches = re.findall(r'itemtype=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for itemtype in itemtype_matches[:5]:  # Limit to 5
            structured_data.append({"format": "Microdata", "type": itemtype})
            findings.append(f"  - Microdata: {itemtype}")

    # Check for RDFa
    vocab_count = len(re.findall(r'vocab=', html, re.IGNORECASE))
    typeof_count = len(re.findall(r'typeof=', html, re.IGNORECASE))

    if vocab_count > 0 or typeof_count > 0:
        findings.append(f"Found RDFa markup (vocab: {vocab_count}, typeof: {typeof_count})")
        score_bonus += 1

    if not structured_data:
        findings.append("No structured data found - this limits AI understanding")
        findings.append("Recommendation: Add JSON-LD schema for Organization, Product, FAQ, etc.")

    # Check for common important schemas
    important_schemas = ['Organization', 'LocalBusiness', 'Product', 'Article', 'FAQPage', 'HowTo']
    found_important = [sd['type'] for sd in structured_data if any(s in sd['type'] for s in important_schemas)]

    if found_important:
        findings.append(f"Key schemas present: {', '.join(set(found_important))}")
    else:
        findings.append("Missing key schemas (Organization, Product, FAQ, etc.)")

    return {
        "score_bonus": min(5, score_bonus),  # Cap bonus at 5
        "findings": findings,
        "structured_data": structured_data,
        "has_json_ld": len(json_ld_matches) > 0,
        "has_microdata": itemscope_count > 0,
        "has_rdfa": vocab_count > 0 or typeof_count > 0
    }


def check_content_extraction(html: str) -> Dict[str, Any]:
    """
    Check how easily content can be extracted from the page.

    Args:
        html: HTML content to analyze

    Returns:
        Dict with content extraction analysis
    """
    findings = []
    issues = []
    score = 0

    # Check meta description
    meta_desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if not meta_desc:
        meta_desc = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)

    if meta_desc:
        desc_length = len(meta_desc.group(1))
        if 120 <= desc_length <= 160:
            findings.append(f"Good: Meta description present ({desc_length} chars)")
            score += 2
        else:
            findings.append(f"Fair: Meta description present but suboptimal length ({desc_length} chars)")
            score += 1
    else:
        findings.append("Missing: No meta description")
        issues.append("Add meta description for AI snippet extraction")

    # Check title tag
    title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    if title_match:
        title_length = len(title_match.group(1))
        if 30 <= title_length <= 60:
            findings.append(f"Good: Title tag present ({title_length} chars)")
            score += 2
        else:
            findings.append(f"Fair: Title present but length could be optimized ({title_length} chars)")
            score += 1
    else:
        findings.append("Missing: No title tag")
        issues.append("Add title tag")

    # Check for readable content (text to HTML ratio)
    # Remove scripts and styles
    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)

    # Extract text
    text = re.sub(r'<[^>]+>', ' ', clean_html)
    text = re.sub(r'\s+', ' ', text).strip()

    text_length = len(text)
    html_length = len(html)

    if html_length > 0:
        text_ratio = text_length / html_length
        if text_ratio > 0.3:
            findings.append(f"Good: High text-to-HTML ratio ({text_ratio:.1%})")
            score += 2
        elif text_ratio > 0.15:
            findings.append(f"Fair: Moderate text-to-HTML ratio ({text_ratio:.1%})")
            score += 1
        else:
            findings.append(f"Poor: Low text-to-HTML ratio ({text_ratio:.1%}) - heavy markup or JS-dependent content")
            issues.append("Increase visible text content, reduce markup bloat")

    # Check for images with alt text
    img_tags = re.findall(r'<img[^>]+>', html, re.IGNORECASE)
    imgs_with_alt = len([img for img in img_tags if 'alt=' in img.lower()])

    if img_tags:
        alt_ratio = imgs_with_alt / len(img_tags)
        if alt_ratio >= 0.9:
            findings.append(f"Good: {imgs_with_alt}/{len(img_tags)} images have alt text")
            score += 1
        else:
            findings.append(f"Issue: Only {imgs_with_alt}/{len(img_tags)} images have alt text")
            issues.append("Add alt text to all images")

    return {
        "score": score,
        "max": 7,
        "findings": findings,
        "issues": issues,
        "details": {
            "has_meta_description": meta_desc is not None,
            "has_title": title_match is not None,
            "text_length": text_length,
            "text_ratio": text_length / html_length if html_length > 0 else 0,
            "image_count": len(img_tags),
            "images_with_alt": imgs_with_alt
        }
    }


def check_javascript_dependency(html: str) -> Dict[str, Any]:
    """
    Check if content requires JavaScript to render (bad for LLMs).

    Args:
        html: HTML content to analyze

    Returns:
        Dict with JS dependency analysis
    """
    findings = []
    issues = []
    score = 3  # Start with max, deduct for issues

    # Check for SPA frameworks
    spa_indicators = [
        ('react', r'react|__NEXT_DATA__|_next'),
        ('vue', r'vue|__VUE__|nuxt'),
        ('angular', r'ng-app|angular|ng-version'),
        ('svelte', r'svelte'),
    ]

    detected_frameworks = []
    for name, pattern in spa_indicators:
        if re.search(pattern, html, re.IGNORECASE):
            detected_frameworks.append(name)

    if detected_frameworks:
        findings.append(f"Detected JS framework(s): {', '.join(detected_frameworks)}")

        # Check if there's actual content or just JS shell
        # Remove script tags and check remaining content
        clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', clean_html)
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) < 500:
            findings.append("WARNING: Very little server-rendered content - may be JS-dependent")
            issues.append("Implement Server-Side Rendering (SSR) for AI accessibility")
            score -= 3
        elif len(text) < 2000:
            findings.append("Moderate server-rendered content - some content may require JS")
            score -= 1
        else:
            findings.append("Good: Substantial content renders without JS (SSR working)")
    else:
        findings.append("No SPA framework detected - content likely server-rendered")

    # Check for noscript content
    noscript_match = re.search(r'<noscript[^>]*>(.*?)</noscript>', html, flags=re.DOTALL | re.IGNORECASE)
    if noscript_match:
        noscript_content = noscript_match.group(1)
        if len(noscript_content) > 100:
            findings.append("Good: Has meaningful noscript fallback content")
        else:
            findings.append("Has noscript tag but minimal content")

    return {
        "score": max(0, score),
        "max": 3,
        "findings": findings,
        "issues": issues,
        "details": {
            "detected_frameworks": detected_frameworks,
            "has_noscript": noscript_match is not None
        }
    }


def analyze_site_structure(url: str) -> Dict[str, Any]:
    """
    Main function to analyze a website's LLM parseability.

    Args:
        url: URL to analyze

    Returns:
        Dict with complete parseability analysis including score
    """
    html = fetch_page(url)

    if not html:
        return {
            "score": 0,
            "max": 15,
            "findings": [f"Could not fetch {url}"],
            "issues": [],
            "error": "Failed to fetch page"
        }

    # Run all checks
    semantic_result = check_semantic_html(html)
    structured_data_result = check_structured_data(html)
    content_result = check_content_extraction(html)
    js_result = check_javascript_dependency(html)

    # Combine findings
    all_findings = []
    all_findings.extend(semantic_result["findings"])
    all_findings.extend(structured_data_result["findings"])
    all_findings.extend(content_result["findings"])
    all_findings.extend(js_result["findings"])

    # Combine issues
    all_issues = []
    all_issues.extend(semantic_result.get("issues", []))
    all_issues.extend(content_result.get("issues", []))
    all_issues.extend(js_result.get("issues", []))

    # Calculate total score (0-15)
    base_score = (
        semantic_result["score"] * 0.4 +  # 40% weight
        content_result["score"] / content_result["max"] * 15 * 0.3 +  # 30% weight
        js_result["score"] / js_result["max"] * 15 * 0.3  # 30% weight
    )

    # Add structured data bonus
    total_score = min(15, base_score + structured_data_result["score_bonus"])

    return {
        "score": round(total_score),
        "max": 15,
        "findings": all_findings,
        "issues": all_issues,
        "details": {
            "semantic_html": semantic_result,
            "structured_data": structured_data_result,
            "content_extraction": content_result,
            "js_dependency": js_result
        }
    }


__all__ = [
    'ParseabilityIssue',
    'fetch_page',
    'check_semantic_html',
    'check_structured_data',
    'check_content_extraction',
    'check_javascript_dependency',
    'analyze_site_structure'
]
