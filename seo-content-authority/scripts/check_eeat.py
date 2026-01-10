"""
Check E-E-A-T Signals

Analyze Experience, Expertise, Authoritativeness, and Trustworthiness signals.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin


@dataclass
class EEATIssue:
    """An E-E-A-T issue found during analysis."""
    severity: str
    category: str  # "experience", "expertise", "authority", "trust"
    description: str
    recommendation: str = ""


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


def check_author_pages(html: str, base_url: str) -> Dict[str, Any]:
    """
    Check for author pages and credentials.

    Args:
        html: HTML content
        base_url: Base URL for resolving relative links

    Returns:
        Dict with author page analysis
    """
    result = {
        "has_authors": False,
        "author_count": 0,
        "authors_with_bios": 0,
        "authors_with_credentials": 0,
        "author_links": [],
        "issues": [],
        "findings": []
    }

    # Look for author indicators
    author_patterns = [
        # Schema.org author
        (r'"author"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"', 'schema'),
        # Meta tag author
        (r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)', 'meta'),
        # Common author class patterns
        (r'class=["\'][^"\']*author[^"\']*["\'][^>]*>([^<]+)</(?:a|span|div)', 'class'),
        # "By [Author]" patterns
        (r'[Bb]y\s+<a[^>]+>([^<]+)</a>', 'byline'),
        (r'[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', 'byline_text'),
    ]

    authors_found = set()
    for pattern, source in author_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            author_name = match.strip()
            if len(author_name) > 2 and len(author_name) < 100:
                authors_found.add(author_name)

    result["author_count"] = len(authors_found)
    result["has_authors"] = len(authors_found) > 0

    if authors_found:
        result["findings"].append(f"Found {len(authors_found)} author(s)")
    else:
        result["issues"].append({
            "severity": "medium",
            "category": "expertise",
            "description": "No author attribution found",
            "recommendation": "Add author names and links to author bio pages"
        })

    # Look for author bio links
    author_link_patterns = [
        r'href=["\']([^"\']*(?:author|team|about)[^"\']*)["\']',
        r'href=["\']([^"\']*(?:\/about\/|\/team\/|\/author\/)[^"\']*)["\']',
    ]

    for pattern in author_link_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            full_url = urljoin(base_url, match)
            if full_url not in result["author_links"]:
                result["author_links"].append(full_url)

    # Check for credential indicators
    credential_patterns = [
        r'(?:Ph\.?D|M\.?D|J\.?D|MBA|CPA|CFA)',
        r'(?:\d+\+?\s+)?years?\s+(?:of\s+)?experience',
        r'certified|licensed|accredited',
        r'professor|doctor|attorney|expert',
    ]

    for pattern in credential_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["authors_with_credentials"] += 1
            break

    if result["authors_with_credentials"] > 0:
        result["findings"].append("Author credentials visible")
    elif result["has_authors"]:
        result["issues"].append({
            "severity": "low",
            "category": "expertise",
            "description": "No visible author credentials",
            "recommendation": "Add author qualifications, experience, and credentials"
        })

    return result


def check_about_page(base_url: str) -> Dict[str, Any]:
    """
    Check about page quality.

    Args:
        base_url: Base URL of the site

    Returns:
        Dict with about page analysis
    """
    result = {
        "has_about_page": False,
        "about_url": None,
        "has_company_info": False,
        "has_team_info": False,
        "has_history": False,
        "word_count": 0,
        "issues": [],
        "findings": []
    }

    # Try common about page URLs
    about_urls = [
        "/about",
        "/about-us",
        "/about/",
        "/company",
        "/company/about",
    ]

    for path in about_urls:
        url = urljoin(base_url, path)
        html = fetch_page(url)
        if html:
            result["has_about_page"] = True
            result["about_url"] = url
            break

    if not result["has_about_page"]:
        result["issues"].append({
            "severity": "high",
            "category": "trust",
            "description": "No about page found",
            "recommendation": "Create a comprehensive about page with company information"
        })
        return result

    # Analyze about page content
    html_lower = html.lower()

    # Check for company information
    company_indicators = [
        'founded', 'established', 'mission', 'vision', 'values',
        'headquarters', 'office', 'location'
    ]
    company_matches = sum(1 for ind in company_indicators if ind in html_lower)
    if company_matches >= 3:
        result["has_company_info"] = True
        result["findings"].append("About page has company information")

    # Check for team information
    team_indicators = ['team', 'leadership', 'founder', 'ceo', 'staff', 'employees']
    if any(ind in html_lower for ind in team_indicators):
        result["has_team_info"] = True
        result["findings"].append("About page mentions team/leadership")

    # Check for company history
    history_indicators = ['history', 'story', 'journey', 'since', 'years']
    if any(ind in html_lower for ind in history_indicators):
        result["has_history"] = True
        result["findings"].append("About page includes company history")

    # Check word count
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    result["word_count"] = len(text.split())

    if result["word_count"] < 200:
        result["issues"].append({
            "severity": "medium",
            "category": "trust",
            "description": "About page is too brief",
            "recommendation": "Expand about page with more company details"
        })

    return result


def check_contact_page(base_url: str) -> Dict[str, Any]:
    """
    Check contact information availability.

    Args:
        base_url: Base URL of the site

    Returns:
        Dict with contact page analysis
    """
    result = {
        "has_contact_page": False,
        "has_address": False,
        "has_phone": False,
        "has_email": False,
        "has_form": False,
        "issues": [],
        "findings": []
    }

    # Try common contact page URLs
    contact_urls = ["/contact", "/contact-us", "/contact/", "/get-in-touch"]

    html = None
    for path in contact_urls:
        url = urljoin(base_url, path)
        html = fetch_page(url)
        if html:
            result["has_contact_page"] = True
            break

    # Also check homepage and footer
    homepage_html = fetch_page(base_url)

    # Check for contact info in either page
    check_html = (html or "") + (homepage_html or "")

    # Check for address
    address_patterns = [
        r'<address[^>]*>.*?</address>',
        r'(?:street|avenue|road|blvd|drive|suite|floor)\s*(?:#?\d+)?',
        r'\d{5}(?:-\d{4})?',  # ZIP code
    ]
    if any(re.search(p, check_html, re.IGNORECASE) for p in address_patterns):
        result["has_address"] = True
        result["findings"].append("Physical address found")

    # Check for phone
    phone_pattern = r'(?:\+1|1)?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    if re.search(phone_pattern, check_html):
        result["has_phone"] = True
        result["findings"].append("Phone number found")

    # Check for email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if re.search(email_pattern, check_html):
        result["has_email"] = True
        result["findings"].append("Email address found")

    # Check for contact form
    if '<form' in check_html.lower():
        result["has_form"] = True
        result["findings"].append("Contact form available")

    # Generate issues
    if not result["has_contact_page"]:
        result["issues"].append({
            "severity": "medium",
            "category": "trust",
            "description": "No dedicated contact page found",
            "recommendation": "Create a contact page with multiple ways to reach you"
        })

    missing = []
    if not result["has_address"]:
        missing.append("address")
    if not result["has_phone"]:
        missing.append("phone")
    if not result["has_email"]:
        missing.append("email")

    if missing:
        result["issues"].append({
            "severity": "medium",
            "category": "trust",
            "description": f"Missing contact info: {', '.join(missing)}",
            "recommendation": "Add complete contact information for trustworthiness"
        })

    return result


def check_trust_signals(html: str, base_url: str) -> Dict[str, Any]:
    """
    Check for trust signals throughout the site.

    Args:
        html: HTML content (homepage)
        base_url: Base URL

    Returns:
        Dict with trust signal analysis
    """
    result = {
        "has_privacy_policy": False,
        "has_terms": False,
        "has_testimonials": False,
        "has_certifications": False,
        "has_secure_badges": False,
        "social_profiles": [],
        "issues": [],
        "findings": []
    }

    html_lower = html.lower()

    # Check for privacy policy
    if re.search(r'privacy[\s-]?policy|privacy', html_lower):
        result["has_privacy_policy"] = True
        result["findings"].append("Privacy policy linked")
    else:
        result["issues"].append({
            "severity": "medium",
            "category": "trust",
            "description": "No privacy policy link found",
            "recommendation": "Add visible link to privacy policy"
        })

    # Check for terms
    if re.search(r'terms[\s-]?(?:of[\s-]?(?:service|use))?|terms[\s-]?(?:and[\s-]?)?conditions', html_lower):
        result["has_terms"] = True
        result["findings"].append("Terms of service linked")

    # Check for testimonials/reviews
    testimonial_indicators = ['testimonial', 'review', 'customer said', 'client said', 'rating']
    if any(ind in html_lower for ind in testimonial_indicators):
        result["has_testimonials"] = True
        result["findings"].append("Testimonials/reviews present")

    # Check for certifications/badges
    cert_indicators = ['certified', 'accredited', 'verified', 'award', 'badge', 'iso', 'soc']
    if any(ind in html_lower for ind in cert_indicators):
        result["has_certifications"] = True
        result["findings"].append("Certifications or badges present")

    # Check for security badges
    security_indicators = ['ssl', 'secure', 'encrypted', 'https', 'norton', 'mcafee', 'trust']
    if any(ind in html_lower for ind in security_indicators):
        result["has_secure_badges"] = True

    # Check for social profiles
    social_patterns = [
        (r'(?:linkedin\.com|linkedin)', 'LinkedIn'),
        (r'(?:twitter\.com|twitter|x\.com)', 'Twitter/X'),
        (r'(?:facebook\.com|facebook)', 'Facebook'),
        (r'(?:instagram\.com|instagram)', 'Instagram'),
        (r'(?:youtube\.com|youtube)', 'YouTube'),
    ]

    for pattern, name in social_patterns:
        if re.search(pattern, html_lower):
            result["social_profiles"].append(name)

    if result["social_profiles"]:
        result["findings"].append(f"Social profiles: {', '.join(result['social_profiles'])}")

    return result


def analyze_eeat_signals(url: str) -> Dict[str, Any]:
    """
    Complete E-E-A-T analysis for a website.

    Args:
        url: Website URL to analyze

    Returns:
        Dict with complete E-E-A-T analysis (0-20 score)
    """
    result = {
        "score": 0,
        "max": 20,
        "authors": {},
        "about_page": {},
        "contact": {},
        "trust_signals": {},
        "issues": [],
        "findings": []
    }

    # Fetch homepage
    html = fetch_page(url)
    if not html:
        result["issues"].append({
            "severity": "high",
            "category": "fetch",
            "description": "Could not fetch homepage"
        })
        result["score"] = 0
        return result

    # Check authors
    result["authors"] = check_author_pages(html, url)
    result["issues"].extend(result["authors"].get("issues", []))
    result["findings"].extend(result["authors"].get("findings", []))

    # Check about page
    result["about_page"] = check_about_page(url)
    result["issues"].extend(result["about_page"].get("issues", []))
    result["findings"].extend(result["about_page"].get("findings", []))

    # Check contact
    result["contact"] = check_contact_page(url)
    result["issues"].extend(result["contact"].get("issues", []))
    result["findings"].extend(result["contact"].get("findings", []))

    # Check trust signals
    result["trust_signals"] = check_trust_signals(html, url)
    result["issues"].extend(result["trust_signals"].get("issues", []))
    result["findings"].extend(result["trust_signals"].get("findings", []))

    # Calculate score (0-20)
    score = 0

    # Experience (5 points)
    # First-hand experience indicators would need content analysis
    # For now, base on case studies, examples mentioned
    if 'case study' in html.lower() or 'example' in html.lower():
        score += 2
        result["findings"].append("Shows experience through examples")

    # Expertise (5 points)
    if result["authors"].get("has_authors"):
        score += 2
    if result["authors"].get("authors_with_credentials"):
        score += 3

    # Authoritativeness (5 points)
    if result["trust_signals"].get("has_testimonials"):
        score += 2
    if result["trust_signals"].get("has_certifications"):
        score += 2
    if len(result["trust_signals"].get("social_profiles", [])) >= 2:
        score += 1

    # Trust (5 points)
    if result["about_page"].get("has_about_page"):
        score += 1
        if result["about_page"].get("has_company_info"):
            score += 1
    if result["contact"].get("has_email") and result["contact"].get("has_phone"):
        score += 1
    if result["trust_signals"].get("has_privacy_policy"):
        score += 1
    if result["contact"].get("has_address"):
        score += 1

    result["score"] = min(20, score)

    return result


__all__ = [
    'EEATIssue',
    'check_author_pages',
    'check_about_page',
    'check_contact_page',
    'check_trust_signals',
    'analyze_eeat_signals'
]
