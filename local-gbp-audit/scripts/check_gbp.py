"""
Check Google Business Profile (GBP)

GBP API has strict access, so this module supports:
1. Manual GBP data input (client provides screenshots/checklist)
2. Website-based signals that indicate GBP health
3. Scraping fallback (fragile but possible)
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GBPData:
    """Manual GBP data input from client or auditor."""
    claimed_verified: bool = False
    categories_accurate: bool = False
    primary_category: str = ""
    service_areas_configured: bool = False
    service_areas: List[str] = field(default_factory=list)
    photos_count_90_days: int = 0
    photos_variety: bool = False  # Team, trucks, projects
    posts_last_30_days: bool = False
    qa_response_rate: float = 0.0
    hours_accurate: bool = False
    emergency_hours_match_claim: bool = True  # If says 24/7, verify
    review_response_rate: float = 0.0
    review_count: int = 0
    review_rating: float = 0.0
    review_recency_days: int = 999  # Days since last review


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


def check_gbp_signals_from_website(html: str, target_url: str) -> Dict[str, Any]:
    """
    Check for GBP-related signals visible on the website.

    Args:
        html: HTML content
        target_url: Target URL

    Returns:
        Dict with website-based GBP signals
    """
    result = {
        "has_google_maps_embed": False,
        "has_review_widgets": False,
        "has_gbp_link": False,
        "has_schema_local_business": False,
        "nap_visible": {
            "name": False,
            "address": False,
            "phone": False,
        },
        "findings": [],
        "issues": [],
    }

    html_lower = html.lower()

    # Check for Google Maps embed
    maps_patterns = [
        r'maps\.google\.com/maps',
        r'google\.com/maps/embed',
        r'<iframe[^>]*maps\.google',
    ]
    for pattern in maps_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["has_google_maps_embed"] = True
            result["findings"].append("Google Maps embed found")
            break

    # Check for review widgets
    review_patterns = [
        r'google.*review',
        r'elfsight.*review',
        r'trustpilot',
        r'review.*widget',
    ]
    for pattern in review_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["has_review_widgets"] = True
            result["findings"].append("Review widget found")
            break

    # Check for GBP link
    gbp_patterns = [
        r'google\.com/maps/place',
        r'maps\.app\.goo\.gl',
        r'g\.page',
    ]
    for pattern in gbp_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["has_gbp_link"] = True
            result["findings"].append("Google Business Profile link found")
            break

    # Check for LocalBusiness schema
    schema_patterns = [
        r'"@type"\s*:\s*"LocalBusiness"',
        r'"@type"\s*:\s*"(?:HVAC|Plumber|Electrician|Contractor)',
        r'"@type"\s*:\s*"(?:HomeAndConstructionBusiness|ProfessionalService)"',
    ]
    for pattern in schema_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["has_schema_local_business"] = True
            result["findings"].append("LocalBusiness schema found")
            break

    # Check for NAP (Name, Address, Phone)
    # Phone
    phone_pattern = r'(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    if re.search(phone_pattern, html):
        result["nap_visible"]["phone"] = True

    # Address (basic patterns)
    address_patterns = [
        r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|blvd|drive|dr|lane|ln)',
        r'<address[^>]*>',
        r'(?:suite|ste|unit|apt)[.\s]?\d+',
    ]
    for pattern in address_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            result["nap_visible"]["address"] = True
            break

    # Issues for missing elements
    if not result["has_schema_local_business"]:
        result["issues"].append({
            "severity": "medium",
            "description": "No LocalBusiness schema markup found",
            "recommendation": "Add LocalBusiness schema to help Google understand your business",
        })

    if not result["has_google_maps_embed"] and not result["has_gbp_link"]:
        result["issues"].append({
            "severity": "low",
            "description": "No Google Maps integration visible",
            "recommendation": "Embed Google Maps or link to your Google Business Profile",
        })

    return result


def score_gbp_data(gbp_data: GBPData) -> Dict[str, Any]:
    """
    Score GBP data from manual input.

    Args:
        gbp_data: GBPData object with manual input

    Returns:
        Dict with GBP scoring (0-30 points for comprehensive)
    """
    result = {
        "score": 0,
        "max": 30,
        "gbp_claimed": gbp_data.claimed_verified,
        "breakdown": {},
        "issues": [],
        "findings": [],
        "quick_wins": [],
    }

    # Claimed/Verified (critical - 5 points)
    if gbp_data.claimed_verified:
        result["score"] += 5
        result["breakdown"]["claimed"] = {"score": 5, "max": 5}
        result["findings"].append("GBP is claimed and verified")
    else:
        result["breakdown"]["claimed"] = {"score": 0, "max": 5}
        result["issues"].append({
            "severity": "critical",
            "description": "Google Business Profile not claimed or verified",
            "recommendation": "Claim your GBP immediately - this is your most important local ranking factor",
        })
        result["quick_wins"].append({
            "title": "Claim your Google Business Profile",
            "description": "60-70% of trade searches have local intent. Without a claimed GBP, you're invisible in the map pack.",
            "effort": "low",
            "impact": "critical",
        })

    # Categories (3 points)
    if gbp_data.categories_accurate and gbp_data.primary_category:
        result["score"] += 3
        result["breakdown"]["categories"] = {"score": 3, "max": 3}
        result["findings"].append(f"Category set: {gbp_data.primary_category}")
    else:
        result["breakdown"]["categories"] = {"score": 0, "max": 3}
        result["issues"].append({
            "severity": "high",
            "description": "GBP category may be incorrect or too generic",
            "recommendation": "Set specific category like 'HVAC Contractor' not just 'Business'",
        })

    # Service Areas (3 points)
    if gbp_data.service_areas_configured and gbp_data.service_areas:
        result["score"] += 3
        result["breakdown"]["service_areas"] = {"score": 3, "max": 3}
        result["findings"].append(f"Service areas: {', '.join(gbp_data.service_areas[:5])}")
    else:
        result["breakdown"]["service_areas"] = {"score": 0, "max": 3}
        result["issues"].append({
            "severity": "medium",
            "description": "Service areas not configured in GBP",
            "recommendation": "Add all suburbs/cities you service to expand local visibility",
        })

    # Photos - Recent (3 points)
    if gbp_data.photos_count_90_days >= 5:
        result["score"] += 3
        result["breakdown"]["photos_recent"] = {"score": 3, "max": 3}
        result["findings"].append(f"{gbp_data.photos_count_90_days} photos added in last 90 days")
    elif gbp_data.photos_count_90_days > 0:
        result["score"] += 1
        result["breakdown"]["photos_recent"] = {"score": 1, "max": 3}
    else:
        result["breakdown"]["photos_recent"] = {"score": 0, "max": 3}
        result["issues"].append({
            "severity": "medium",
            "description": "No recent photos on GBP (last 90 days)",
            "recommendation": "Add project photos monthly - recent activity signals quality to Google",
        })
        result["quick_wins"].append({
            "title": "Add recent project photos",
            "description": "Your GBP has no photos from the last 90 days. Recent photos signal activity.",
            "effort": "low",
            "impact": "medium",
        })

    # Photos - Variety (2 points)
    if gbp_data.photos_variety:
        result["score"] += 2
        result["breakdown"]["photos_variety"] = {"score": 2, "max": 2}
        result["findings"].append("Photo variety: team, trucks, projects")
    else:
        result["breakdown"]["photos_variety"] = {"score": 0, "max": 2}
        result["issues"].append({
            "severity": "low",
            "description": "GBP photos lack variety",
            "recommendation": "Add photos of your team, trucks/vehicles, and completed projects",
        })

    # Posts (2 points)
    if gbp_data.posts_last_30_days:
        result["score"] += 2
        result["breakdown"]["posts"] = {"score": 2, "max": 2}
        result["findings"].append("Active GBP posting (last 30 days)")
    else:
        result["breakdown"]["posts"] = {"score": 0, "max": 2}
        result["issues"].append({
            "severity": "low",
            "description": "No GBP posts in last 30 days",
            "recommendation": "Post updates, offers, or tips monthly to show activity",
        })

    # Review Response Rate (critical - 5 points)
    if gbp_data.review_response_rate >= 0.9:
        result["score"] += 5
        result["breakdown"]["review_response"] = {"score": 5, "max": 5}
        result["findings"].append(f"Review response rate: {gbp_data.review_response_rate*100:.0f}%")
    elif gbp_data.review_response_rate >= 0.5:
        result["score"] += 2
        result["breakdown"]["review_response"] = {"score": 2, "max": 5}
    else:
        result["breakdown"]["review_response"] = {"score": 0, "max": 5}
        result["issues"].append({
            "severity": "high",
            "description": f"Review response rate is low ({gbp_data.review_response_rate*100:.0f}%)",
            "recommendation": "Google explicitly rewards businesses that respond to reviews",
        })
        result["quick_wins"].append({
            "title": "Respond to all reviews",
            "description": "Google rewards businesses that respond to reviews. Respond to all - positive and negative.",
            "effort": "medium",
            "impact": "high",
        })

    # Review Recency (2 points)
    if gbp_data.review_recency_days <= 30:
        result["score"] += 2
        result["breakdown"]["review_recency"] = {"score": 2, "max": 2}
        result["findings"].append("Recent reviews (within 30 days)")
    elif gbp_data.review_recency_days <= 90:
        result["score"] += 1
        result["breakdown"]["review_recency"] = {"score": 1, "max": 2}
    else:
        result["breakdown"]["review_recency"] = {"score": 0, "max": 2}
        result["issues"].append({
            "severity": "medium",
            "description": f"No reviews in {gbp_data.review_recency_days} days",
            "recommendation": "Implement a review request workflow to get consistent new reviews",
        })

    # Hours Accuracy (2 points)
    if gbp_data.hours_accurate:
        result["score"] += 2
        result["breakdown"]["hours"] = {"score": 2, "max": 2}
    else:
        result["breakdown"]["hours"] = {"score": 0, "max": 2}
        result["issues"].append({
            "severity": "medium",
            "description": "GBP hours may be inaccurate",
            "recommendation": "Update hours, especially holiday hours and emergency availability",
        })

    # Emergency Hours Match (3 points - important for trades)
    if gbp_data.emergency_hours_match_claim:
        result["score"] += 3
        result["breakdown"]["emergency_hours"] = {"score": 3, "max": 3}
    else:
        result["breakdown"]["emergency_hours"] = {"score": 0, "max": 3}
        result["issues"].append({
            "severity": "high",
            "description": "Website claims 24/7 but GBP hours don't match",
            "recommendation": "Ensure GBP hours match website claims, especially for emergency services",
        })

    return result


def analyze_gbp_health(
    target_url: str,
    gbp_data: Optional[GBPData] = None,
) -> Dict[str, Any]:
    """
    Complete GBP health analysis.

    Args:
        target_url: Website URL
        gbp_data: Optional manual GBP data input

    Returns:
        Dict with GBP analysis
    """
    result = {
        "score": 0,
        "max": 12,  # Website signals only
        "gbp_claimed": None,  # Unknown without manual data
        "website_signals": {},
        "gbp_data_analysis": None,
        "issues": [],
        "findings": [],
        "quick_wins": [],
        "manual_checklist": [],
    }

    # Fetch website
    html = fetch_page(target_url)
    if html:
        # Check website signals
        result["website_signals"] = check_gbp_signals_from_website(html, target_url)
        result["issues"].extend(result["website_signals"].get("issues", []))
        result["findings"].extend(result["website_signals"].get("findings", []))

        # Score website signals
        website_score = 0
        if result["website_signals"]["has_schema_local_business"]:
            website_score += 4
        if result["website_signals"]["has_google_maps_embed"]:
            website_score += 2
        if result["website_signals"]["has_gbp_link"]:
            website_score += 2
        if result["website_signals"]["has_review_widgets"]:
            website_score += 2
        if all(result["website_signals"]["nap_visible"].values()):
            website_score += 2

        result["score"] = website_score

    # If manual GBP data provided, do full analysis
    if gbp_data:
        result["gbp_data_analysis"] = score_gbp_data(gbp_data)
        result["score"] = result["gbp_data_analysis"]["score"]
        result["max"] = result["gbp_data_analysis"]["max"]
        result["gbp_claimed"] = gbp_data.claimed_verified
        result["issues"].extend(result["gbp_data_analysis"].get("issues", []))
        result["findings"].extend(result["gbp_data_analysis"].get("findings", []))
        result["quick_wins"].extend(result["gbp_data_analysis"].get("quick_wins", []))
    else:
        # Generate manual checklist for client
        result["manual_checklist"] = [
            {"item": "Is your GBP claimed and verified?", "field": "claimed_verified"},
            {"item": "Is your primary category accurate (e.g., 'HVAC Contractor')?", "field": "categories_accurate"},
            {"item": "Are service areas configured?", "field": "service_areas_configured"},
            {"item": "How many photos added in last 90 days?", "field": "photos_count_90_days"},
            {"item": "Do photos show team, trucks, AND projects?", "field": "photos_variety"},
            {"item": "Any posts in the last 30 days?", "field": "posts_last_30_days"},
            {"item": "What % of reviews have responses?", "field": "review_response_rate"},
            {"item": "Days since last review?", "field": "review_recency_days"},
            {"item": "Are hours accurate?", "field": "hours_accurate"},
            {"item": "If you claim 24/7, do GBP hours match?", "field": "emergency_hours_match_claim"},
        ]
        result["findings"].append("GBP manual checklist generated - requires client input for full scoring")

    return result


__all__ = [
    'GBPData',
    'check_gbp_signals_from_website',
    'score_gbp_data',
    'analyze_gbp_health',
]
