"""
Analyze Internal Links

Evaluate internal linking structure, orphan pages, and link equity flow.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urljoin, urlparse


@dataclass
class InternalLink:
    """An internal link found on the site."""
    source_url: str
    target_url: str
    anchor_text: str
    is_navigation: bool


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


def extract_internal_links(
    html: str,
    page_url: str,
    base_url: str
) -> list[InternalLink]:
    """
    Extract all internal links from a page.

    Args:
        html: HTML content
        page_url: URL of the current page
        base_url: Base URL of the site

    Returns:
        List of InternalLink objects
    """
    links = []
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    # Find all anchor tags
    link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    matches = re.findall(link_pattern, html, re.IGNORECASE | re.DOTALL)

    # Check if link is in navigation
    nav_section = ""
    nav_match = re.search(
        r'<(?:nav|header)[^>]*>.*?</(?:nav|header)>',
        html,
        re.IGNORECASE | re.DOTALL
    )
    if nav_match:
        nav_section = nav_match.group(0).lower()

    for href, anchor in matches:
        # Resolve relative URLs
        full_url = urljoin(page_url, href)
        parsed = urlparse(full_url)

        # Check if internal
        if parsed.netloc == base_domain:
            # Clean anchor text
            anchor_clean = re.sub(r'<[^>]+>', '', anchor)
            anchor_clean = re.sub(r'\s+', ' ', anchor_clean).strip()

            # Check if in navigation
            is_nav = href.lower() in nav_section

            # Normalize URL (remove fragments, trailing slashes)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            normalized = normalized.rstrip('/')

            links.append(InternalLink(
                source_url=page_url,
                target_url=normalized,
                anchor_text=anchor_clean[:100],  # Limit length
                is_navigation=is_nav
            ))

    return links


def find_orphan_pages(
    all_pages: set[str],
    linked_pages: set[str],
    base_url: str
) -> list[str]:
    """
    Find pages that have no internal links pointing to them.

    Args:
        all_pages: Set of all discovered page URLs
        linked_pages: Set of pages that have incoming internal links
        base_url: Base URL of the site

    Returns:
        List of orphan page URLs
    """
    orphans = []

    for page in all_pages:
        if page not in linked_pages:
            # Don't count homepage as orphan
            parsed = urlparse(page)
            if parsed.path not in ['', '/', '/index.html', '/index.php']:
                orphans.append(page)

    return orphans


def analyze_anchor_text(links: list[InternalLink]) -> dict[str, Any]:
    """
    Analyze anchor text distribution and diversity.

    Args:
        links: List of internal links

    Returns:
        Dict with anchor text analysis
    """
    result = {
        "total_links": len(links),
        "unique_anchors": 0,
        "empty_anchors": 0,
        "generic_anchors": 0,
        "anchor_distribution": {},
        "issues": []
    }

    generic_phrases = [
        'click here', 'read more', 'learn more', 'here', 'this',
        'link', 'more', 'continue', 'see more'
    ]

    anchor_counts = defaultdict(int)

    for link in links:
        anchor = link.anchor_text.lower().strip()

        if not anchor:
            result["empty_anchors"] += 1
        elif anchor in generic_phrases:
            result["generic_anchors"] += 1

        anchor_counts[anchor] += 1

    result["unique_anchors"] = len(anchor_counts)

    # Top anchors
    sorted_anchors = sorted(anchor_counts.items(), key=lambda x: x[1], reverse=True)
    result["anchor_distribution"] = dict(sorted_anchors[:10])

    # Issues
    if result["empty_anchors"] > len(links) * 0.1:
        result["issues"].append({
            "severity": "medium",
            "description": f"{result['empty_anchors']} links have empty anchor text",
            "recommendation": "Add descriptive anchor text to image links"
        })

    if result["generic_anchors"] > len(links) * 0.2:
        result["issues"].append({
            "severity": "low",
            "description": f"{result['generic_anchors']} links use generic anchor text",
            "recommendation": "Use descriptive, keyword-rich anchor text"
        })

    # Check for over-optimization (same anchor used too much)
    if sorted_anchors:
        top_anchor, top_count = sorted_anchors[0]
        if top_count > len(links) * 0.3 and top_anchor not in ['', 'home']:
            result["issues"].append({
                "severity": "low",
                "description": f"Anchor '{top_anchor}' used {top_count} times (over-optimization risk)",
                "recommendation": "Vary anchor text for natural link profile"
            })

    return result


def calculate_link_equity_distribution(
    links: list[InternalLink],
    all_pages: set[str]
) -> dict[str, Any]:
    """
    Calculate how link equity flows through the site.

    Args:
        links: All internal links
        all_pages: All pages on the site

    Returns:
        Dict with link equity analysis
    """
    result = {
        "pages_analyzed": len(all_pages),
        "incoming_links": {},
        "outgoing_links": {},
        "high_authority_pages": [],
        "low_authority_pages": [],
        "issues": []
    }

    incoming = defaultdict(int)
    outgoing = defaultdict(int)

    for link in links:
        incoming[link.target_url] += 1
        outgoing[link.source_url] += 1

    result["incoming_links"] = dict(incoming)
    result["outgoing_links"] = dict(outgoing)

    # Find high and low authority pages
    if incoming:
        avg_incoming = sum(incoming.values()) / len(incoming)

        for page, count in incoming.items():
            if count >= avg_incoming * 2:
                result["high_authority_pages"].append({
                    "url": page,
                    "incoming_links": count
                })
            elif count <= 1:
                result["low_authority_pages"].append({
                    "url": page,
                    "incoming_links": count
                })

        result["high_authority_pages"].sort(key=lambda x: x["incoming_links"], reverse=True)
        result["low_authority_pages"] = result["low_authority_pages"][:10]

    # Check for issues
    if result["low_authority_pages"]:
        result["issues"].append({
            "severity": "medium",
            "description": f"{len(result['low_authority_pages'])} pages have very few internal links",
            "recommendation": "Add more internal links to important pages"
        })

    return result


def calculate_click_depth(
    base_url: str,
    links: list[InternalLink],
    max_depth: int = 5
) -> dict[str, Any]:
    """
    Calculate click depth (how many clicks from homepage to reach each page).

    Args:
        base_url: Homepage URL
        links: All internal links
        max_depth: Maximum depth to analyze

    Returns:
        Dict with click depth analysis
    """
    result = {
        "depth_distribution": defaultdict(list),
        "unreachable_pages": [],
        "deep_pages": [],  # Pages >3 clicks deep
        "issues": []
    }

    # Build adjacency list
    graph = defaultdict(set)
    all_pages = set()

    for link in links:
        graph[link.source_url].add(link.target_url)
        all_pages.add(link.source_url)
        all_pages.add(link.target_url)

    # BFS from homepage
    normalized_base = base_url.rstrip('/')
    visited = {normalized_base: 0}
    queue = [normalized_base]

    while queue:
        current = queue.pop(0)
        current_depth = visited[current]

        if current_depth >= max_depth:
            continue

        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                visited[neighbor] = current_depth + 1
                queue.append(neighbor)

    # Categorize pages by depth
    for page, depth in visited.items():
        result["depth_distribution"][depth].append(page)
        if depth > 3:
            result["deep_pages"].append({"url": page, "depth": depth})

    # Find unreachable pages
    for page in all_pages:
        if page not in visited and page != normalized_base:
            result["unreachable_pages"].append(page)

    # Convert defaultdict to regular dict
    result["depth_distribution"] = dict(result["depth_distribution"])

    # Issues
    if result["unreachable_pages"]:
        result["issues"].append({
            "severity": "high",
            "description": f"{len(result['unreachable_pages'])} pages not reachable from homepage",
            "recommendation": "Add internal links to make all pages accessible"
        })

    if len(result["deep_pages"]) > len(all_pages) * 0.2:
        result["issues"].append({
            "severity": "medium",
            "description": f"{len(result['deep_pages'])} pages are more than 3 clicks from homepage",
            "recommendation": "Flatten site architecture or add shortcuts to deep content"
        })

    return result


def analyze_internal_links(
    url: str,
    crawl_depth: int = 30
) -> dict[str, Any]:
    """
    Complete internal linking analysis.

    Args:
        url: Base URL to analyze
        crawl_depth: Number of pages to crawl

    Returns:
        Dict with complete internal link analysis (0-10 score)
    """
    result = {
        "score": 0,
        "max": 10,
        "pages_crawled": 0,
        "total_links": 0,
        "orphan_pages": [],
        "anchor_analysis": {},
        "equity_distribution": {},
        "click_depth": {},
        "issues": [],
        "findings": []
    }

    # Crawl site to collect links
    all_links = []
    crawled_pages = set()
    pages_to_crawl = [url]
    all_discovered_pages = set()

    urlparse(url)

    while pages_to_crawl and len(crawled_pages) < crawl_depth:
        current_url = pages_to_crawl.pop(0)

        if current_url in crawled_pages:
            continue

        html = fetch_page(current_url)
        if not html:
            continue

        crawled_pages.add(current_url)
        all_discovered_pages.add(current_url)

        # Extract links from this page
        page_links = extract_internal_links(html, current_url, url)
        all_links.extend(page_links)

        # Add new URLs to crawl queue
        for link in page_links:
            all_discovered_pages.add(link.target_url)
            if link.target_url not in crawled_pages:
                pages_to_crawl.append(link.target_url)

    result["pages_crawled"] = len(crawled_pages)
    result["total_links"] = len(all_links)
    result["findings"].append(f"Crawled {len(crawled_pages)} pages, found {len(all_links)} internal links")

    if not all_links:
        result["issues"].append({
            "severity": "high",
            "description": "No internal links found",
            "recommendation": "Add internal links to connect your content"
        })
        result["score"] = 0
        return result

    # Find orphan pages
    linked_pages = {link.target_url for link in all_links}
    result["orphan_pages"] = find_orphan_pages(all_discovered_pages, linked_pages, url)

    if result["orphan_pages"]:
        result["findings"].append(f"Found {len(result['orphan_pages'])} orphan pages")
        result["issues"].append({
            "severity": "medium",
            "description": f"{len(result['orphan_pages'])} pages have no internal links pointing to them",
            "recommendation": "Add internal links to orphan pages"
        })

    # Analyze anchor text
    result["anchor_analysis"] = analyze_anchor_text(all_links)
    result["issues"].extend(result["anchor_analysis"].get("issues", []))

    # Analyze link equity distribution
    result["equity_distribution"] = calculate_link_equity_distribution(all_links, all_discovered_pages)
    result["issues"].extend(result["equity_distribution"].get("issues", []))

    # Calculate click depth
    result["click_depth"] = calculate_click_depth(url, all_links)
    result["issues"].extend(result["click_depth"].get("issues", []))

    # Calculate score (0-10)
    score = 10

    # Orphan pages penalty
    orphan_ratio = len(result["orphan_pages"]) / len(all_discovered_pages) if all_discovered_pages else 0
    if orphan_ratio > 0.3:
        score -= 4
    elif orphan_ratio > 0.1:
        score -= 2

    # Click depth penalty
    deep_ratio = len(result["click_depth"].get("deep_pages", [])) / len(crawled_pages) if crawled_pages else 0
    if deep_ratio > 0.3:
        score -= 2
    elif deep_ratio > 0.1:
        score -= 1

    # Anchor text issues
    if result["anchor_analysis"].get("empty_anchors", 0) > len(all_links) * 0.2:
        score -= 1
    if result["anchor_analysis"].get("generic_anchors", 0) > len(all_links) * 0.3:
        score -= 1

    # Unreachable pages
    if result["click_depth"].get("unreachable_pages"):
        score -= 2

    result["score"] = max(0, score)

    return result


__all__ = [
    'InternalLink',
    'extract_internal_links',
    'find_orphan_pages',
    'analyze_anchor_text',
    'calculate_link_equity_distribution',
    'calculate_click_depth',
    'analyze_internal_links'
]
