"""
Score Backlinks

Analyze external backlink profile quality using real API data.
Supports Moz Link API (primary), with fallback providers.
When no API key is configured, returns score=None with data_source="unavailable".
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


@dataclass
class Backlink:
    """A backlink pointing to the site."""
    source_url: str
    target_url: str
    anchor_text: str
    domain_rating: Optional[int]
    is_dofollow: bool
    is_relevant: bool


def analyze_backlink_profile(
    url: str,
    api_key: Optional[str] = None,
    api_provider: str = "moz"
) -> dict[str, Any]:
    """
    Analyze backlink profile using external API.

    Tries providers in order: Moz → Ahrefs → Semrush.
    When no API key is available for any provider, returns score=None
    with data_source="unavailable" (never returns a fake neutral score).

    Args:
        url: URL to analyze backlinks for
        api_key: API key for backlink service
        api_provider: Preferred service ("moz", "ahrefs", "semrush")

    Returns:
        Dict with backlink analysis (0-15 score, or None if unavailable)
    """
    # Try each provider in priority order
    providers = _get_provider_order(api_provider)

    for provider in providers:
        key = api_key if provider == api_provider else None
        key = key or os.environ.get(f'{provider.upper()}_API_KEY')

        if not key:
            continue

        try:
            if provider == "moz":
                secret = os.environ.get('MOZ_API_SECRET', '')
                return _analyze_with_moz(url, key, secret)
            elif provider == "ahrefs":
                return _analyze_with_ahrefs(url, key)
            elif provider == "semrush":
                return _analyze_with_semrush(url, key)
        except Exception as e:
            logger.warning(f"Backlink analysis with {provider} failed: {e}")
            continue

    # No API key available for any provider — return honest unavailable
    return {
        "score": None,
        "max": 15,
        "data_source": "unavailable",
        "total_backlinks": None,
        "referring_domains": None,
        "domain_authority": None,
        "dofollow_ratio": None,
        "anchor_distribution": {},
        "top_referring_domains": [],
        "toxic_links": [],
        "issues": [{
            "severity": "medium",
            "category": "backlinks",
            "description": "Backlink analysis unavailable — no API key configured",
            "recommendation": (
                "Set MOZ_API_KEY (recommended), AHREFS_API_KEY, or SEMRUSH_API_KEY "
                "for real backlink data"
            )
        }],
        "findings": [
            "Backlink data unavailable — API key required for accurate analysis",
            "This component is excluded from scoring until real data is available"
        ]
    }


def _get_provider_order(preferred: str) -> list[str]:
    """Return provider list with preferred first."""
    all_providers = ["moz", "ahrefs", "semrush"]
    if preferred in all_providers:
        all_providers.remove(preferred)
        return [preferred] + all_providers
    return all_providers


def _analyze_with_moz(url: str, access_id: str, secret_key: str) -> dict[str, Any]:
    """
    Analyze backlinks using Moz Links API v2.

    Uses the URL Metrics endpoint for domain authority and link counts.

    Args:
        url: URL to analyze
        access_id: Moz Access ID
        secret_key: Moz Secret Key

    Returns:
        Dict with real backlink analysis
    """
    parsed = urlparse(url)
    target = parsed.netloc or parsed.path

    # Moz Links API v2 - URL Metrics
    api_url = "https://lsapi.seomoz.com/v2/url_metrics"
    payload = {
        "targets": [target]
    }

    response = requests.post(
        api_url,
        json=payload,
        auth=(access_id, secret_key),
        timeout=15,
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("results"):
        raise ValueError("Moz API returned no results")

    metrics = data["results"][0]

    # Extract real metrics
    domain_authority = metrics.get("domain_authority", 0)
    page_authority = metrics.get("page_authority", 0)
    linking_root_domains = metrics.get("root_domains_to_root_domain", 0)
    external_links = metrics.get("external_pages_to_root_domain", 0)

    # Calculate score from real data
    score = calculate_backlink_score({
        "domain_authority": round(domain_authority),
        "referring_domains": linking_root_domains,
        "dofollow_ratio": 0.65,  # Moz doesn't break this out in basic endpoint
        "toxic_count": 0
    })

    return {
        "score": score,
        "max": 15,
        "data_source": "real_api",
        "api_provider": "moz",
        "total_backlinks": external_links,
        "referring_domains": linking_root_domains,
        "domain_authority": round(domain_authority),
        "page_authority": round(page_authority),
        "dofollow_ratio": None,  # Not available in basic Moz endpoint
        "anchor_distribution": {},
        "top_referring_domains": [],
        "toxic_links": [],
        "issues": [],
        "findings": [
            f"Domain Authority: {round(domain_authority)}/100 (Moz)",
            f"Page Authority: {round(page_authority)}/100",
            f"Referring Domains: {linking_root_domains:,}",
            f"External Links: {external_links:,}"
        ]
    }


def _analyze_with_ahrefs(url: str, api_key: str) -> dict[str, Any]:
    """
    Analyze backlinks using Ahrefs API v3.

    Args:
        url: URL to analyze
        api_key: Ahrefs API token

    Returns:
        Dict with real backlink analysis
    """
    parsed = urlparse(url)
    target = parsed.netloc or parsed.path

    # Ahrefs API v3 - Domain Rating
    api_url = "https://apiv2.ahrefs.com"
    params = {
        "token": api_key,
        "from": "domain_rating",
        "target": target,
        "mode": "domain",
        "output": "json"
    }

    response = requests.get(api_url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    domain_rating = data.get("domain", {}).get("domain_rating", 0)

    # Get backlink counts
    params["from"] = "backlinks_stats"
    response = requests.get(api_url, params=params, timeout=15)
    response.raise_for_status()
    stats = response.json()

    stats_data = stats.get("stats", {})
    total_backlinks = stats_data.get("backlinks", 0)
    referring_domains = stats_data.get("refdomains", 0)

    dofollow = stats_data.get("backlinks_dofollow", 0)
    dofollow_ratio = dofollow / total_backlinks if total_backlinks > 0 else 0

    score = calculate_backlink_score({
        "domain_authority": round(domain_rating),
        "referring_domains": referring_domains,
        "dofollow_ratio": dofollow_ratio,
        "toxic_count": 0
    })

    return {
        "score": score,
        "max": 15,
        "data_source": "real_api",
        "api_provider": "ahrefs",
        "total_backlinks": total_backlinks,
        "referring_domains": referring_domains,
        "domain_authority": round(domain_rating),
        "dofollow_ratio": round(dofollow_ratio, 2),
        "anchor_distribution": {},
        "top_referring_domains": [],
        "toxic_links": [],
        "issues": [],
        "findings": [
            f"Domain Rating: {round(domain_rating)}/100 (Ahrefs)",
            f"Referring Domains: {referring_domains:,}",
            f"Total Backlinks: {total_backlinks:,}",
            f"Dofollow Ratio: {dofollow_ratio:.0%}"
        ]
    }


def _analyze_with_semrush(url: str, api_key: str) -> dict[str, Any]:
    """
    Analyze backlinks using SEMrush API.

    Args:
        url: URL to analyze
        api_key: SEMrush API key

    Returns:
        Dict with real backlink analysis
    """
    parsed = urlparse(url)
    target = parsed.netloc or parsed.path

    # SEMrush Backlinks Overview
    api_url = "https://api.semrush.com/analytics/v1/"
    params = {
        "key": api_key,
        "type": "backlinks_overview",
        "target": target,
        "target_type": "root_domain",
        "export_columns": "total,domains_num,urls_num,ips_num,follows_num,nofollows_num,score"
    }

    response = requests.get(api_url, params=params, timeout=15)
    response.raise_for_status()

    # SEMrush returns semicolon-separated data
    lines = response.text.strip().split("\n")
    if len(lines) < 2:
        raise ValueError("SEMrush returned insufficient data")

    headers = lines[0].split(";")
    values = lines[1].split(";")
    metrics = dict(zip(headers, values))

    total_backlinks = int(metrics.get("total", 0))
    referring_domains = int(metrics.get("domains_num", 0))
    follows = int(metrics.get("follows_num", 0))
    authority_score = int(metrics.get("score", 0))
    dofollow_ratio = follows / total_backlinks if total_backlinks > 0 else 0

    score = calculate_backlink_score({
        "domain_authority": authority_score,
        "referring_domains": referring_domains,
        "dofollow_ratio": dofollow_ratio,
        "toxic_count": 0
    })

    return {
        "score": score,
        "max": 15,
        "data_source": "real_api",
        "api_provider": "semrush",
        "total_backlinks": total_backlinks,
        "referring_domains": referring_domains,
        "domain_authority": authority_score,
        "dofollow_ratio": round(dofollow_ratio, 2),
        "anchor_distribution": {},
        "top_referring_domains": [],
        "toxic_links": [],
        "issues": [],
        "findings": [
            f"Authority Score: {authority_score}/100 (SEMrush)",
            f"Referring Domains: {referring_domains:,}",
            f"Total Backlinks: {total_backlinks:,}",
            f"Dofollow Ratio: {dofollow_ratio:.0%}"
        ]
    }


def check_toxic_links(backlinks: list[Backlink]) -> dict[str, Any]:
    """
    Check for potentially toxic or harmful backlinks.

    Args:
        backlinks: List of backlinks to analyze

    Returns:
        Dict with toxic link analysis
    """
    result = {
        "toxic_count": 0,
        "suspicious_count": 0,
        "toxic_links": [],
        "issues": []
    }

    toxic_indicators = [
        r'(?:porn|xxx|adult|casino|gambling|viagra|cialis|pharma)',
        r'(?:free-?(?:download|movies|music|software))',
        r'(?:cheap-?(?:seo|backlinks|links))',
        r'\.(?:xyz|top|gq|ml|cf|tk|ga)$',
        r'(?:link-?farm|link-?network|pbn)',
    ]

    for backlink in backlinks:
        source_lower = backlink.source_url.lower()

        is_toxic = False
        is_suspicious = False

        for pattern in toxic_indicators:
            if re.search(pattern, source_lower):
                is_toxic = True
                break

        if backlink.domain_rating is not None:
            if backlink.domain_rating < 10:
                is_suspicious = True

        if is_toxic:
            result["toxic_count"] += 1
            result["toxic_links"].append({
                "url": backlink.source_url,
                "reason": "Matches toxic pattern"
            })
        elif is_suspicious:
            result["suspicious_count"] += 1

    if result["toxic_count"] > 0:
        result["issues"].append({
            "severity": "high",
            "category": "backlinks",
            "description": f"Found {result['toxic_count']} potentially toxic backlinks",
            "recommendation": "Review and disavow toxic backlinks in Google Search Console"
        })

    if backlinks and result["suspicious_count"] > len(backlinks) * 0.3:
        result["issues"].append({
            "severity": "medium",
            "category": "backlinks",
            "description": (
                f"High number of low-quality backlinks ({result['suspicious_count']})"
            ),
            "recommendation": "Focus on earning higher-quality backlinks"
        })

    return result


def calculate_backlink_score(metrics: dict[str, Any]) -> int:
    """
    Calculate backlink score from metrics.

    Args:
        metrics: Backlink metrics from API

    Returns:
        Score from 0-15
    """
    score = 0

    # Domain rating/authority (0-6 points)
    dr = metrics.get("domain_rating") or metrics.get("domain_authority") or 0
    if dr >= 70:
        score += 6
    elif dr >= 50:
        score += 5
    elif dr >= 30:
        score += 4
    elif dr >= 20:
        score += 3
    elif dr >= 10:
        score += 2
    elif dr > 0:
        score += 1

    # Referring domains (0-5 points)
    rd = metrics.get("referring_domains", 0)
    if rd >= 1000:
        score += 5
    elif rd >= 500:
        score += 4
    elif rd >= 100:
        score += 3
    elif rd >= 50:
        score += 2
    elif rd >= 10:
        score += 1

    # Dofollow ratio (0-2 points)
    dofollow_ratio = metrics.get("dofollow_ratio", 0)
    if dofollow_ratio >= 0.7:
        score += 2
    elif dofollow_ratio >= 0.5:
        score += 1

    # Deduct for toxic links
    toxic_count = metrics.get("toxic_count", 0)
    if toxic_count > 10:
        score -= 3
    elif toxic_count > 5:
        score -= 2
    elif toxic_count > 0:
        score -= 1

    return max(0, min(15, score))


def estimate_backlink_health(url: str) -> dict[str, Any]:
    """
    Estimate backlink health without external API using observable signals.

    This is a heuristic fallback — the score is clearly marked as estimated
    and the data_source is set to "heuristic" to distinguish from real API data.

    Args:
        url: URL to analyze

    Returns:
        Dict with estimated backlink health
    """
    result = {
        "score": None,
        "max": 15,
        "data_source": "heuristic",
        "estimated": True,
        "findings": ["Backlink score estimated from on-page signals — add API key for real data"],
        "issues": [{
            "severity": "low",
            "category": "backlinks",
            "description": "Using heuristic backlink estimation (no API key)",
            "recommendation": "Set MOZ_API_KEY for accurate backlink analysis"
        }]
    }

    try:
        headers = {'User-Agent': 'SEO-Health-Report-Bot/1.0'}
        response = requests.get(url, headers=headers, timeout=10)

        html = response.text.lower()
        authority_signals = 0

        if any(term in html for term in ['featured in', 'as seen in', 'press', 'media']):
            authority_signals += 1
        if any(term in html for term in ['award', 'recognized', 'certified', 'accredited']):
            authority_signals += 1
        if any(term in html for term in ['partner', 'trusted by', 'our clients']):
            authority_signals += 1
        if any(term in html for term in ['testimonial', 'review', 'customers']):
            authority_signals += 1

        if authority_signals >= 3:
            result["score"] = 10
            result["findings"].append("Strong authority signals detected on page")
        elif authority_signals >= 2:
            result["score"] = 8
            result["findings"].append("Some authority signals detected on page")
        elif authority_signals >= 1:
            result["score"] = 6
            result["findings"].append("Limited authority signals detected on page")
        else:
            result["score"] = 4
            result["findings"].append("No authority signals detected on page")

    except (requests.RequestException, OSError):
        result["findings"].append("Could not fetch page for heuristic analysis")

    return result


__all__ = [
    'Backlink',
    'analyze_backlink_profile',
    'check_toxic_links',
    'calculate_backlink_score',
    'estimate_backlink_health'
]
