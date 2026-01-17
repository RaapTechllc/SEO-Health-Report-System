"""
Check CTA (Call-to-Action) Optimization

Analyze CTA placement, clarity, and effectiveness for lead generation.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CTAElement:
    """A CTA element found on the page."""
    text: str
    type: str  # button, link, form_submit
    classes: str
    href: Optional[str]
    position: str  # header, hero, body, footer


def fetch_page(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch HTML content from URL."""
    try:
        import requests
        headers = {'User-Agent': 'SEO-Health-Report-Bot/1.0'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception:
        return None


# CTA text patterns (good vs weak)
STRONG_CTA_PATTERNS = [
    r'get\s+(?:a\s+)?(?:free\s+)?(?:quote|estimate|consultation)',
    r'(?:request|schedule)\s+(?:a\s+)?(?:quote|estimate|consultation|appointment|service)',
    r'call\s+(?:us\s+)?(?:now|today)',
    r'contact\s+us',
    r'get\s+started',
    r'book\s+(?:now|online|appointment)',
    r'free\s+(?:quote|estimate|consultation)',
]

WEAK_CTA_PATTERNS = [
    r'^submit$',
    r'^send$',
    r'^click\s+here$',
    r'^learn\s+more$',
    r'^more\s+info$',
]

# CTA button class patterns
CTA_CLASS_PATTERNS = [
    r'btn|button',
    r'cta',
    r'action',
    r'primary',
]


def extract_ctas(html: str) -> List[CTAElement]:
    """
    Extract CTAs from HTML content.

    Args:
        html: HTML content

    Returns:
        List of CTAElement objects
    """
    ctas = []

    # Find buttons
    button_patterns = [
        # <button> elements
        r'<button[^>]*(?:class=["\']([^"\']*)["\'])?[^>]*>([^<]*)</button>',
        # <input type="submit">
        r'<input[^>]*type=["\']submit["\'][^>]*value=["\']([^"\']*)["\'][^>]*>',
        # <a> with button classes
        r'<a[^>]*(?:class=["\']([^"\']*)["\'])[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>',
    ]

    # Extract buttons
    button_matches = re.findall(
        r'<button[^>]*>([^<]*)</button>',
        html,
        re.IGNORECASE | re.DOTALL
    )
    for match in button_matches:
        text = match.strip()
        if text:
            ctas.append(CTAElement(
                text=text,
                type="button",
                classes="",
                href=None,
                position="body"
            ))

    # Extract submit inputs
    submit_matches = re.findall(
        r'<input[^>]*type=["\']submit["\'][^>]*value=["\']([^"\']*)["\']',
        html,
        re.IGNORECASE
    )
    for match in submit_matches:
        text = match.strip()
        if text:
            ctas.append(CTAElement(
                text=text,
                type="form_submit",
                classes="",
                href=None,
                position="body"
            ))

    # Extract links with button-like classes
    link_pattern = r'<a[^>]*class=["\']([^"\']*(?:btn|button|cta)[^"\']*)["\'][^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>'
    link_matches = re.findall(link_pattern, html, re.IGNORECASE | re.DOTALL)
    for classes, href, text in link_matches:
        text = text.strip()
        if text:
            ctas.append(CTAElement(
                text=text,
                type="link",
                classes=classes,
                href=href,
                position="body"
            ))

    return ctas


def check_cta_clarity(ctas: List[CTAElement]) -> Dict[str, Any]:
    """
    Check CTA text clarity and effectiveness.

    Args:
        ctas: List of CTAElement objects

    Returns:
        Dict with clarity analysis
    """
    result = {
        "strong_ctas": [],
        "weak_ctas": [],
        "cta_text_clear": False,
        "score": 0,
        "max": 2,
        "issues": [],
        "findings": [],
    }

    if not ctas:
        result["issues"].append({
            "severity": "high",
            "description": "No CTAs found on page",
            "recommendation": "Add clear call-to-action buttons like 'Get a Free Quote'",
            "impact_estimate": "Missing CTAs can reduce conversions by 50%+"
        })
        return result

    for cta in ctas:
        text_lower = cta.text.lower().strip()

        # Check against strong patterns
        is_strong = any(
            re.search(pattern, text_lower)
            for pattern in STRONG_CTA_PATTERNS
        )

        # Check against weak patterns
        is_weak = any(
            re.search(pattern, text_lower)
            for pattern in WEAK_CTA_PATTERNS
        )

        if is_strong:
            result["strong_ctas"].append(cta.text)
        elif is_weak:
            result["weak_ctas"].append(cta.text)

    # Calculate score
    if result["strong_ctas"]:
        result["score"] = 2
        result["cta_text_clear"] = True
        result["findings"].append(f"Strong CTAs found: {', '.join(result['strong_ctas'][:3])}")
    elif ctas and not result["weak_ctas"]:
        result["score"] = 1
        result["cta_text_clear"] = True
        result["findings"].append("CTAs present with acceptable text")
    else:
        result["score"] = 0
        result["cta_text_clear"] = False

    if result["weak_ctas"]:
        result["issues"].append({
            "severity": "medium",
            "description": f"Weak CTA text found: {', '.join(result['weak_ctas'][:3])}",
            "recommendation": "Use action-oriented text like 'Get a Free Quote' instead of 'Submit'",
            "impact_estimate": "Clear CTAs can improve conversions by 10-20%"
        })

    return result


def check_cta_placement(html: str) -> Dict[str, Any]:
    """
    Check CTA placement on the page.

    Args:
        html: HTML content

    Returns:
        Dict with placement analysis
    """
    result = {
        "primary_cta_above_fold": False,
        "cta_in_header": False,
        "cta_in_hero": False,
        "multiple_ctas": False,
        "score": 0,
        "max": 2,
        "issues": [],
        "findings": [],
    }

    # Check above fold (first 3000 chars after body)
    body_match = re.search(r'<body[^>]*>(.*)', html, re.IGNORECASE | re.DOTALL)
    if body_match:
        above_fold = body_match.group(1)[:3000]
        above_fold_ctas = extract_ctas(above_fold)

        if above_fold_ctas:
            result["primary_cta_above_fold"] = True
            result["score"] += 2
            result["findings"].append("CTA found above the fold")

    # Check header
    header_patterns = [
        r'<header[^>]*>.*?</header>',
        r'<nav[^>]*>.*?</nav>',
    ]
    for pattern in header_patterns:
        header_match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if header_match:
            header_ctas = extract_ctas(header_match.group(0))
            if header_ctas:
                result["cta_in_header"] = True
                result["findings"].append("CTA found in header/navigation")
                break

    # Check hero section (common patterns)
    hero_patterns = [
        r'<(?:section|div)[^>]*class=["\'][^"\']*(?:hero|banner|jumbotron)[^"\']*["\'][^>]*>.*?</(?:section|div)>',
    ]
    for pattern in hero_patterns:
        hero_match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if hero_match:
            hero_ctas = extract_ctas(hero_match.group(0))
            if hero_ctas:
                result["cta_in_hero"] = True
                result["findings"].append("CTA found in hero section")
                break

    # Count total CTAs
    all_ctas = extract_ctas(html)
    result["multiple_ctas"] = len(all_ctas) > 1

    if not result["primary_cta_above_fold"]:
        result["issues"].append({
            "severity": "high",
            "description": "No CTA visible above the fold",
            "recommendation": "Add a primary CTA to your hero section or header",
            "impact_estimate": "Above-fold CTAs can increase conversions by 20-30%"
        })

    return result


def check_cta_styling(html: str) -> Dict[str, Any]:
    """
    Check CTA visual styling and prominence.

    Args:
        html: HTML content

    Returns:
        Dict with styling analysis
    """
    result = {
        "has_button_styling": False,
        "has_contrasting_color": False,  # Hard to determine without CSS
        "score": 0,
        "max": 1,
        "issues": [],
        "findings": [],
    }

    ctas = extract_ctas(html)

    # Check for button classes
    button_keywords = ['btn', 'button', 'cta', 'action', 'primary']
    for cta in ctas:
        if any(kw in cta.classes.lower() for kw in button_keywords):
            result["has_button_styling"] = True
            result["score"] = 1
            result["findings"].append("CTAs have button styling")
            break

    if not result["has_button_styling"] and ctas:
        result["issues"].append({
            "severity": "low",
            "description": "CTAs may lack prominent button styling",
            "recommendation": "Use contrasting button styles to make CTAs stand out",
            "impact_estimate": ""
        })

    return result


def analyze_cta_optimization(url: str) -> Dict[str, Any]:
    """
    Complete CTA optimization analysis for a website.

    Args:
        url: Website URL to analyze

    Returns:
        Dict with complete CTA analysis (0-5 score)
    """
    result = {
        "score": 0,
        "max": 5,
        "primary_cta_above_fold": False,
        "cta_text_clear": False,
        "ctas_found": [],
        "clarity": {},
        "placement": {},
        "styling": {},
        "issues": [],
        "findings": [],
        "quick_wins": [],
    }

    # Fetch homepage
    html = fetch_page(url)
    if not html:
        result["issues"].append({
            "severity": "high",
            "description": "Could not fetch homepage for CTA analysis",
            "recommendation": "Ensure site is accessible",
            "impact_estimate": ""
        })
        return result

    # Extract CTAs
    ctas = extract_ctas(html)
    result["ctas_found"] = [cta.text for cta in ctas]

    # Check clarity
    result["clarity"] = check_cta_clarity(ctas)
    result["cta_text_clear"] = result["clarity"]["cta_text_clear"]
    result["score"] += result["clarity"]["score"]
    result["issues"].extend(result["clarity"].get("issues", []))
    result["findings"].extend(result["clarity"].get("findings", []))

    # Check placement
    result["placement"] = check_cta_placement(html)
    result["primary_cta_above_fold"] = result["placement"]["primary_cta_above_fold"]
    result["score"] += result["placement"]["score"]
    result["issues"].extend(result["placement"].get("issues", []))
    result["findings"].extend(result["placement"].get("findings", []))

    # Check styling
    result["styling"] = check_cta_styling(html)
    result["score"] += result["styling"]["score"]
    result["issues"].extend(result["styling"].get("issues", []))
    result["findings"].extend(result["styling"].get("findings", []))

    # Generate quick wins
    if not result["primary_cta_above_fold"]:
        result["quick_wins"].append({
            "title": "Add above-fold CTA",
            "description": "Visitors shouldn't have to scroll to find how to contact you.",
            "effort": "low",
            "impact": "high",
            "implementation": "Add 'Get a Free Quote' button to hero section",
        })

    if result["clarity"]["weak_ctas"]:
        result["quick_wins"].append({
            "title": "Improve CTA text",
            "description": "Replace generic 'Submit' buttons with action-oriented text.",
            "effort": "low",
            "impact": "medium",
            "implementation": "Use text like 'Get Your Free Quote' or 'Schedule Service'",
        })

    return result


__all__ = [
    'CTAElement',
    'extract_ctas',
    'check_cta_clarity',
    'check_cta_placement',
    'check_cta_styling',
    'analyze_cta_optimization',
]
