"""
Check Analytics and Tracking Setup

Analyze GA4, conversion tracking, and phone click tracking.
"""

import re
from typing import Dict, Any, List, Optional


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


def check_ga4_installed(html: str) -> Dict[str, Any]:
    """
    Check if Google Analytics 4 is installed.

    Args:
        html: HTML content

    Returns:
        Dict with GA4 analysis
    """
    result = {
        "ga4_installed": False,
        "ga4_id": None,
        "gtag_installed": False,
        "gtm_installed": False,
        "gtm_id": None,
        "score": 0,
        "max": 2,
        "issues": [],
        "findings": [],
    }

    # Check for GA4 (G-XXXXXXXX format)
    ga4_pattern = r'(?:gtag|config)[^\w]*(G-[A-Z0-9]+)'
    ga4_match = re.search(ga4_pattern, html, re.IGNORECASE)
    if ga4_match:
        result["ga4_installed"] = True
        result["ga4_id"] = ga4_match.group(1)
        result["score"] = 2
        result["findings"].append(f"GA4 installed (ID: {result['ga4_id']})")

    # Check for gtag.js
    if 'gtag.js' in html or 'googletagmanager.com/gtag' in html:
        result["gtag_installed"] = True
        if not result["ga4_installed"]:
            result["findings"].append("Google gtag.js found")
            result["score"] = 1

    # Check for Google Tag Manager
    gtm_pattern = r'GTM-[A-Z0-9]+'
    gtm_match = re.search(gtm_pattern, html, re.IGNORECASE)
    if gtm_match:
        result["gtm_installed"] = True
        result["gtm_id"] = gtm_match.group(0)
        result["findings"].append(f"Google Tag Manager installed (ID: {result['gtm_id']})")
        if not result["ga4_installed"]:
            result["score"] = 1  # GTM might have GA4 configured inside

    # Check for Universal Analytics (old) - warn about deprecation
    ua_pattern = r'UA-\d+-\d+'
    if re.search(ua_pattern, html):
        result["issues"].append({
            "severity": "medium",
            "description": "Universal Analytics (UA) detected - this is deprecated",
            "recommendation": "Migrate to Google Analytics 4 (GA4) for continued data collection",
            "impact_estimate": ""
        })

    if not result["ga4_installed"] and not result["gtm_installed"]:
        result["issues"].append({
            "severity": "high",
            "description": "Google Analytics 4 not detected",
            "recommendation": "Install GA4 to track website performance and conversions",
            "impact_estimate": "Without analytics, you can't measure what's working"
        })

    return result


def check_phone_click_tracking(html: str) -> Dict[str, Any]:
    """
    Check if phone number clicks are being tracked.

    Args:
        html: HTML content

    Returns:
        Dict with phone tracking analysis
    """
    result = {
        "phone_click_tracking": False,
        "tracking_method": None,
        "score": 0,
        "max": 1,
        "issues": [],
        "findings": [],
    }

    # Check for tel: link tracking (various methods)
    tracking_patterns = [
        # GA4 event tracking on tel links
        (r'gtag\s*\(\s*["\']event["\'].*?["\']click["\'].*?tel:', "GA4 event tracking"),
        (r'onclick.*?gtag.*?tel:', "GA4 onclick tracking"),
        (r'onclick.*?ga\s*\(.*?tel:', "GA onclick tracking"),
        # Generic event listeners on phone links
        (r'addEventListener.*?["\']click["\'].*?tel:', "Event listener tracking"),
        # Data attributes for tracking
        (r'data-(?:ga|gtm|track).*?tel:', "Data attribute tracking"),
        # Common phone tracking scripts
        (r'CallTrack|CallRail|WhatConverts|PhoneWagon', "Third-party call tracking"),
    ]

    for pattern, method in tracking_patterns:
        if re.search(pattern, html, re.IGNORECASE | re.DOTALL):
            result["phone_click_tracking"] = True
            result["tracking_method"] = method
            result["score"] = 1
            result["findings"].append(f"Phone click tracking found: {method}")
            break

    if not result["phone_click_tracking"]:
        # Check if there are tel: links at all
        if 'href="tel:' in html.lower() or "href='tel:" in html.lower():
            result["issues"].append({
                "severity": "medium",
                "description": "Phone numbers are clickable but clicks are not being tracked",
                "recommendation": "Add event tracking to tel: links to measure call conversions",
                "impact_estimate": "Phone call tracking helps measure which pages drive calls"
            })
        else:
            result["issues"].append({
                "severity": "high",
                "description": "No phone click tracking (no tel: links found)",
                "recommendation": "Add clickable phone numbers and track clicks",
                "impact_estimate": ""
            })

    return result


def check_conversion_tracking(html: str) -> Dict[str, Any]:
    """
    Check for conversion tracking setup.

    Args:
        html: HTML content

    Returns:
        Dict with conversion tracking analysis
    """
    result = {
        "has_conversion_tracking": False,
        "conversion_pixels": [],
        "score": 0,
        "max": 1,
        "issues": [],
        "findings": [],
    }

    # Check for various conversion tracking pixels
    conversion_patterns = [
        # Google Ads conversion
        (r'googleadservices\.com/pagead/conversion', "Google Ads"),
        (r'gtag.*?AW-[0-9]+', "Google Ads (gtag)"),
        # Facebook Pixel
        (r'connect\.facebook\.net.*?fbevents\.js', "Facebook Pixel"),
        (r'fbq\s*\(\s*["\']init', "Facebook Pixel"),
        # LinkedIn Insight
        (r'snap\.licdn\.com/li\.lms-analytics', "LinkedIn Insight"),
        # Microsoft/Bing UET
        (r'bat\.bing\.com/bat\.js', "Microsoft/Bing UET"),
        # Generic conversion tracking
        (r'conversion[_-]?tracking', "Generic conversion tracking"),
    ]

    for pattern, pixel_name in conversion_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["has_conversion_tracking"] = True
            result["conversion_pixels"].append(pixel_name)

    if result["conversion_pixels"]:
        result["score"] = 1
        result["findings"].append(f"Conversion tracking: {', '.join(result['conversion_pixels'])}")
    else:
        result["issues"].append({
            "severity": "medium",
            "description": "No advertising conversion tracking detected",
            "recommendation": "If running ads, install conversion tracking to measure ROI",
            "impact_estimate": ""
        })

    return result


def check_form_tracking(html: str) -> Dict[str, Any]:
    """
    Check if form submissions are being tracked.

    Args:
        html: HTML content

    Returns:
        Dict with form tracking analysis
    """
    result = {
        "form_tracking": False,
        "tracking_method": None,
        "score": 0,
        "max": 1,
        "issues": [],
        "findings": [],
    }

    # Check for form submission tracking
    tracking_patterns = [
        # GA4 form tracking
        (r'gtag\s*\(\s*["\']event["\'].*?["\'](?:form|submit|lead)', "GA4 form event"),
        (r'onsubmit.*?gtag', "GA4 onsubmit tracking"),
        # Standard event listeners
        (r'addEventListener.*?["\']submit["\']', "Form submit listener"),
        # Data attributes
        (r'data-(?:ga|gtm|track).*?form', "Data attribute tracking"),
        # Thank you page redirect (often indicates tracking)
        (r'action=["\'][^"\']*thank', "Thank you page redirect"),
    ]

    for pattern, method in tracking_patterns:
        if re.search(pattern, html, re.IGNORECASE | re.DOTALL):
            result["form_tracking"] = True
            result["tracking_method"] = method
            result["score"] = 1
            result["findings"].append(f"Form tracking found: {method}")
            break

    if not result["form_tracking"]:
        # Check if there are forms at all
        if '<form' in html.lower():
            result["issues"].append({
                "severity": "medium",
                "description": "Forms found but submissions may not be tracked",
                "recommendation": "Add form submission tracking to measure lead generation",
                "impact_estimate": "Form tracking helps identify which pages generate leads"
            })

    return result


def analyze_tracking_setup(url: str) -> Dict[str, Any]:
    """
    Complete tracking setup analysis for a website.

    Args:
        url: Website URL to analyze

    Returns:
        Dict with complete tracking analysis (0-5 score)
    """
    result = {
        "score": 0,
        "max": 5,
        "ga4_installed": False,
        "phone_click_tracking": False,
        "analytics": {},
        "phone_tracking": {},
        "conversion_tracking": {},
        "form_tracking": {},
        "issues": [],
        "findings": [],
        "quick_wins": [],
    }

    # Fetch homepage
    html = fetch_page(url)
    if not html:
        result["issues"].append({
            "severity": "high",
            "description": "Could not fetch homepage for tracking analysis",
            "recommendation": "Ensure site is accessible",
            "impact_estimate": ""
        })
        return result

    # Check GA4
    result["analytics"] = check_ga4_installed(html)
    result["ga4_installed"] = result["analytics"]["ga4_installed"]
    result["score"] += result["analytics"]["score"]
    result["issues"].extend(result["analytics"].get("issues", []))
    result["findings"].extend(result["analytics"].get("findings", []))

    # Check phone tracking
    result["phone_tracking"] = check_phone_click_tracking(html)
    result["phone_click_tracking"] = result["phone_tracking"]["phone_click_tracking"]
    result["score"] += result["phone_tracking"]["score"]
    result["issues"].extend(result["phone_tracking"].get("issues", []))
    result["findings"].extend(result["phone_tracking"].get("findings", []))

    # Check conversion tracking
    result["conversion_tracking"] = check_conversion_tracking(html)
    result["score"] += result["conversion_tracking"]["score"]
    result["issues"].extend(result["conversion_tracking"].get("issues", []))
    result["findings"].extend(result["conversion_tracking"].get("findings", []))

    # Check form tracking
    result["form_tracking"] = check_form_tracking(html)
    result["score"] += result["form_tracking"]["score"]
    result["issues"].extend(result["form_tracking"].get("issues", []))
    result["findings"].extend(result["form_tracking"].get("findings", []))

    # Generate quick wins
    if not result["ga4_installed"]:
        result["quick_wins"].append({
            "title": "Install Google Analytics 4",
            "description": "You can't improve what you don't measure. GA4 is free and essential.",
            "effort": "low",
            "impact": "high",
            "implementation": "Create GA4 property and add tracking code to site header",
        })

    if not result["phone_click_tracking"] and 'tel:' in html.lower():
        result["quick_wins"].append({
            "title": "Track phone clicks",
            "description": "Know which pages are driving phone calls.",
            "effort": "low",
            "impact": "medium",
            "implementation": "Add gtag event tracking to tel: links",
        })

    return result


__all__ = [
    'check_ga4_installed',
    'check_phone_click_tracking',
    'check_conversion_tracking',
    'check_form_tracking',
    'analyze_tracking_setup',
]
