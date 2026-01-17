"""
Check Phone Number Optimization

Analyze phone number placement, click-to-call functionality, and visibility.
For trades: Phone number placement matters more than backlinks.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PhoneIssue:
    """A phone-related issue found during analysis."""
    severity: str  # critical, high, medium, low
    description: str
    recommendation: str
    impact_estimate: str = ""


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


def extract_phone_numbers(html: str) -> List[Dict[str, Any]]:
    """
    Extract all phone numbers from HTML content.

    Args:
        html: HTML content

    Returns:
        List of dicts with phone number details
    """
    phone_numbers = []

    # Common US phone number patterns
    patterns = [
        # Standard formats: (123) 456-7890, 123-456-7890, 123.456.7890
        r'(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
        # tel: links
        r'href=["\']tel:([^"\']+)["\']',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, html, re.IGNORECASE)
        for match in matches:
            if 'tel:' in pattern:
                phone = match.group(1)
            else:
                phone = f"({match.group(1)}) {match.group(2)}-{match.group(3)}"

            # Clean the phone number
            phone_clean = re.sub(r'[^\d+]', '', phone)

            if len(phone_clean) >= 10:  # Valid US phone
                phone_numbers.append({
                    "raw": match.group(0),
                    "formatted": phone,
                    "clean": phone_clean,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                })

    # Deduplicate by clean number
    seen = set()
    unique = []
    for p in phone_numbers:
        if p["clean"] not in seen:
            seen.add(p["clean"])
            unique.append(p)

    return unique


def check_click_to_call(html: str) -> Dict[str, Any]:
    """
    Check if phone numbers have click-to-call (tel:) links.

    Args:
        html: HTML content

    Returns:
        Dict with click-to-call analysis
    """
    result = {
        "has_click_to_call": False,
        "click_to_call_count": 0,
        "phone_numbers_found": 0,
        "unlinked_phones": [],
        "linked_phones": [],
        "score": 0,
        "max": 2,
        "issues": [],
        "findings": [],
    }

    # Find all phone numbers
    all_phones = extract_phone_numbers(html)
    result["phone_numbers_found"] = len(all_phones)

    if not all_phones:
        result["issues"].append({
            "severity": "high",
            "description": "No phone numbers found on page",
            "recommendation": "Add a prominent phone number to increase call conversions",
            "impact_estimate": "Missing phone number can reduce calls by 30-50%"
        })
        return result

    # Check for tel: links
    tel_pattern = r'<a[^>]*href=["\']tel:([^"\']+)["\'][^>]*>([^<]*)</a>'
    tel_matches = re.findall(tel_pattern, html, re.IGNORECASE | re.DOTALL)

    result["click_to_call_count"] = len(tel_matches)
    result["has_click_to_call"] = len(tel_matches) > 0

    # Track which phones are linked
    linked_numbers = set()
    for tel_href, tel_text in tel_matches:
        clean = re.sub(r'[^\d+]', '', tel_href)
        linked_numbers.add(clean)
        result["linked_phones"].append({
            "href": tel_href,
            "text": tel_text.strip(),
            "clean": clean,
        })

    # Find unlinked phones
    for phone in all_phones:
        if phone["clean"] not in linked_numbers:
            result["unlinked_phones"].append(phone)

    # Calculate score
    if result["has_click_to_call"]:
        result["score"] = 2
        result["findings"].append(f"Found {result['click_to_call_count']} click-to-call link(s)")
    else:
        result["score"] = 0
        result["issues"].append({
            "severity": "critical",
            "description": "Phone number is not click-to-call on mobile",
            "recommendation": "Wrap phone numbers in tel: links: <a href=\"tel:+1234567890\">",
            "impact_estimate": "You're losing 15-25% of potential calls when users have to manually dial"
        })

    if result["unlinked_phones"]:
        result["issues"].append({
            "severity": "medium",
            "description": f"{len(result['unlinked_phones'])} phone number(s) without click-to-call",
            "recommendation": "Convert all phone numbers to clickable links",
            "impact_estimate": ""
        })

    return result


def check_phone_placement(html: str) -> Dict[str, Any]:
    """
    Check phone number placement (header, above fold, footer).

    Args:
        html: HTML content

    Returns:
        Dict with placement analysis
    """
    result = {
        "phone_in_header": False,
        "phone_above_fold_mobile": False,
        "phone_in_footer": False,
        "phone_visible_all_pages": False,  # Can't determine from single page
        "score": 0,
        "max": 3,
        "issues": [],
        "findings": [],
    }

    html_lower = html.lower()

    # Extract phone numbers
    phones = extract_phone_numbers(html)
    if not phones:
        result["issues"].append({
            "severity": "high",
            "description": "No phone numbers found to analyze placement",
            "recommendation": "Add phone number to header for visibility",
            "impact_estimate": ""
        })
        return result

    # Check header placement
    # Look for phone in <header> or common header classes/IDs
    header_patterns = [
        r'<header[^>]*>.*?</header>',
        r'<div[^>]*(?:class|id)=["\'][^"\']*header[^"\']*["\'][^>]*>.*?</div>',
        r'<nav[^>]*>.*?</nav>',
    ]

    for pattern in header_patterns:
        header_match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if header_match:
            header_html = header_match.group(0)
            header_phones = extract_phone_numbers(header_html)
            if header_phones:
                result["phone_in_header"] = True
                result["findings"].append("Phone number found in header/navigation")
                break

    # Check above fold (approximate by checking first 2000 chars after <body>)
    body_match = re.search(r'<body[^>]*>(.*)', html, re.IGNORECASE | re.DOTALL)
    if body_match:
        above_fold = body_match.group(1)[:3000]  # Approximate above fold
        above_fold_phones = extract_phone_numbers(above_fold)
        if above_fold_phones:
            result["phone_above_fold_mobile"] = True
            result["findings"].append("Phone number appears above the fold")

    # Check footer placement
    footer_patterns = [
        r'<footer[^>]*>.*?</footer>',
        r'<div[^>]*(?:class|id)=["\'][^"\']*footer[^"\']*["\'][^>]*>.*?</div>',
    ]

    for pattern in footer_patterns:
        footer_match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if footer_match:
            footer_html = footer_match.group(0)
            footer_phones = extract_phone_numbers(footer_html)
            if footer_phones:
                result["phone_in_footer"] = True
                result["findings"].append("Phone number found in footer")
                break

    # Calculate score
    if result["phone_in_header"]:
        result["score"] += 1
    else:
        result["issues"].append({
            "severity": "high",
            "description": "Phone number not in header",
            "recommendation": "Add phone number to site header for visibility on all pages",
            "impact_estimate": "Header phone visibility can increase calls by 10-15%"
        })

    if result["phone_above_fold_mobile"]:
        result["score"] += 2
    else:
        result["issues"].append({
            "severity": "critical",
            "description": "Phone number not visible above fold on mobile",
            "recommendation": "Move phone number above the fold for mobile visitors",
            "impact_estimate": "Mobile users who have to scroll may call competitors instead"
        })

    return result


def check_phone_formatting(html: str) -> Dict[str, Any]:
    """
    Check phone number formatting and accessibility.

    Args:
        html: HTML content

    Returns:
        Dict with formatting analysis
    """
    result = {
        "consistent_formatting": True,
        "has_area_code": True,
        "has_international_format": False,
        "formats_found": [],
        "score": 0,
        "max": 1,
        "issues": [],
        "findings": [],
    }

    phones = extract_phone_numbers(html)
    if not phones:
        return result

    # Track different formats
    formats = set()
    for phone in phones:
        # Detect format type
        raw = phone["raw"]
        if re.match(r'\(\d{3}\)', raw):
            formats.add("parentheses")
        elif re.match(r'\d{3}-\d{3}', raw):
            formats.add("dashes")
        elif re.match(r'\d{3}\.\d{3}', raw):
            formats.add("dots")
        elif re.match(r'\+1', raw):
            result["has_international_format"] = True
            formats.add("international")

    result["formats_found"] = list(formats)
    result["consistent_formatting"] = len(formats) <= 1

    if len(formats) > 1:
        result["issues"].append({
            "severity": "low",
            "description": f"Inconsistent phone formatting: {', '.join(formats)}",
            "recommendation": "Use consistent phone number format across the site",
            "impact_estimate": ""
        })
    else:
        result["score"] = 1
        result["findings"].append("Phone number formatting is consistent")

    return result


def analyze_phone_optimization(url: str) -> Dict[str, Any]:
    """
    Complete phone optimization analysis for a website.

    Args:
        url: Website URL to analyze

    Returns:
        Dict with complete phone analysis (0-6 score)
    """
    result = {
        "score": 0,
        "max": 6,
        "phone_click_to_call": False,
        "phone_above_fold_mobile": False,
        "phone_in_header": False,
        "phone_numbers": [],
        "click_to_call": {},
        "placement": {},
        "formatting": {},
        "issues": [],
        "findings": [],
        "quick_wins": [],
    }

    # Fetch homepage
    html = fetch_page(url)
    if not html:
        result["issues"].append({
            "severity": "high",
            "description": "Could not fetch homepage for phone analysis",
            "recommendation": "Ensure site is accessible",
            "impact_estimate": ""
        })
        return result

    # Extract phone numbers
    result["phone_numbers"] = extract_phone_numbers(html)

    # Check click-to-call
    result["click_to_call"] = check_click_to_call(html)
    result["phone_click_to_call"] = result["click_to_call"]["has_click_to_call"]
    result["score"] += result["click_to_call"]["score"]
    result["issues"].extend(result["click_to_call"].get("issues", []))
    result["findings"].extend(result["click_to_call"].get("findings", []))

    # Check placement
    result["placement"] = check_phone_placement(html)
    result["phone_above_fold_mobile"] = result["placement"]["phone_above_fold_mobile"]
    result["phone_in_header"] = result["placement"]["phone_in_header"]
    result["score"] += result["placement"]["score"]
    result["issues"].extend(result["placement"].get("issues", []))
    result["findings"].extend(result["placement"].get("findings", []))

    # Check formatting
    result["formatting"] = check_phone_formatting(html)
    result["score"] += result["formatting"]["score"]
    result["issues"].extend(result["formatting"].get("issues", []))
    result["findings"].extend(result["formatting"].get("findings", []))

    # Generate quick wins
    if not result["phone_click_to_call"]:
        result["quick_wins"].append({
            "title": "Add click-to-call links",
            "description": "You're likely losing 15-25% of potential calls because your phone number isn't click-to-call on mobile.",
            "effort": "low",
            "impact": "high",
            "implementation": "Wrap phone numbers with: <a href=\"tel:+1234567890\">123-456-7890</a>",
        })

    if not result["phone_above_fold_mobile"]:
        result["quick_wins"].append({
            "title": "Move phone number above fold",
            "description": "Mobile visitors need to see your phone number without scrolling. Emergency calls go to whoever's visible first.",
            "effort": "low",
            "impact": "high",
            "implementation": "Add phone number to header or hero section",
        })

    if not result["phone_in_header"]:
        result["quick_wins"].append({
            "title": "Add phone to header",
            "description": "Header phone numbers are visible on every page, making it easy for customers to call from anywhere on your site.",
            "effort": "low",
            "impact": "medium",
            "implementation": "Add phone number to site header, visible on all pages",
        })

    return result


__all__ = [
    'PhoneIssue',
    'extract_phone_numbers',
    'check_click_to_call',
    'check_phone_placement',
    'check_phone_formatting',
    'analyze_phone_optimization',
]
