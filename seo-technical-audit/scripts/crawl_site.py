"""
Crawl Site Analysis

Analyze robots.txt, sitemaps, and crawlability of a website.
"""

import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET

# Cache imports with fallback
try:
    from seo_health_report.scripts.cache import cached, TTL_HTTP_FETCH
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False
    def cached(*args, **kwargs):
        def decorator(func): 
            return func
        return decorator
    TTL_HTTP_FETCH = 0


@dataclass
class CrawlIssue:
    """A crawlability issue found during analysis."""
    severity: str  # "critical", "high", "medium", "low"
    category: str
    description: str
    url: Optional[str] = None
    recommendation: str = ""


@cached("http_fetch", TTL_HTTP_FETCH)
def fetch_url(url: str, timeout: int = 30) -> Optional[str]:
    """
    Fetch content from a URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Response text or None if failed
    """
    try:
        import requests
        headers = {
            'User-Agent': 'SEO-Health-Report-Bot/1.0 (Technical Audit)'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except ImportError:
        print("Warning: requests package not installed")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def check_robots(url: str) -> Dict[str, Any]:
    """
    Analyze robots.txt file.

    Args:
        url: Base URL of the site

    Returns:
        Dict with robots.txt analysis
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    result = {
        "url": robots_url,
        "exists": False,
        "content": None,
        "rules": [],
        "sitemaps": [],
        "issues": [],
        "score": 0
    }

    content = fetch_url(robots_url)

    if not content:
        result["issues"].append(CrawlIssue(
            severity="medium",
            category="robots",
            description="robots.txt not found or not accessible",
            url=robots_url,
            recommendation="Create a robots.txt file at the root of your domain"
        ))
        return result

    result["exists"] = True
    result["content"] = content

    # Parse robots.txt
    current_user_agent = None
    rules = []

    for line in content.split('\n'):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue

        # Parse directive
        if ':' in line:
            directive, value = line.split(':', 1)
            directive = directive.strip().lower()
            value = value.strip()

            if directive == 'user-agent':
                current_user_agent = value
            elif directive == 'disallow':
                rules.append({
                    "user_agent": current_user_agent or "*",
                    "type": "disallow",
                    "path": value
                })
            elif directive == 'allow':
                rules.append({
                    "user_agent": current_user_agent or "*",
                    "type": "allow",
                    "path": value
                })
            elif directive == 'sitemap':
                result["sitemaps"].append(value)
            elif directive == 'crawl-delay':
                result["issues"].append(CrawlIssue(
                    severity="low",
                    category="robots",
                    description=f"Crawl-delay directive found ({value}s)",
                    recommendation="Crawl-delay may slow down indexing; consider removing if not needed"
                ))

    result["rules"] = rules

    # Analyze rules for issues
    for rule in rules:
        if rule["type"] == "disallow":
            path = rule["path"]

            # Check for overly broad blocks
            if path == "/" and rule["user_agent"] == "*":
                result["issues"].append(CrawlIssue(
                    severity="critical",
                    category="robots",
                    description="Entire site blocked from crawling (Disallow: /)",
                    recommendation="Remove 'Disallow: /' unless intentional"
                ))
            elif path in ["/wp-admin", "/admin", "/cgi-bin"]:
                pass  # These are fine to block
            elif "/?" in path or "/*?" in path:
                pass  # Blocking parameters is often fine
            elif path.endswith(".js") or path.endswith(".css"):
                result["issues"].append(CrawlIssue(
                    severity="medium",
                    category="robots",
                    description=f"Blocking JS/CSS files: {path}",
                    recommendation="Allow crawlers to access JS/CSS for proper rendering"
                ))

    # Check for sitemap declaration
    if not result["sitemaps"]:
        result["issues"].append(CrawlIssue(
            severity="low",
            category="robots",
            description="No sitemap declared in robots.txt",
            recommendation="Add 'Sitemap: https://yoursite.com/sitemap.xml' to robots.txt"
        ))

    # Calculate score
    score = 20  # Start with max
    for issue in result["issues"]:
        if issue.severity == "critical":
            score -= 10
        elif issue.severity == "high":
            score -= 5
        elif issue.severity == "medium":
            score -= 2
        elif issue.severity == "low":
            score -= 1

    result["score"] = max(0, score)

    # Convert issues to dict format
    result["issues"] = [
        {
            "severity": i.severity,
            "category": i.category,
            "description": i.description,
            "url": i.url,
            "recommendation": i.recommendation
        }
        for i in result["issues"]
    ]

    return result


def check_sitemaps(url: str, sitemap_urls: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze XML sitemaps.

    Args:
        url: Base URL of the site
        sitemap_urls: Optional list of known sitemap URLs

    Returns:
        Dict with sitemap analysis
    """
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Default sitemap locations to check
    default_locations = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap/sitemap.xml",
        "/sitemaps/sitemap.xml"
    ]

    result = {
        "sitemaps_found": [],
        "total_urls": 0,
        "issues": [],
        "score": 0
    }

    sitemaps_to_check = []

    if sitemap_urls:
        sitemaps_to_check.extend(sitemap_urls)
    else:
        for loc in default_locations:
            sitemaps_to_check.append(urljoin(base_url, loc))

    found_urls: Set[str] = set()

    for sitemap_url in sitemaps_to_check:
        content = fetch_url(sitemap_url)

        if not content:
            continue

        sitemap_data = {
            "url": sitemap_url,
            "type": "unknown",
            "urls": [],
            "child_sitemaps": []
        }

        try:
            # Parse XML
            root = ET.fromstring(content)

            # Remove namespace for easier parsing
            namespace = ""
            if root.tag.startswith("{"):
                namespace = root.tag.split("}")[0] + "}"

            # Check if it's a sitemap index
            if "sitemapindex" in root.tag.lower():
                sitemap_data["type"] = "index"

                for sitemap in root.findall(f".//{namespace}sitemap"):
                    loc = sitemap.find(f"{namespace}loc")
                    if loc is not None and loc.text:
                        sitemap_data["child_sitemaps"].append(loc.text)
                        # Recursively check child sitemaps
                        sitemaps_to_check.append(loc.text)

            elif "urlset" in root.tag.lower():
                sitemap_data["type"] = "urlset"

                for url_elem in root.findall(f".//{namespace}url"):
                    loc = url_elem.find(f"{namespace}loc")
                    if loc is not None and loc.text:
                        sitemap_data["urls"].append(loc.text)
                        found_urls.add(loc.text)

            result["sitemaps_found"].append(sitemap_data)

        except ET.ParseError as e:
            result["issues"].append({
                "severity": "high",
                "category": "sitemap",
                "description": f"Sitemap XML parse error: {sitemap_url}",
                "url": sitemap_url,
                "recommendation": "Fix XML syntax errors in sitemap"
            })

    result["total_urls"] = len(found_urls)

    # Check for issues
    if not result["sitemaps_found"]:
        result["issues"].append({
            "severity": "high",
            "category": "sitemap",
            "description": "No sitemap found",
            "recommendation": "Create and submit an XML sitemap"
        })

    # Check for large sitemaps
    for sitemap in result["sitemaps_found"]:
        if len(sitemap.get("urls", [])) > 50000:
            result["issues"].append({
                "severity": "medium",
                "category": "sitemap",
                "description": f"Sitemap exceeds 50,000 URLs: {sitemap['url']}",
                "url": sitemap["url"],
                "recommendation": "Split into multiple sitemaps using a sitemap index"
            })

    # Calculate score (contributes to indexing score)
    score = 15
    for issue in result["issues"]:
        if issue["severity"] == "critical":
            score -= 8
        elif issue["severity"] == "high":
            score -= 4
        elif issue["severity"] == "medium":
            score -= 2
        elif issue["severity"] == "low":
            score -= 1

    result["score"] = max(0, score)

    return result


def check_redirects(url: str, max_chain: int = 5) -> Dict[str, Any]:
    """
    Check for redirect chains and issues.

    Args:
        url: URL to check
        max_chain: Maximum redirect chain to follow

    Returns:
        Dict with redirect analysis
    """
    result = {
        "final_url": url,
        "chain": [],
        "chain_length": 0,
        "issues": []
    }

    try:
        import requests

        headers = {
            'User-Agent': 'SEO-Health-Report-Bot/1.0'
        }

        current_url = url
        chain = []

        for _ in range(max_chain):
            response = requests.head(
                current_url,
                headers=headers,
                allow_redirects=False,
                timeout=10
            )

            chain.append({
                "url": current_url,
                "status_code": response.status_code
            })

            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location')
                if location:
                    # Handle relative URLs
                    if not location.startswith('http'):
                        location = urljoin(current_url, location)
                    current_url = location
                else:
                    break
            else:
                break

        result["chain"] = chain
        result["chain_length"] = len(chain)
        result["final_url"] = current_url

        # Check for issues
        if len(chain) > 3:
            result["issues"].append({
                "severity": "medium",
                "category": "redirects",
                "description": f"Long redirect chain ({len(chain)} hops)",
                "url": url,
                "recommendation": "Reduce redirect chain to 1-2 hops maximum"
            })

        # Check for redirect loops (same URL appearing twice)
        urls_seen = set()
        for item in chain:
            if item["url"] in urls_seen:
                result["issues"].append({
                    "severity": "critical",
                    "category": "redirects",
                    "description": "Redirect loop detected",
                    "url": url,
                    "recommendation": "Fix redirect configuration to prevent loops"
                })
                break
            urls_seen.add(item["url"])

        # Check for 302 instead of 301
        for item in chain[:-1]:  # All except final
            if item["status_code"] == 302:
                result["issues"].append({
                    "severity": "low",
                    "category": "redirects",
                    "description": f"302 redirect used instead of 301 at {item['url']}",
                    "url": item["url"],
                    "recommendation": "Use 301 for permanent redirects to pass SEO value"
                })

    except ImportError:
        result["issues"].append({
            "severity": "low",
            "category": "redirects",
            "description": "requests package not installed - redirect check skipped"
        })
    except Exception as e:
        result["issues"].append({
            "severity": "low",
            "category": "redirects",
            "description": f"Error checking redirects: {str(e)}"
        })

    return result


def analyze_meta_robots(html: str, url: str) -> Dict[str, Any]:
    """
    Analyze meta robots tags in HTML.

    Args:
        html: HTML content
        url: Page URL

    Returns:
        Dict with meta robots analysis
    """
    result = {
        "directives": [],
        "indexable": True,
        "followable": True,
        "issues": []
    }

    # Find meta robots tags
    robots_pattern = r'<meta[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']'
    matches = re.findall(robots_pattern, html, re.IGNORECASE)

    # Also check for reverse order
    robots_pattern_alt = r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']robots["\']'
    matches.extend(re.findall(robots_pattern_alt, html, re.IGNORECASE))

    for match in matches:
        directives = [d.strip().lower() for d in match.split(',')]
        result["directives"].extend(directives)

        if 'noindex' in directives:
            result["indexable"] = False
            result["issues"].append({
                "severity": "high",
                "category": "meta_robots",
                "description": "Page has noindex directive",
                "url": url,
                "recommendation": "Remove noindex if page should be indexed"
            })

        if 'nofollow' in directives:
            result["followable"] = False
            result["issues"].append({
                "severity": "medium",
                "category": "meta_robots",
                "description": "Page has nofollow directive",
                "url": url,
                "recommendation": "Remove nofollow if links should be followed"
            })

    return result


def analyze_canonical(html: str, page_url: str) -> Dict[str, Any]:
    """
    Analyze canonical tag.

    Args:
        html: HTML content
        page_url: URL of the page

    Returns:
        Dict with canonical analysis
    """
    result = {
        "canonical_url": None,
        "is_self_referencing": False,
        "issues": []
    }

    # Find canonical tag
    canonical_pattern = r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']'
    match = re.search(canonical_pattern, html, re.IGNORECASE)

    if not match:
        # Try reverse order
        canonical_pattern_alt = r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']'
        match = re.search(canonical_pattern_alt, html, re.IGNORECASE)

    if match:
        result["canonical_url"] = match.group(1)

        # Check if self-referencing
        canonical = result["canonical_url"].rstrip('/')
        page = page_url.rstrip('/')

        if canonical == page:
            result["is_self_referencing"] = True
        else:
            # Different canonical - might be intentional or an issue
            result["issues"].append({
                "severity": "low",
                "category": "canonical",
                "description": f"Canonical points to different URL: {canonical}",
                "url": page_url,
                "recommendation": "Verify this is intentional cross-canonical"
            })
    else:
        result["issues"].append({
            "severity": "medium",
            "category": "canonical",
            "description": "No canonical tag found",
            "url": page_url,
            "recommendation": "Add self-referencing canonical tag"
        })

    return result


def analyze_internal_links(html: str, page_url: str, base_url: str) -> Dict[str, Any]:
    """
    Analyze internal links on a page.

    Args:
        html: HTML content
        page_url: URL of the page being analyzed
        base_url: Base URL of the site

    Returns:
        Dict with internal link analysis
    """
    result = {
        "total_links": 0,
        "internal_links": 0,
        "external_links": 0,
        "nofollow_links": 0,
        "broken_links": [],  # Would need actual checking
        "issues": []
    }

    # Find all links
    link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    matches = re.findall(link_pattern, html, re.IGNORECASE | re.DOTALL)

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    for href, anchor_text in matches:
        result["total_links"] += 1

        # Skip javascript, mailto, tel links
        if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            continue

        # Resolve relative URLs
        full_url = urljoin(page_url, href)
        parsed = urlparse(full_url)

        if parsed.netloc == base_domain:
            result["internal_links"] += 1
        else:
            result["external_links"] += 1

    # Check for issues
    if result["internal_links"] == 0:
        result["issues"].append({
            "severity": "medium",
            "category": "internal_links",
            "description": "No internal links found on page",
            "url": page_url,
            "recommendation": "Add internal links to help crawlers discover content"
        })

    if result["total_links"] > 100:
        result["issues"].append({
            "severity": "low",
            "category": "internal_links",
            "description": f"High number of links on page ({result['total_links']})",
            "url": page_url,
            "recommendation": "Consider reducing number of links for better crawl priority"
        })

    return result


def analyze_crawlability(
    url: str,
    depth: int = 50,
    check_pages: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive crawlability analysis.

    Args:
        url: Base URL to analyze
        depth: Maximum pages to crawl
        check_pages: Whether to crawl and check individual pages

    Returns:
        Dict with complete crawlability analysis
    """
    result = {
        "score": 0,
        "max": 20,
        "robots": {},
        "sitemaps": {},
        "redirects": {},
        "pages_analyzed": 0,
        "issues": [],
        "findings": []
    }

    # Check robots.txt
    robots_result = check_robots(url)
    result["robots"] = robots_result
    result["issues"].extend(robots_result.get("issues", []))

    # Check sitemaps
    sitemap_urls = robots_result.get("sitemaps", [])
    sitemaps_result = check_sitemaps(url, sitemap_urls)
    result["sitemaps"] = sitemaps_result
    result["issues"].extend(sitemaps_result.get("issues", []))

    # Check redirects on main URL
    redirects_result = check_redirects(url)
    result["redirects"] = redirects_result
    result["issues"].extend(redirects_result.get("issues", []))

    # Check main page
    if check_pages:
        html = fetch_url(url)
        if html:
            result["pages_analyzed"] = 1

            # Check meta robots
            meta_robots = analyze_meta_robots(html, url)
            result["issues"].extend(meta_robots.get("issues", []))

            # Check canonical
            canonical = analyze_canonical(html, url)
            result["issues"].extend(canonical.get("issues", []))

            # Check internal links
            links = analyze_internal_links(html, url, url)
            result["issues"].extend(links.get("issues", []))

    # Generate findings
    if robots_result.get("exists"):
        result["findings"].append("robots.txt found and accessible")
    else:
        result["findings"].append("robots.txt not found")

    if sitemaps_result.get("sitemaps_found"):
        result["findings"].append(f"Found {len(sitemaps_result['sitemaps_found'])} sitemap(s) with {sitemaps_result['total_urls']} URLs")
    else:
        result["findings"].append("No sitemap found")

    if redirects_result.get("chain_length", 0) > 1:
        result["findings"].append(f"Homepage has {redirects_result['chain_length']}-hop redirect chain")
    else:
        result["findings"].append("Homepage accessible without redirect chain")

    # Calculate score
    score = 20
    for issue in result["issues"]:
        severity = issue.get("severity", "low")
        if severity == "critical":
            score -= 10
        elif severity == "high":
            score -= 5
        elif severity == "medium":
            score -= 2
        elif severity == "low":
            score -= 1

    result["score"] = max(0, min(20, score))

    return result


__all__ = [
    'CrawlIssue',
    'fetch_url',
    'check_robots',
    'check_sitemaps',
    'check_redirects',
    'analyze_meta_robots',
    'analyze_canonical',
    'analyze_internal_links',
    'analyze_crawlability'
]
