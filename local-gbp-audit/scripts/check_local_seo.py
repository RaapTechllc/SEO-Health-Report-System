"""
Check Local SEO Optimization

Analyze local keyword usage, geo-targeting, and location pages.
"""

import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse


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


def check_local_keywords(html: str, service_areas: List[str] = None) -> Dict[str, Any]:
    """
    Check for local keyword optimization.

    Args:
        html: HTML content
        service_areas: List of target service areas/cities

    Returns:
        Dict with local keyword analysis
    """
    result = {
        "has_location_in_title": False,
        "has_location_in_h1": False,
        "has_location_in_content": False,
        "locations_found": [],
        "score": 0,
        "max": 5,
        "issues": [],
        "findings": [],
    }

    # Default service areas if none provided (common Chicago suburbs for trades)
    if not service_areas:
        service_areas = [
            "chicago", "naperville", "schaumburg", "evanston", "oak park",
            "aurora", "joliet", "elgin", "waukegan", "cicero"
        ]

    html_lower = html.lower()

    # Extract title
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    title = title_match.group(1).lower() if title_match else ""

    # Extract H1
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
    h1 = h1_match.group(1).lower() if h1_match else ""

    # Check for locations
    for area in service_areas:
        area_lower = area.lower()

        if area_lower in title:
            result["has_location_in_title"] = True
            result["locations_found"].append(area)

        if area_lower in h1:
            result["has_location_in_h1"] = True
            if area not in result["locations_found"]:
                result["locations_found"].append(area)

        if area_lower in html_lower:
            result["has_location_in_content"] = True
            if area not in result["locations_found"]:
                result["locations_found"].append(area)

    # Calculate score
    if result["has_location_in_title"]:
        result["score"] += 2
        result["findings"].append(f"Location in title tag")
    else:
        result["issues"].append({
            "severity": "medium",
            "description": "No location in page title",
            "recommendation": "Add primary service area to title tag (e.g., 'HVAC Services in Chicago')",
        })

    if result["has_location_in_h1"]:
        result["score"] += 2
        result["findings"].append("Location in H1 heading")
    else:
        result["issues"].append({
            "severity": "medium",
            "description": "No location in H1 heading",
            "recommendation": "Include primary service area in main heading",
        })

    if result["has_location_in_content"]:
        result["score"] += 1
        result["findings"].append(f"Locations mentioned: {', '.join(result['locations_found'][:5])}")

    return result


def check_location_pages(html: str, base_url: str) -> Dict[str, Any]:
    """
    Check for dedicated location/service area pages.

    Args:
        html: HTML content
        base_url: Base URL for the site

    Returns:
        Dict with location page analysis
    """
    result = {
        "has_location_pages": False,
        "location_page_links": [],
        "has_service_area_section": False,
        "score": 0,
        "max": 3,
        "issues": [],
        "findings": [],
    }

    # Look for links to location pages
    location_patterns = [
        r'href=["\']([^"\']*(?:service-area|locations?|areas?-served|cities)[^"\']*)["\']',
        r'href=["\']([^"\']*(?:/il/|/chicago|/naperville|/schaumburg)[^"\']*)["\']',
    ]

    for pattern in location_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            if match not in result["location_page_links"]:
                result["location_page_links"].append(match)

    if result["location_page_links"]:
        result["has_location_pages"] = True
        result["score"] += 2
        result["findings"].append(f"Location pages found: {len(result['location_page_links'])}")

    # Check for service area sections
    service_area_patterns = [
        r'(?:service|serving|areas?\s+served|we\s+serve)',
        r'(?:locations?|cities|suburbs)',
    ]

    for pattern in service_area_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["has_service_area_section"] = True
            result["score"] += 1
            result["findings"].append("Service area section found on page")
            break

    if not result["has_location_pages"] and not result["has_service_area_section"]:
        result["issues"].append({
            "severity": "medium",
            "description": "No dedicated location/service area content found",
            "recommendation": "Create pages for each major service area to rank for '[service] in [city]' searches",
        })

    return result


def check_geo_meta_tags(html: str) -> Dict[str, Any]:
    """
    Check for geo-targeting meta tags.

    Args:
        html: HTML content

    Returns:
        Dict with geo meta analysis
    """
    result = {
        "has_geo_region": False,
        "has_geo_position": False,
        "has_icbm": False,
        "geo_data": {},
        "score": 0,
        "max": 2,
        "issues": [],
        "findings": [],
    }

    # Check for geo.region
    region_match = re.search(
        r'<meta[^>]*name=["\']geo\.region["\'][^>]*content=["\']([^"\']+)',
        html, re.IGNORECASE
    )
    if region_match:
        result["has_geo_region"] = True
        result["geo_data"]["region"] = region_match.group(1)
        result["score"] += 1
        result["findings"].append(f"Geo region: {region_match.group(1)}")

    # Check for geo.position
    position_match = re.search(
        r'<meta[^>]*name=["\']geo\.position["\'][^>]*content=["\']([^"\']+)',
        html, re.IGNORECASE
    )
    if position_match:
        result["has_geo_position"] = True
        result["geo_data"]["position"] = position_match.group(1)
        result["score"] += 0.5

    # Check for ICBM
    icbm_match = re.search(
        r'<meta[^>]*name=["\']ICBM["\'][^>]*content=["\']([^"\']+)',
        html, re.IGNORECASE
    )
    if icbm_match:
        result["has_icbm"] = True
        result["geo_data"]["icbm"] = icbm_match.group(1)
        result["score"] += 0.5

    if not any([result["has_geo_region"], result["has_geo_position"]]):
        result["issues"].append({
            "severity": "low",
            "description": "No geo-targeting meta tags found",
            "recommendation": "Add geo.region and geo.position meta tags for local relevance",
        })

    return result


def analyze_local_seo(
    target_url: str,
    service_areas: List[str] = None,
) -> Dict[str, Any]:
    """
    Complete local SEO analysis.

    Args:
        target_url: Website URL
        service_areas: Target service areas

    Returns:
        Dict with local SEO analysis
    """
    result = {
        "score": 0,
        "max": 10,
        "local_keywords": {},
        "location_pages": {},
        "geo_meta": {},
        "issues": [],
        "findings": [],
        "quick_wins": [],
    }

    # Fetch homepage
    html = fetch_page(target_url)
    if not html:
        result["issues"].append({
            "severity": "high",
            "description": "Could not fetch homepage for local SEO analysis",
            "recommendation": "Ensure site is accessible",
        })
        return result

    # Check local keywords
    result["local_keywords"] = check_local_keywords(html, service_areas)
    result["score"] += result["local_keywords"].get("score", 0)
    result["issues"].extend(result["local_keywords"].get("issues", []))
    result["findings"].extend(result["local_keywords"].get("findings", []))

    # Check location pages
    result["location_pages"] = check_location_pages(html, target_url)
    result["score"] += result["location_pages"].get("score", 0)
    result["issues"].extend(result["location_pages"].get("issues", []))
    result["findings"].extend(result["location_pages"].get("findings", []))

    # Check geo meta
    result["geo_meta"] = check_geo_meta_tags(html)
    result["score"] += result["geo_meta"].get("score", 0)
    result["issues"].extend(result["geo_meta"].get("issues", []))
    result["findings"].extend(result["geo_meta"].get("findings", []))

    # Generate quick wins
    if not result["local_keywords"]["has_location_in_title"]:
        result["quick_wins"].append({
            "title": "Add location to title tag",
            "description": "Include your primary service area in page titles for local search visibility.",
            "effort": "low",
            "impact": "high",
        })

    if not result["location_pages"]["has_location_pages"]:
        result["quick_wins"].append({
            "title": "Create location pages",
            "description": "Create dedicated pages for each major service area to rank for local searches.",
            "effort": "medium",
            "impact": "high",
        })

    return result


__all__ = [
    'check_local_keywords',
    'check_location_pages',
    'check_geo_meta_tags',
    'analyze_local_seo',
]
