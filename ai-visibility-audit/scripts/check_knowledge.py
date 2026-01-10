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
    brand_name: str,
    api_key: Optional[str] = None
) -> KnowledgeSource:
    """
    Check Google Knowledge Graph for brand presence.

    Args:
        brand_name: Brand/company name to search
        api_key: Google Knowledge Graph API key (defaults to GOOGLE_KG_API_KEY env var)

    Returns:
        KnowledgeSource with results
    """
    api_key = api_key or os.environ.get('GOOGLE_KG_API_KEY')

    if not api_key:
        # STUB: Return placeholder when no API key
        return KnowledgeSource(
            source="google_kg",
            found=False,
            error="GOOGLE_KG_API_KEY not set - skipping Google Knowledge Graph check"
        )

    try:
        import requests

        url = "https://kgsearch.googleapis.com/v1/entities:search"
        params = {
            "query": brand_name,
            "key": api_key,
            "limit": 5,
            "types": "Organization,Corporation,LocalBusiness"
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
                            "detailed_description": result.get("detailedDescription", {}).get("articleBody"),
                            "types": result.get("@type", []),
                            "score": item.get("resultScore", 0)
                        }
                    )

            # No exact match but found related
            return KnowledgeSource(
                source="google_kg",
                found=False,
                data={"related_entities": [item.get("result", {}).get("name") for item in items[:3]]}
            )
        else:
            return KnowledgeSource(
                source="google_kg",
                found=False
            )

    except ImportError:
        return KnowledgeSource(
            source="google_kg",
            found=False,
            error="requests package not installed"
        )
    except Exception as e:
        return KnowledgeSource(
            source="google_kg",
            found=False,
            error=str(e)
        )


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

        # Search Wikipedia API
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": brand_name,
            "format": "json",
            "srlimit": 5
        }

        response = requests.get(search_url, params=search_params, timeout=10)
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
                        "format": "json"
                    }

                    extract_response = requests.get(search_url, params=extract_params, timeout=10)
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
                            "extract": page_data.get("extract", "")[:500]  # First 500 chars
                        }
                    )

            # No exact match
            return KnowledgeSource(
                source="wikipedia",
                found=False,
                data={"related_articles": [r["title"] for r in results[:3]]}
            )
        else:
            return KnowledgeSource(
                source="wikipedia",
                found=False
            )

    except ImportError:
        return KnowledgeSource(
            source="wikipedia",
            found=False,
            error="requests package not installed"
        )
    except Exception as e:
        return KnowledgeSource(
            source="wikipedia",
            found=False,
            error=str(e)
        )


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

        # Search Wikidata API
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": brand_name,
            "language": "en",
            "format": "json",
            "limit": 5,
            "type": "item"
        }

        response = requests.get(url, params=params, timeout=10)
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
                            "aliases": result.get("aliases", [])
                        }
                    )

            # No exact match
            return KnowledgeSource(
                source="wikidata",
                found=False,
                data={"related_items": [r.get("label") for r in results[:3]]}
            )
        else:
            return KnowledgeSource(
                source="wikidata",
                found=False
            )

    except ImportError:
        return KnowledgeSource(
            source="wikidata",
            found=False,
            error="requests package not installed"
        )
    except Exception as e:
        return KnowledgeSource(
            source="wikidata",
            found=False,
            error=str(e)
        )


def check_crunchbase(brand_name: str, api_key: Optional[str] = None) -> KnowledgeSource:
    """
    Check Crunchbase for brand presence.

    Args:
        brand_name: Brand/company name to search
        api_key: Crunchbase API key (defaults to CRUNCHBASE_API_KEY env var)

    Returns:
        KnowledgeSource with results
    """
    api_key = api_key or os.environ.get('CRUNCHBASE_API_KEY')

    if not api_key:
        # STUB: Return placeholder when no API key
        # Can still check if a Crunchbase page exists via web search
        return KnowledgeSource(
            source="crunchbase",
            found=False,
            error="CRUNCHBASE_API_KEY not set - skipping Crunchbase check"
        )

    # STUB: Crunchbase API integration
    # TODO: Implement when API key is available
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
        error="Crunchbase API integration not yet implemented"
    )


def check_linkedin(brand_name: str) -> KnowledgeSource:
    """
    Check if brand has LinkedIn company page (via search, no API needed).

    Args:
        brand_name: Brand/company name to search

    Returns:
        KnowledgeSource with results
    """
    # Note: LinkedIn doesn't have a public API for this
    # This is a placeholder - in production, you might use web scraping
    # or a third-party service

    # Construct expected LinkedIn URL
    slug = brand_name.lower().replace(" ", "-").replace(".", "")
    expected_url = f"https://www.linkedin.com/company/{slug}"

    return KnowledgeSource(
        source="linkedin",
        found=False,  # Can't verify without scraping
        url=expected_url,
        error="LinkedIn presence check requires manual verification or third-party service"
    )


def check_all_sources(
    brand_name: str,
    target_url: Optional[str] = None
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

    # Count successes
    found_count = sum(1 for s in sources.values() if s.found)
    total_sources = len([s for s in sources.values() if s.error is None or "not set" not in s.error])

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
                findings.append(f"  Related: {', '.join(source.data['related_entities'][:3])}")

    # Calculate score (0-15)
    # Wikipedia + Google KG = 12 points, others = 3 points
    score = 0

    if sources["wikipedia"].found:
        score += 6
        findings.append("Wikipedia presence: Strong authority signal for AI systems")
    else:
        findings.append("Recommendation: Create Wikipedia article to improve AI awareness")

    if sources["google_kg"].found:
        score += 6
        findings.append("Google Knowledge Graph: Directly feeds Google's AI systems")
    elif sources["google_kg"].error and "not set" in sources["google_kg"].error:
        score += 3  # Give partial credit if we couldn't check
    else:
        findings.append("Recommendation: Improve structured data to appear in Google KG")

    if sources["wikidata"].found:
        score += 2
        findings.append("Wikidata: Feeds multiple AI knowledge bases")

    if sources["crunchbase"].found:
        score += 1

    return {
        "score": min(15, score),
        "max": 15,
        "findings": findings,
        "sources": {
            name: {
                "found": s.found,
                "url": s.url,
                "error": s.error,
                "data": s.data
            }
            for name, s in sources.items()
        },
        "details": {
            "sources_checked": total_sources,
            "sources_found": found_count,
            "presence_rate": found_count / total_sources if total_sources > 0 else 0
        }
    }


__all__ = [
    'KnowledgeSource',
    'check_google_knowledge_graph',
    'check_wikipedia',
    'check_wikidata',
    'check_crunchbase',
    'check_linkedin',
    'check_all_sources'
]
