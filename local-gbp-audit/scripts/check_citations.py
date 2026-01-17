"""
Check Citations and NAP Consistency

Analyze Name, Address, Phone (NAP) consistency across the website.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NAPData:
    """Name, Address, Phone data."""
    name: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    phone: str = ""
    phone_formatted: str = ""


def fetch_page(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch HTML content from URL."""
    try:
        import requests
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception:
        return None


def extract_phone_numbers(html: str) -> List[str]:
    """Extract all phone numbers from HTML."""
    patterns = [
        r'(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
    ]

    phones = set()
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            # Normalize to digits only
            phone = ''.join(match)
            if len(phone) == 10:
                phones.add(phone)

    return list(phones)


def extract_addresses(html: str) -> List[Dict[str, str]]:
    """Extract addresses from HTML."""
    addresses = []

    # Look for structured address data
    # Schema.org address
    schema_pattern = r'"streetAddress"\s*:\s*"([^"]+)".*?"addressLocality"\s*:\s*"([^"]+)".*?"addressRegion"\s*:\s*"([^"]+)".*?"postalCode"\s*:\s*"([^"]+)"'
    schema_matches = re.findall(schema_pattern, html, re.IGNORECASE | re.DOTALL)
    for match in schema_matches:
        addresses.append({
            "street": match[0],
            "city": match[1],
            "state": match[2],
            "zip": match[3],
        })

    # Look for <address> tags
    address_tag_pattern = r'<address[^>]*>(.*?)</address>'
    address_matches = re.findall(address_tag_pattern, html, re.IGNORECASE | re.DOTALL)
    for match in address_matches:
        # Clean HTML
        text = re.sub(r'<[^>]+>', ' ', match)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            addresses.append({"raw": text})

    return addresses


def extract_business_name(html: str, url: str) -> Optional[str]:
    """Extract business name from HTML."""
    # Try schema.org
    schema_pattern = r'"name"\s*:\s*"([^"]+)"'
    schema_match = re.search(schema_pattern, html)
    if schema_match:
        return schema_match.group(1)

    # Try og:site_name
    og_pattern = r'<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)'
    og_match = re.search(og_pattern, html, re.IGNORECASE)
    if og_match:
        return og_match.group(1)

    # Try title tag
    title_pattern = r'<title[^>]*>([^<|]+)'
    title_match = re.search(title_pattern, html, re.IGNORECASE)
    if title_match:
        return title_match.group(1).strip()

    return None


def check_nap_consistency(html: str, url: str) -> Dict[str, Any]:
    """
    Check NAP consistency within a single page.

    Args:
        html: HTML content
        url: Page URL

    Returns:
        Dict with NAP consistency analysis
    """
    result = {
        "nap_found": {
            "name": False,
            "address": False,
            "phone": False,
        },
        "phone_numbers": [],
        "addresses": [],
        "business_name": None,
        "phone_consistent": True,
        "address_consistent": True,
        "score": 0,
        "max": 8,
        "issues": [],
        "findings": [],
    }

    # Extract data
    result["phone_numbers"] = extract_phone_numbers(html)
    result["addresses"] = extract_addresses(html)
    result["business_name"] = extract_business_name(html, url)

    # Check what was found
    if result["business_name"]:
        result["nap_found"]["name"] = True
        result["findings"].append(f"Business name found: {result['business_name']}")

    if result["phone_numbers"]:
        result["nap_found"]["phone"] = True
        result["findings"].append(f"Phone number(s) found: {len(result['phone_numbers'])}")

        # Check phone consistency
        if len(set(result["phone_numbers"])) > 1:
            result["phone_consistent"] = False
            result["issues"].append({
                "severity": "high",
                "description": f"Multiple different phone numbers found ({len(set(result['phone_numbers']))})",
                "recommendation": "Use one consistent phone number across all pages",
            })

    if result["addresses"]:
        result["nap_found"]["address"] = True
        result["findings"].append(f"Address found")

    # Calculate score
    if result["nap_found"]["name"]:
        result["score"] += 2
    else:
        result["issues"].append({
            "severity": "medium",
            "description": "Business name not clearly identifiable",
            "recommendation": "Add business name in schema markup and site header",
        })

    if result["nap_found"]["phone"]:
        result["score"] += 3
        if result["phone_consistent"]:
            result["score"] += 1
    else:
        result["issues"].append({
            "severity": "high",
            "description": "No phone number found on page",
            "recommendation": "Add phone number prominently for local SEO",
        })

    if result["nap_found"]["address"]:
        result["score"] += 2
    else:
        result["issues"].append({
            "severity": "medium",
            "description": "No physical address found",
            "recommendation": "Add business address for local search visibility",
        })

    return result


def check_schema_local_business(html: str) -> Dict[str, Any]:
    """
    Check for LocalBusiness schema markup.

    Args:
        html: HTML content

    Returns:
        Dict with schema analysis
    """
    result = {
        "has_local_business_schema": False,
        "schema_type": None,
        "schema_completeness": 0,
        "missing_fields": [],
        "score": 0,
        "max": 4,
        "issues": [],
        "findings": [],
    }

    # Check for LocalBusiness or subtypes
    type_patterns = [
        (r'"@type"\s*:\s*"LocalBusiness"', "LocalBusiness"),
        (r'"@type"\s*:\s*"HVACBusiness"', "HVACBusiness"),
        (r'"@type"\s*:\s*"Plumber"', "Plumber"),
        (r'"@type"\s*:\s*"Electrician"', "Electrician"),
        (r'"@type"\s*:\s*"HomeAndConstructionBusiness"', "HomeAndConstructionBusiness"),
        (r'"@type"\s*:\s*"ProfessionalService"', "ProfessionalService"),
    ]

    for pattern, schema_type in type_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["has_local_business_schema"] = True
            result["schema_type"] = schema_type
            result["score"] += 2
            result["findings"].append(f"LocalBusiness schema found: {schema_type}")
            break

    if not result["has_local_business_schema"]:
        result["issues"].append({
            "severity": "medium",
            "description": "No LocalBusiness schema markup found",
            "recommendation": "Add LocalBusiness schema to help Google understand your business",
        })
        return result

    # Check for required fields
    required_fields = [
        ("name", r'"name"\s*:\s*"[^"]+"'),
        ("address", r'"address"\s*:\s*\{'),
        ("telephone", r'"telephone"\s*:\s*"[^"]+"'),
        ("openingHours", r'"openingHours"'),
        ("priceRange", r'"priceRange"'),
        ("areaServed", r'"areaServed"'),
    ]

    fields_found = 0
    for field_name, pattern in required_fields:
        if re.search(pattern, html, re.IGNORECASE):
            fields_found += 1
        else:
            result["missing_fields"].append(field_name)

    result["schema_completeness"] = fields_found / len(required_fields)

    if result["schema_completeness"] >= 0.8:
        result["score"] += 2
        result["findings"].append("Schema markup is comprehensive")
    elif result["schema_completeness"] >= 0.5:
        result["score"] += 1
        result["issues"].append({
            "severity": "low",
            "description": f"Schema missing: {', '.join(result['missing_fields'][:3])}",
            "recommendation": "Add missing schema fields for better local search visibility",
        })
    else:
        result["issues"].append({
            "severity": "medium",
            "description": "Schema markup is incomplete",
            "recommendation": "Add required schema fields: name, address, telephone, openingHours",
        })

    return result


def analyze_citations(
    target_url: str,
    check_pages: List[str] = None,
) -> Dict[str, Any]:
    """
    Complete citation and NAP analysis.

    Args:
        target_url: Website URL
        check_pages: Additional pages to check (relative paths)

    Returns:
        Dict with citation analysis
    """
    result = {
        "score": 0,
        "max": 12,
        "nap_consistency": {},
        "schema": {},
        "pages_checked": [],
        "issues": [],
        "findings": [],
        "quick_wins": [],
    }

    # Default pages to check
    if check_pages is None:
        check_pages = ["", "/contact", "/about"]

    all_phones = []
    all_names = []

    for path in check_pages:
        url = target_url.rstrip('/') + path if path else target_url
        html = fetch_page(url)

        if html:
            result["pages_checked"].append(url)

            # Check NAP on each page
            nap_result = check_nap_consistency(html, url)
            all_phones.extend(nap_result.get("phone_numbers", []))
            if nap_result.get("business_name"):
                all_names.append(nap_result["business_name"])

            # Store homepage results
            if path == "" or path == "/":
                result["nap_consistency"] = nap_result
                result["score"] += nap_result.get("score", 0)
                result["issues"].extend(nap_result.get("issues", []))
                result["findings"].extend(nap_result.get("findings", []))

                # Check schema on homepage
                result["schema"] = check_schema_local_business(html)
                result["score"] += result["schema"].get("score", 0)
                result["issues"].extend(result["schema"].get("issues", []))
                result["findings"].extend(result["schema"].get("findings", []))

    # Check cross-page consistency
    unique_phones = set(all_phones)
    if len(unique_phones) > 1:
        result["issues"].append({
            "severity": "high",
            "description": f"Multiple phone numbers across pages: {len(unique_phones)} different numbers",
            "recommendation": "Use one consistent phone number across your entire website",
        })

    # Generate quick wins
    if not result["schema"].get("has_local_business_schema"):
        result["quick_wins"].append({
            "title": "Add LocalBusiness schema",
            "description": "Schema markup helps Google understand your business for local searches.",
            "effort": "medium",
            "impact": "medium",
        })

    if not result["nap_consistency"].get("nap_found", {}).get("phone"):
        result["quick_wins"].append({
            "title": "Add phone number to homepage",
            "description": "Phone number visibility is critical for local SEO and conversions.",
            "effort": "low",
            "impact": "high",
        })

    return result


__all__ = [
    'NAPData',
    'extract_phone_numbers',
    'extract_addresses',
    'check_nap_consistency',
    'check_schema_local_business',
    'analyze_citations',
]
