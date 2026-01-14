"""
Map Topics and Analyze Topical Authority

Identify topic clusters, semantic coverage, and content gaps.
"""

import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
from collections import defaultdict


@dataclass
class TopicCluster:
    """A topic cluster with pillar and supporting content."""
    topic: str
    pillar_url: Optional[str]
    supporting_urls: List[str]
    keyword_coverage: List[str]
    depth_score: int  # 1-5


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


def extract_keywords_from_content(html: str) -> List[str]:
    """
    Extract potential keywords from page content.

    Args:
        html: HTML content

    Returns:
        List of potential keywords/phrases
    """
    keywords = set()

    # Extract from title
    title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    if title_match:
        title = title_match.group(1)
        # Split title by common separators
        parts = re.split(r'[|\-–—:]', title)
        for part in parts:
            part = part.strip()
            if len(part) > 3 and len(part) < 60:
                keywords.add(part.lower())

    # Extract from h1, h2, h3
    heading_patterns = [r'<h1[^>]*>([^<]+)</h1>', r'<h2[^>]*>([^<]+)</h2>']
    for pattern in heading_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            match = re.sub(r'<[^>]+>', '', match).strip()
            if len(match) > 3 and len(match) < 100:
                keywords.add(match.lower())

    # Extract from meta description
    meta_desc = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)',
        html, re.IGNORECASE
    )
    if meta_desc:
        # Extract key phrases from description
        desc = meta_desc.group(1)
        # Simple n-gram extraction for 2-3 word phrases
        words = desc.lower().split()
        for i in range(len(words) - 1):
            phrase = ' '.join(words[i:i+2])
            if len(phrase) > 5:
                keywords.add(phrase)

    return list(keywords)[:20]  # Limit to top 20


def identify_topic_clusters(
    pages: List[Dict[str, Any]],
    primary_keywords: List[str]
) -> List[TopicCluster]:
    """
    Identify topic clusters from page data.

    Args:
        pages: List of page analysis results with URLs and keywords
        primary_keywords: Target keywords to cluster around

    Returns:
        List of TopicCluster objects
    """
    clusters = []

    def fuzzy_match(text: str, keyword: str) -> bool:
        """Check if text contains keyword or related terms."""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        # Exact match
        if keyword_lower in text_lower:
            return True
        
        # Check individual words (for multi-word keywords)
        keyword_words = keyword_lower.split()
        if len(keyword_words) > 1:
            # If most words match, consider it relevant
            matches = sum(1 for w in keyword_words if w in text_lower and len(w) > 3)
            if matches >= len(keyword_words) * 0.6:  # 60% of words match
                return True
        
        # Check for word stems (simple stemming)
        for kw_word in keyword_words:
            if len(kw_word) > 4:
                stem = kw_word[:4]  # Simple prefix matching
                if stem in text_lower:
                    return True
        
        return False

    for keyword in primary_keywords:
        keyword_lower = keyword.lower()

        # Find pillar (longest content about topic)
        pillar_url = None
        pillar_score = 0
        supporting_urls = []
        covered_keywords = [keyword]

        for page in pages:
            url = page.get("url", "")
            page_keywords = page.get("keywords", [])
            word_count = page.get("word_count", 0)
            title = page.get("title", "")
            content = page.get("content", "")

            # Check if page is relevant to this keyword (fuzzy matching)
            is_relevant = (
                fuzzy_match(url, keyword) or
                fuzzy_match(title, keyword) or
                any(fuzzy_match(kw, keyword) for kw in page_keywords) or
                (content and fuzzy_match(content[:500], keyword))  # Check first 500 chars
            )

            if is_relevant:
                # Score for pillar candidacy
                score = word_count

                if score > pillar_score:
                    # Demote current pillar to supporting
                    if pillar_url:
                        supporting_urls.append(pillar_url)
                    pillar_url = url
                    pillar_score = score
                else:
                    supporting_urls.append(url)

                # Track keyword variations covered
                for kw in page_keywords:
                    if fuzzy_match(kw, keyword) and kw not in covered_keywords:
                        covered_keywords.append(kw)

        # Calculate depth score (1-5)
        if pillar_url:
            depth = 1
            if pillar_score >= 2000:
                depth += 1
            if len(supporting_urls) >= 2:
                depth += 1
            if len(supporting_urls) >= 5:
                depth += 1
            if len(covered_keywords) >= 5:
                depth += 1

            clusters.append(TopicCluster(
                topic=keyword,
                pillar_url=pillar_url,
                supporting_urls=supporting_urls[:10],  # Limit
                keyword_coverage=covered_keywords[:10],
                depth_score=depth
            ))
        else:
            # Topic has no coverage
            clusters.append(TopicCluster(
                topic=keyword,
                pillar_url=None,
                supporting_urls=[],
                keyword_coverage=[],
                depth_score=0
            ))

    return clusters


def find_content_gaps(
    clusters: List[TopicCluster],
    primary_keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    Find content gaps based on topic cluster analysis.

    Args:
        clusters: List of TopicCluster objects
        primary_keywords: Target keywords

    Returns:
        List of content gap opportunities
    """
    gaps = []

    for cluster in clusters:
        if cluster.depth_score == 0:
            # No content for this topic
            gaps.append({
                "type": "missing_topic",
                "topic": cluster.topic,
                "priority": "high",
                "recommendation": f"Create pillar content for '{cluster.topic}'",
                "suggested_content": {
                    "type": "pillar",
                    "target_words": 2500,
                    "format": "comprehensive guide"
                }
            })
        elif cluster.depth_score <= 2:
            # Shallow coverage
            gaps.append({
                "type": "thin_coverage",
                "topic": cluster.topic,
                "priority": "medium",
                "recommendation": f"Expand coverage of '{cluster.topic}'",
                "suggested_content": {
                    "type": "supporting",
                    "count": 3 - len(cluster.supporting_urls),
                    "format": "supporting articles"
                }
            })

        # Check for missing supporting content
        if cluster.pillar_url and len(cluster.supporting_urls) < 3:
            gaps.append({
                "type": "needs_support",
                "topic": cluster.topic,
                "priority": "medium",
                "pillar_url": cluster.pillar_url,
                "recommendation": f"Add supporting content for '{cluster.topic}' pillar",
                "suggested_count": 3 - len(cluster.supporting_urls)
            })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))

    return gaps


def analyze_keyword_optimization(
    html: str,
    target_keywords: List[str]
) -> Dict[str, Any]:
    """
    Analyze how well a page is optimized for target keywords.

    Args:
        html: HTML content
        target_keywords: Keywords to check optimization for

    Returns:
        Dict with keyword optimization analysis
    """
    result = {
        "keywords_analyzed": [],
        "optimization_score": 0,
        "issues": [],
        "findings": []
    }

    html_lower = html.lower()

    for keyword in target_keywords:
        kw_lower = keyword.lower()

        kw_analysis = {
            "keyword": keyword,
            "in_title": False,
            "in_h1": False,
            "in_h2": False,
            "in_meta_description": False,
            "in_url": False,
            "in_first_paragraph": False,
            "density": 0,
            "score": 0
        }

        # Check title
        title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        if title_match and kw_lower in title_match.group(1).lower():
            kw_analysis["in_title"] = True
            kw_analysis["score"] += 2

        # Check H1
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
        if h1_match and kw_lower in h1_match.group(1).lower():
            kw_analysis["in_h1"] = True
            kw_analysis["score"] += 2

        # Check H2s
        h2_matches = re.findall(r'<h2[^>]*>([^<]+)</h2>', html, re.IGNORECASE)
        if any(kw_lower in h2.lower() for h2 in h2_matches):
            kw_analysis["in_h2"] = True
            kw_analysis["score"] += 1

        # Check meta description
        meta_match = re.search(
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)',
            html, re.IGNORECASE
        )
        if meta_match and kw_lower in meta_match.group(1).lower():
            kw_analysis["in_meta_description"] = True
            kw_analysis["score"] += 1

        # Calculate keyword density
        text = re.sub(r'<[^>]+>', ' ', html)
        text_lower = text.lower()
        word_count = len(text.split())
        keyword_count = text_lower.count(kw_lower)

        if word_count > 0:
            kw_analysis["density"] = round((keyword_count / word_count) * 100, 2)

            if 0.5 <= kw_analysis["density"] <= 2.5:
                kw_analysis["score"] += 1  # Good density
            elif kw_analysis["density"] > 3:
                result["issues"].append({
                    "severity": "low",
                    "description": f"Keyword '{keyword}' may be over-optimized ({kw_analysis['density']}%)"
                })

        result["keywords_analyzed"].append(kw_analysis)

    # Calculate overall optimization score
    if result["keywords_analyzed"]:
        total_score = sum(kw["score"] for kw in result["keywords_analyzed"])
        max_score = len(result["keywords_analyzed"]) * 7  # Max 7 points per keyword
        result["optimization_score"] = round((total_score / max_score) * 100)

    return result


def analyze_topical_coverage(
    url: str,
    primary_keywords: List[str],
    crawl_depth: int = 20
) -> Dict[str, Any]:
    """
    Analyze topical coverage and authority.

    Args:
        url: Base URL to analyze
        primary_keywords: Target keywords
        crawl_depth: Number of pages to analyze

    Returns:
        Dict with topical authority analysis (0-15 score)
    """
    result = {
        "score": 0,
        "max": 15,
        "topics_covered": 0,
        "clusters": [],
        "content_gaps": [],
        "keyword_optimization": {},
        "issues": [],
        "findings": []
    }

    # Fetch and analyze homepage
    html = fetch_page(url)
    if not html:
        result["issues"].append({
            "severity": "high",
            "description": "Could not fetch homepage"
        })
        return result

    # Extract internal links to crawl
    link_pattern = r'href=["\']([^"\']+)["\']'
    links = re.findall(link_pattern, html, re.IGNORECASE)

    parsed_base = urlparse(url)
    internal_urls = [url]  # Start with homepage

    for link in links:
        full_url = urljoin(url, link)
        parsed = urlparse(full_url)

        if parsed.netloc == parsed_base.netloc:
            # Skip common non-content URLs
            skip_patterns = [
                r'/wp-', r'/admin', r'/cart', r'/checkout',
                r'/login', r'/register', r'\?', r'#',
                r'\.(?:jpg|png|gif|css|js|pdf)$'
            ]
            if not any(re.search(p, full_url, re.IGNORECASE) for p in skip_patterns):
                if full_url not in internal_urls:
                    internal_urls.append(full_url)

        if len(internal_urls) >= crawl_depth:
            break

    # Analyze each page
    pages = []
    for page_url in internal_urls[:crawl_depth]:
        page_html = fetch_page(page_url)
        if page_html:
            # Extract title
            title_match = re.search(r'<title>([^<]+)</title>', page_html, re.IGNORECASE)
            title = title_match.group(1) if title_match else ""

            # Extract text and count words
            text = re.sub(r'<[^>]+>', ' ', page_html)
            text = re.sub(r'\s+', ' ', text)
            word_count = len(text.split())

            # Extract keywords
            keywords = extract_keywords_from_content(page_html)

            pages.append({
                "url": page_url,
                "title": title,
                "word_count": word_count,
                "keywords": keywords
            })

    result["findings"].append(f"Analyzed {len(pages)} pages")

    # Identify topic clusters
    clusters = identify_topic_clusters(pages, primary_keywords)
    result["clusters"] = [
        {
            "topic": c.topic,
            "pillar_url": c.pillar_url,
            "supporting_count": len(c.supporting_urls),
            "depth_score": c.depth_score
        }
        for c in clusters
    ]

    # Count topics covered
    result["topics_covered"] = sum(1 for c in clusters if c.depth_score > 0)
    result["findings"].append(f"Covering {result['topics_covered']}/{len(primary_keywords)} target topics")

    # Find content gaps
    result["content_gaps"] = find_content_gaps(clusters, primary_keywords)

    if result["content_gaps"]:
        result["findings"].append(f"Found {len(result['content_gaps'])} content gaps")

    # Analyze keyword optimization on homepage
    result["keyword_optimization"] = analyze_keyword_optimization(html, primary_keywords)

    # Calculate score (0-15)
    score = 0

    # Topic coverage (0-8)
    coverage_ratio = result["topics_covered"] / len(primary_keywords) if primary_keywords else 0
    if coverage_ratio >= 0.8:
        score += 8
    elif coverage_ratio >= 0.6:
        score += 6
    elif coverage_ratio >= 0.4:
        score += 4
    elif coverage_ratio >= 0.2:
        score += 2

    # Cluster depth (0-4)
    avg_depth = sum(c.depth_score for c in clusters) / len(clusters) if clusters else 0
    if avg_depth >= 4:
        score += 4
    elif avg_depth >= 3:
        score += 3
    elif avg_depth >= 2:
        score += 2
    elif avg_depth >= 1:
        score += 1

    # Keyword optimization (0-3)
    opt_score = result["keyword_optimization"].get("optimization_score", 0)
    if opt_score >= 70:
        score += 3
    elif opt_score >= 50:
        score += 2
    elif opt_score >= 30:
        score += 1

    result["score"] = min(15, score)

    return result


__all__ = [
    'TopicCluster',
    'extract_keywords_from_content',
    'identify_topic_clusters',
    'find_content_gaps',
    'analyze_keyword_optimization',
    'analyze_topical_coverage'
]
