"""
Analyze Content Quality

Evaluate content quality metrics: word count, readability, media, freshness.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class ContentIssue:
    """A content quality issue found during analysis."""
    severity: str
    category: str
    description: str
    url: Optional[str] = None
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


def extract_text_content(html: str) -> str:
    """Extract text content from HTML, removing scripts and styles."""
    # Remove scripts and styles
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', clean)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def count_words(text: str) -> int:
    """Count words in text."""
    words = text.split()
    return len(words)


def calculate_readability(text: str) -> dict[str, Any]:
    """
    Calculate readability scores using Flesch-Kincaid.

    Args:
        text: Plain text content

    Returns:
        Dict with readability metrics
    """
    words = text.split()
    word_count = len(words)

    if word_count == 0:
        return {
            "flesch_reading_ease": 0,
            "flesch_kincaid_grade": 0,
            "avg_sentence_length": 0,
            "avg_syllables_per_word": 0
        }

    # Count sentences (rough approximation)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    sentence_count = max(len(sentences), 1)

    # Count syllables (rough approximation)
    def count_syllables(word: str) -> int:
        word = word.lower()
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        # Handle silent e
        if word.endswith('e') and count > 1:
            count -= 1
        return max(count, 1)

    total_syllables = sum(count_syllables(word) for word in words)

    # Calculate metrics
    avg_sentence_length = word_count / sentence_count
    avg_syllables_per_word = total_syllables / word_count

    # Flesch Reading Ease
    flesch_reading_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    flesch_reading_ease = max(0, min(100, flesch_reading_ease))

    # Flesch-Kincaid Grade Level
    flesch_kincaid_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
    flesch_kincaid_grade = max(0, flesch_kincaid_grade)

    return {
        "flesch_reading_ease": round(flesch_reading_ease, 1),
        "flesch_kincaid_grade": round(flesch_kincaid_grade, 1),
        "avg_sentence_length": round(avg_sentence_length, 1),
        "avg_syllables_per_word": round(avg_syllables_per_word, 2)
    }


def analyze_media_richness(html: str) -> dict[str, Any]:
    """
    Analyze media elements in content.

    Args:
        html: HTML content

    Returns:
        Dict with media analysis
    """
    # Count images
    images = re.findall(r'<img[^>]+>', html, re.IGNORECASE)
    images_with_alt = len([img for img in images if 'alt=' in img.lower()])

    # Count videos
    videos = len(re.findall(r'<video[^>]*>|<iframe[^>]*(?:youtube|vimeo)[^>]*>', html, re.IGNORECASE))

    # Count other rich content
    infographics = len(re.findall(r'<(?:svg|canvas)[^>]*>', html, re.IGNORECASE))
    tables = len(re.findall(r'<table[^>]*>', html, re.IGNORECASE))
    lists = len(re.findall(r'<(?:ul|ol)[^>]*>', html, re.IGNORECASE))

    return {
        "image_count": len(images),
        "images_with_alt": images_with_alt,
        "video_count": videos,
        "infographic_count": infographics,
        "table_count": tables,
        "list_count": lists,
        "has_rich_media": videos > 0 or infographics > 0 or len(images) >= 3
    }


def check_content_freshness(html: str, url: str) -> dict[str, Any]:
    """
    Check content freshness indicators.

    Args:
        html: HTML content
        url: Page URL

    Returns:
        Dict with freshness analysis
    """
    result = {
        "last_modified": None,
        "published_date": None,
        "has_date": False,
        "age_days": None,
        "freshness_status": "unknown"
    }

    # Look for dates in structured data
    date_patterns = [
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'"dateModified"\s*:\s*"([^"]+)"',
        r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)',
        r'<meta[^>]*property=["\']article:modified_time["\'][^>]*content=["\']([^"\']+)',
        r'<time[^>]*datetime=["\']([^"\']+)["\']',
    ]

    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        dates_found.extend(matches)

    if dates_found:
        result["has_date"] = True
        # Try to parse the most recent date
        for date_str in dates_found:
            try:
                # Try ISO format
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                age = (datetime.now(date.tzinfo) - date).days
                if result["age_days"] is None or age < result["age_days"]:
                    result["age_days"] = age
                    result["last_modified"] = date_str
            except ValueError:
                pass

    # Determine freshness status
    if result["age_days"] is not None:
        if result["age_days"] < 30:
            result["freshness_status"] = "fresh"
        elif result["age_days"] < 180:
            result["freshness_status"] = "recent"
        elif result["age_days"] < 365:
            result["freshness_status"] = "aging"
        else:
            result["freshness_status"] = "stale"

    return result


def is_technical_content(html: str, text: str) -> bool:
    """
    Detect if content is technical documentation.

    Args:
        html: HTML content
        text: Extracted text

    Returns:
        True if content appears to be technical/developer documentation
    """
    # Check for code blocks
    code_count = len(re.findall(r'<code[^>]*>', html, re.IGNORECASE))
    pre_count = len(re.findall(r'<pre[^>]*>', html, re.IGNORECASE))

    # Check for keywords
    tech_keywords = ['api', 'sdk', 'webhook', 'json', 'boolean', 'endpoint', 'authentication', 'curl', 'python', 'javascript', 'parameter', 'config', 'install']
    keyword_count = sum(1 for k in tech_keywords if k in text.lower())

    return code_count > 2 or pre_count > 1 or keyword_count > 5


def analyze_page_content(url: str) -> dict[str, Any]:
    """
    Comprehensive content analysis for a single page.

    Args:
        url: Page URL to analyze

    Returns:
        Dict with complete content analysis
    """
    result = {
        "url": url,
        "success": False,
        "word_count": 0,
        "readability": {},
        "media": {},
        "freshness": {},
        "issues": [],
        "findings": []
    }

    html = fetch_page(url)

    if not html:
        result["issues"].append({
            "severity": "high",
            "category": "fetch",
            "description": f"Could not fetch {url}"
        })
        return result

    result["success"] = True

    # Extract and analyze text
    text = extract_text_content(html)
    result["word_count"] = count_words(text)

    if result["word_count"] < 300:
        result["issues"].append({
            "severity": "high",
            "category": "thin_content",
            "description": f"Thin content: only {result['word_count']} words",
            "url": url,
            "recommendation": "Expand content to at least 500-1000 words"
        })
        result["findings"].append(f"Thin content ({result['word_count']} words)")
    elif result["word_count"] < 500:
        result["issues"].append({
            "severity": "medium",
            "category": "thin_content",
            "description": f"Below average content length: {result['word_count']} words",
            "url": url,
            "recommendation": "Consider expanding to 1000+ words for competitive topics"
        })
    else:
        result["findings"].append(f"Good content length ({result['word_count']} words)")

    # Readability analysis
    result["readability"] = calculate_readability(text)
    is_technical = is_technical_content(html, text)
    result["is_technical"] = is_technical

    flesch_score = result["readability"]["flesch_reading_ease"]

    if is_technical:
        # Relaxed standards for technical content
        if flesch_score < 15:
            result["issues"].append({
                "severity": "medium",
                "category": "readability",
                "description": "Technical content is very dense",
                "url": url,
                "recommendation": "Use more bullet points and examples to break up text"
            })
        elif flesch_score < 40:
            result["findings"].append(f"Acceptable complexity for technical content (Score: {flesch_score})")
        else:
            result["findings"].append("Good readability for technical content")
    else:
        # Standard scoring
        if flesch_score < 30:
            result["issues"].append({
                "severity": "medium",
                "category": "readability",
                "description": "Content is very difficult to read",
                "url": url,
                "recommendation": "Simplify language, use shorter sentences"
            })
        elif flesch_score >= 60:
            result["findings"].append("Good readability score")

    # Media analysis
    result["media"] = analyze_media_richness(html)

    if result["media"]["image_count"] == 0:
        result["issues"].append({
            "severity": "low",
            "category": "media",
            "description": "No images found in content",
            "url": url,
            "recommendation": "Add relevant images to improve engagement"
        })
    elif result["media"]["has_rich_media"]:
        result["findings"].append("Content includes rich media")

    # Freshness analysis
    result["freshness"] = check_content_freshness(html, url)

    if result["freshness"]["freshness_status"] == "stale":
        result["issues"].append({
            "severity": "medium",
            "category": "freshness",
            "description": f"Content is over 1 year old ({result['freshness']['age_days']} days)",
            "url": url,
            "recommendation": "Review and update content to maintain relevance"
        })
    elif result["freshness"]["freshness_status"] == "fresh":
        result["findings"].append("Content is recently updated")

    return result


def assess_content_quality(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Assess overall content quality across multiple pages.

    Args:
        pages: List of page analysis results

    Returns:
        Dict with overall content quality assessment (0-25 score)
    """
    result = {
        "score": 0,
        "max": 25,
        "pages_analyzed": len(pages),
        "avg_word_count": 0,
        "avg_readability": 0,
        "thin_content_pages": 0,
        "stale_pages": 0,
        "issues": [],
        "findings": []
    }

    if not pages:
        result["score"] = 0
        result["findings"].append("No pages analyzed")
        return result

    successful_pages = [p for p in pages if p.get("success")]

    if not successful_pages:
        result["score"] = 0
        result["findings"].append("Could not fetch any pages")
        return result

    # Calculate averages
    word_counts = [p["word_count"] for p in successful_pages]
    result["avg_word_count"] = sum(word_counts) / len(word_counts)

    readability_scores = [
        p["readability"]["flesch_reading_ease"]
        for p in successful_pages
        if p.get("readability")
    ]
    if readability_scores:
        result["avg_readability"] = sum(readability_scores) / len(readability_scores)

    # Count issues
    result["thin_content_pages"] = sum(
        1 for p in successful_pages if p["word_count"] < 500
    )
    result["stale_pages"] = sum(
        1 for p in successful_pages
        if p.get("freshness", {}).get("freshness_status") == "stale"
    )

    # Collect issues
    for page in successful_pages:
        result["issues"].extend(page.get("issues", []))

    # Calculate score (0-25)
    score = 25

    # Word count scoring
    if result["avg_word_count"] >= 1500:
        result["findings"].append(f"Strong content depth (avg {int(result['avg_word_count'])} words)")
    elif result["avg_word_count"] >= 800:
        score -= 3
        result["findings"].append(f"Moderate content depth (avg {int(result['avg_word_count'])} words)")
    elif result["avg_word_count"] >= 500:
        score -= 6
        result["findings"].append(f"Below average content depth (avg {int(result['avg_word_count'])} words)")
    else:
        score -= 10
        result["findings"].append(f"Thin content (avg {int(result['avg_word_count'])} words)")

    # Thin content penalty
    thin_ratio = result["thin_content_pages"] / len(successful_pages)
    if thin_ratio > 0.5:
        score -= 8
        result["findings"].append(f"Over half of pages are thin content ({result['thin_content_pages']}/{len(successful_pages)})")
    elif thin_ratio > 0.25:
        score -= 4
        result["findings"].append(f"Significant thin content ({result['thin_content_pages']} pages)")

    # Readability
    threshold = 30 if any(p.get("is_technical") for p in successful_pages) else 50

    if result["avg_readability"] >= 60:
        result["findings"].append("Good overall readability")
    elif result["avg_readability"] >= threshold:
        # Acceptable range, no penalty or small penalty
        if not any(p.get("is_technical") for p in successful_pages):
            score -= 2
        else:
            result["findings"].append("Technical content complexity detected")
    else:
        score -= 4
        result["findings"].append("Content readability needs improvement")

    # Freshness
    if result["stale_pages"] > len(successful_pages) * 0.3:
        score -= 3
        result["findings"].append(f"Many stale pages ({result['stale_pages']} need updates)")

    result["score"] = max(0, score)

    return result


__all__ = [
    'ContentIssue',
    'fetch_page',
    'extract_text_content',
    'count_words',
    'calculate_readability',
    'analyze_media_richness',
    'check_content_freshness',
    'analyze_page_content',
    'assess_content_quality'
]
