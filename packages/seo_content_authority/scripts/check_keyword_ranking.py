"""
Keyword Ranking Analysis

Analyzes keyword rankings using SEMrush API when available,
falls back to on-page signal estimation.
"""

import logging
import os
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def analyze_keyword_ranking(
    url: str,
    keywords: list[str],
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Analyze keyword ranking positions.

    Args:
        url: Target URL to check rankings for
        keywords: List of target keywords
        api_key: Optional SEMrush API key

    Returns:
        Dict with keyword ranking analysis (0-15 score)
    """
    api_key = api_key or os.environ.get("SEMRUSH_API_KEY")

    if api_key:
        return _analyze_with_semrush(url, keywords, api_key)
    return _estimate_keyword_score(url, keywords)


def _analyze_with_semrush(
    url: str, keywords: list[str], api_key: str
) -> dict[str, Any]:
    """Analyze rankings using SEMrush API."""
    import requests

    result = {
        "score": 0,
        "max": 15,
        "data_source": "measured",
        "rankings": [],
        "issues": [],
        "findings": [],
    }

    domain = urlparse(url).netloc
    try:
        # SEMrush Domain Overview API
        api_url = (
            f"https://api.semrush.com/"
            f"?type=domain_ranks&key={api_key}&export_columns=Dn,Rk,Or,Ot"
            f"&domain={domain}"
        )
        response = requests.get(api_url, timeout=15)

        if response.status_code == 200 and response.text.strip():
            lines = response.text.strip().split("\n")
            if len(lines) > 1:
                # Parse organic keywords count from response
                data = lines[1].split(";")
                organic_keywords = int(data[2]) if len(data) > 2 else 0

                if organic_keywords >= 500:
                    result["score"] = 15
                elif organic_keywords >= 200:
                    result["score"] = 12
                elif organic_keywords >= 50:
                    result["score"] = 9
                elif organic_keywords >= 10:
                    result["score"] = 6
                else:
                    result["score"] = 3

                result["findings"].append(
                    f"Domain ranks for {organic_keywords} organic keywords (SEMrush)"
                )
            else:
                result["score"] = 5
                result["findings"].append("Limited ranking data available in SEMrush")
        else:
            logger.warning(f"SEMrush API returned {response.status_code}")
            return _estimate_keyword_score(url, keywords)

    except Exception as e:
        logger.warning(f"SEMrush API error: {e}, falling back to estimation")
        return _estimate_keyword_score(url, keywords)

    return result


def _estimate_keyword_score(url: str, keywords: list[str]) -> dict[str, Any]:
    """
    Estimate keyword ranking score from on-page signals.
    Capped at 10/15 since real measurement would be more accurate.
    """
    result = {
        "score": 5,
        "max": 15,
        "data_source": "estimated",
        "rankings": [],
        "issues": [],
        "findings": ["Keyword ranking estimated from on-page signals (add SEMRUSH_API_KEY for measured data)"],
    }

    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "SEO-Health-Report-Bot/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.lower() if soup.title and soup.title.string else ""
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"].lower()

        h1_tags = [h.get_text().lower() for h in soup.find_all("h1")]
        body_text = soup.get_text().lower()

        signal_score = 0
        keyword_matches = 0

        for keyword in keywords[:10]:
            kw = keyword.lower().strip()
            if not kw:
                continue

            kw_signals = 0
            if kw in title:
                kw_signals += 3
            if kw in meta_desc:
                kw_signals += 2
            if any(kw in h1 for h1 in h1_tags):
                kw_signals += 2
            # Check keyword density in body
            kw_count = body_text.count(kw)
            word_count = len(body_text.split())
            if word_count > 0:
                density = (kw_count / word_count) * 100
                if 0.5 <= density <= 3.0:
                    kw_signals += 1

            if kw_signals > 0:
                keyword_matches += 1
                signal_score += min(kw_signals, 5)

        if keywords:
            match_ratio = keyword_matches / len(keywords[:10])
            avg_signal = signal_score / len(keywords[:10])

            if match_ratio >= 0.8 and avg_signal >= 3:
                result["score"] = 10  # Capped for estimated
            elif match_ratio >= 0.5 and avg_signal >= 2:
                result["score"] = 8
            elif match_ratio >= 0.3:
                result["score"] = 6
            else:
                result["score"] = 4
                result["issues"].append({
                    "severity": "medium",
                    "category": "keyword_optimization",
                    "description": "Low keyword optimization detected",
                    "recommendation": "Optimize title tags, meta descriptions, and H1 tags for target keywords",
                })

            result["findings"].append(
                f"Found on-page signals for {keyword_matches}/{len(keywords[:10])} keywords"
            )

    except Exception as e:
        logger.warning(f"Keyword estimation failed: {e}")
        result["score"] = 5
        result["findings"].append("Could not analyze on-page signals")

    return result
