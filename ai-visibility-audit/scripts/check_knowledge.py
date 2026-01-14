"""
Check Knowledge Graph Presence

Check if brand exists in knowledge graphs: Google KG, Wikipedia, Wikidata, Crunchbase.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class KnowledgeSource:
    """A knowledge graph source result."""

    source: str
    found: bool
    url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def check_google_knowledge_graph(
    brand_name: str, api_key: Optional[str] = None
) -> KnowledgeSource:
    """
    Check Google Knowledge Graph for brand presence.

    Args:
        brand_name: Brand/company name to search
        api_key: Google Knowledge Graph API key (defaults to GOOGLE_KG_API_KEY env var)

    Returns:
        KnowledgeSource with results
    """
    # Support multiple env var names for flexibility
    api_key = (
        api_key
        or os.environ.get("GOOGLE_KG_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )

    if not api_key:
        # STUB: Return placeholder when no API key
        return KnowledgeSource(
            source="google_kg",
            found=False,
            error="GOOGLE_API_KEY or GOOGLE_KG_API_KEY not set - skipping Google Knowledge Graph check",
        )

    try:
        import requests

        url = "https://kgsearch.googleapis.com/v1/entities:search"
        params = {
            "query": brand_name,
            "key": api_key,
            "limit": 5,
            "types": "Organization,Corporation,LocalBusiness",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = data.get("itemListElement", [])

        if items:
            # Find best match
            for item in items:
                result = item.get("result", {})
                name = result.get("name", "").lower()

                if brand_name.lower() in name or name in brand_name.lower():
                    return KnowledgeSource(
                        source="google_kg",
                        found=True,
                        url=result.get("detailedDescription", {}).get("url"),
                        data={
                            "name": result.get("name"),
                            "description": result.get("description"),
                            "detailed_description": result.get(
                                "detailedDescription", {}
                            ).get("articleBody"),
                            "types": result.get("@type", []),
                            "score": item.get("resultScore", 0),
                        },
                    )

            # No exact match but found related
            return KnowledgeSource(
                source="google_kg",
                found=False,
                data={
                    "related_entities": [
                        item.get("result", {}).get("name") for item in items[:3]
                    ]
                },
            )
        else:
            return KnowledgeSource(source="google_kg", found=False)

    except ImportError:
        return KnowledgeSource(
            source="google_kg", found=False, error="requests package not installed"
        )
    except Exception as e:
        return KnowledgeSource(source="google_kg", found=False, error=str(e))


def check_wikipedia(brand_name: str) -> KnowledgeSource:
    """
    Check Wikipedia for brand presence.

    Args:
        brand_name: Brand/company name to search

    Returns:
        KnowledgeSource with results
    """
    try:
        import requests

        headers = {
            "User-Agent": "SEOHealthReport/1.0 (https://raaptech.com; info@raaptech.com)"
        }

        # Search Wikipedia API
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": brand_name,
            "format": "json",
            "srlimit": 5,
        }

        response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("query", {}).get("search", [])

        if results:
            # Check for exact or close match
            for result in results:
                title = result.get("title", "").lower()
                brand_lower = brand_name.lower()

                if brand_lower in title or title in brand_lower:
                    # Found a match - get more details
                    page_url = f"https://en.wikipedia.org/wiki/{quote(result['title'].replace(' ', '_'))}"

                    # Get page extract
                    extract_params = {
                        "action": "query",
                        "titles": result["title"],
                        "prop": "extracts",
                        "exintro": True,
                        "explaintext": True,
                        "format": "json",
                    }

                    extract_response = requests.get(
                        search_url, params=extract_params, headers=headers, timeout=10
                    )
                    extract_data = extract_response.json()

                    pages = extract_data.get("query", {}).get("pages", {})
                    page_data = next(iter(pages.values()), {})

                    return KnowledgeSource(
                        source="wikipedia",
                        found=True,
                        url=page_url,
                        data={
                            "title": result["title"],
                            "snippet": result.get("snippet", ""),
                            "extract": page_data.get("extract", "")[
                                :500
                            ],  # First 500 chars
                        },
                    )

            # No exact match
            return KnowledgeSource(
                source="wikipedia",
                found=False,
                data={"related_articles": [r["title"] for r in results[:3]]},
            )
        else:
            return KnowledgeSource(source="wikipedia", found=False)

    except ImportError:
        return KnowledgeSource(
            source="wikipedia", found=False, error="requests package not installed"
        )
    except Exception as e:
        return KnowledgeSource(source="wikipedia", found=False, error=str(e))


def check_wikidata(brand_name: str) -> KnowledgeSource:
    """
    Check Wikidata for brand presence.

    Args:
        brand_name: Brand/company name to search

    Returns:
        KnowledgeSource with results
    """
    try:
        import requests

        headers = {
            "User-Agent": "SEOHealthReport/1.0 (https://raaptech.com; info@raaptech.com)"
        }

        # Search Wikidata API
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": brand_name,
            "language": "en",
            "format": "json",
            "limit": 5,
            "type": "item",
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("search", [])

        if results:
            # Check for match
            for result in results:
                label = result.get("label", "").lower()
                brand_lower = brand_name.lower()

                if brand_lower in label or label in brand_lower:
                    qid = result.get("id")
                    return KnowledgeSource(
                        source="wikidata",
                        found=True,
                        url=f"https://www.wikidata.org/wiki/{qid}",
                        data={
                            "id": qid,
                            "label": result.get("label"),
                            "description": result.get("description"),
                            "aliases": result.get("aliases", []),
                        },
                    )

            # No exact match
            return KnowledgeSource(
                source="wikidata",
                found=False,
                data={"related_items": [r.get("label") for r in results[:3]]},
            )
        else:
            return KnowledgeSource(source="wikidata", found=False)

    except ImportError:
        return KnowledgeSource(
            source="wikidata", found=False, error="requests package not installed"
        )
    except Exception as e:
        return KnowledgeSource(source="wikidata", found=False, error=str(e))


def check_crunchbase(brand_name: str, api_key: Optional[str] = None) -> KnowledgeSource:
    """
    Check Crunchbase for brand presence.

    Args:
        brand_name: Brand/company name to search
        api_key: Crunchbase API key (defaults to CRUNCHBASE_API_KEY env var)

    Returns:
        KnowledgeSource with results
    """
    api_key = api_key or os.environ.get("CRUNCHBASE_API_KEY")

    if not api_key:
        # STUB: Return placeholder when no API key
        # Can still check if a Crunchbase page exists via web search
        return KnowledgeSource(
            source="crunchbase",
            found=False,
            error="CRUNCHBASE_API_KEY not set - skipping Crunchbase check",
        )

    # Crunchbase API integration - Contact RaapTech for setup
    # Crunchbase API integration available upon request
    # Contact RaapTech for Crunchbase integration setup
    #
    # Crunchbase API endpoint:
    # https://api.crunchbase.com/api/v4/autocompletes?query={brand_name}
    #
    # Or search endpoint:
    # https://api.crunchbase.com/api/v4/searches/organizations
    #
    # Headers: {"X-cb-user-key": api_key}

    return KnowledgeSource(
        source="crunchbase",
        found=False,
        error="Crunchbase API integration not yet implemented",
    )


def check_linkedin(
    brand_name: str, linkedin_url: Optional[str] = None
) -> KnowledgeSource:
    """
    Check if brand has LinkedIn company page by verifying page exists.

    Args:
        brand_name: Brand/company name to search
        linkedin_url: Optional direct LinkedIn company URL to check

    Returns:
        KnowledgeSource with results
    """
    try:
        import requests

        # Generate slug variations to try
        slugs_to_try = []

        # If direct URL provided, extract slug from it
        if linkedin_url:
            if "/company/" in linkedin_url:
                slug = linkedin_url.split("/company/")[-1].rstrip("/")
                slugs_to_try.append(slug)

        # Generate common slug patterns
        base_name = brand_name.lower()
        slugs_to_try.extend(
            [
                base_name.replace(" ", "-")
                .replace(".", "")
                .replace(",", ""),  # sheet-metal-werks
                base_name.replace(" ", "")
                .replace(".", "")
                .replace(",", ""),  # sheetmetalwerks
                base_name.replace(" ", "-").replace(
                    ".", "-"
                ),  # sheet-metal-werks (dots to dashes)
                base_name.replace(" ", ""),  # sheetmetalwerks (simple)
            ]
        )

        # Remove duplicates while preserving order
        seen = set()
        unique_slugs = []
        for slug in slugs_to_try:
            if slug not in seen:
                seen.add(slug)
                unique_slugs.append(slug)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        for slug in unique_slugs:
            url = f"https://www.linkedin.com/company/{slug}"

            try:
                response = requests.get(
                    url, headers=headers, timeout=10, allow_redirects=True
                )

                # LinkedIn returns 200 for valid company pages
                # Invalid pages redirect to login or return 404
                if response.status_code == 200:
                    # Check if it's actually a company page (not a login redirect)
                    content_lower = response.text.lower()

                    # Look for indicators that this is a valid company page
                    is_company_page = any(
                        [
                            "linkedin.com/company/" in response.url.lower(),
                            '"@type":"organization"' in content_lower,
                            'data-entity-urn="urn:li:fsd_company' in content_lower,
                            f"<title>{brand_name.lower()}" in content_lower,
                            "company-name" in content_lower,
                        ]
                    )

                    # Also check it's not a login wall
                    is_login_wall = any(
                        [
                            "join linkedin" in content_lower,
                            "sign in" in content_lower
                            and "company" not in content_lower,
                            "/login" in response.url.lower(),
                        ]
                    )

                    if is_company_page and not is_login_wall:
                        return KnowledgeSource(
                            source="linkedin",
                            found=True,
                            url=url,
                            data={
                                "slug": slug,
                                "verified": True,
                                "response_code": response.status_code,
                            },
                        )

            except requests.RequestException:
                continue  # Try next slug

        # None of the slugs worked
        return KnowledgeSource(
            source="linkedin",
            found=False,
            url=f"https://www.linkedin.com/company/{unique_slugs[0]}"
            if unique_slugs
            else None,
            data={
                "slugs_tried": unique_slugs,
                "suggestion": "Create a LinkedIn company page or verify the company name spelling",
            },
        )

    except ImportError:
        return KnowledgeSource(
            source="linkedin", found=False, error="requests package not installed"
        )
    except Exception as e:
        return KnowledgeSource(source="linkedin", found=False, error=str(e))


def check_all_sources(
    brand_name: str, target_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check all knowledge graph sources for brand presence.

    Args:
        brand_name: Brand/company name to search
        target_url: Optional company website URL for additional verification

    Returns:
        Dict with complete knowledge graph analysis including score
    """
    sources = {}
    findings = []

    # Check each source
    sources["google_kg"] = check_google_knowledge_graph(brand_name)
    sources["wikipedia"] = check_wikipedia(brand_name)
    sources["wikidata"] = check_wikidata(brand_name)
    sources["crunchbase"] = check_crunchbase(brand_name)
    sources["linkedin"] = check_linkedin(brand_name)

    # Count successes
    found_count = sum(1 for s in sources.values() if s.found)
    total_sources = len(
        [s for s in sources.values() if s.error is None or "not set" not in s.error]
    )

    # Generate findings
    for name, source in sources.items():
        if source.error and "not set" in source.error:
            findings.append(f"Skipped {name}: API key not configured")
        elif source.error:
            findings.append(f"Error checking {name}: {source.error}")
        elif source.found:
            url_info = f" ({source.url})" if source.url else ""
            findings.append(f"FOUND in {name}{url_info}")
        else:
            findings.append(f"NOT FOUND in {name}")
            if source.data and source.data.get("related_entities"):
                findings.append(
                    f"  Related: {', '.join(source.data['related_entities'][:3])}"
                )
            if source.data and source.data.get("suggestion"):
                findings.append(f"  Suggestion: {source.data['suggestion']}")

    # Calculate score (0-15)
    # Wikipedia + Google KG = 10 points, LinkedIn = 3 points, others = 2 points
    score = 0

    if sources["wikipedia"].found:
        score += 5
        findings.append("Wikipedia presence: Strong authority signal for AI systems")
    else:
        findings.append(
            "Recommendation: Create Wikipedia article to improve AI awareness"
        )

    if sources["google_kg"].found:
        score += 5
        findings.append("Google Knowledge Graph: Directly feeds Google's AI systems")
    elif sources["google_kg"].error and "not set" in sources["google_kg"].error:
        score += 2  # Give partial credit if we couldn't check
    else:
        findings.append(
            "Recommendation: Improve structured data to appear in Google KG"
        )

    if sources["linkedin"].found:
        score += 3
        findings.append(
            "LinkedIn presence: Important for B2B visibility and professional credibility"
        )
    else:
        findings.append(
            "Recommendation: Create or optimize LinkedIn company page for B2B visibility"
        )

    if sources["wikidata"].found:
        score += 1
        findings.append("Wikidata: Feeds multiple AI knowledge bases")

    if sources["crunchbase"].found:
        score += 1

    return {
        "score": min(15, score),
        "max": 15,
        "findings": findings,
        "sources": {
            name: {"found": s.found, "url": s.url, "error": s.error, "data": s.data}
            for name, s in sources.items()
        },
        "details": {
            "sources_checked": total_sources,
            "sources_found": found_count,
            "presence_rate": found_count / total_sources if total_sources > 0 else 0,
        },
    }


__all__ = [
    "KnowledgeSource",
    "check_google_knowledge_graph",
    "check_wikipedia",
    "check_wikidata",
    "check_crunchbase",
    "check_linkedin",
    "check_all_sources",
]
