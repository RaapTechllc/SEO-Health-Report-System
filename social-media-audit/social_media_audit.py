"""
Social Media Presence Audit

Score company's social media presence using web scraping (no APIs needed).
"""

import re
from typing import Any

import requests


def check_linkedin_presence(company_name: str, domain: str) -> dict[str, Any]:
    """
    Check LinkedIn company page presence.

    Args:
        company_name: Company name
        domain: Company website domain

    Returns:
        Dict with LinkedIn presence data
    """
    # Try common LinkedIn URL patterns
    slug = company_name.lower().replace(' ', '-').replace(',', '').replace('.', '')
    possible_urls = [
        f"https://www.linkedin.com/company/{slug}",
        f"https://www.linkedin.com/company/{slug}-inc",
        f"https://www.linkedin.com/company/{slug}-llc",
    ]

    found_url = None
    for url in possible_urls:
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                found_url = url
                break
        except Exception:
            continue

    # Also check if LinkedIn link is on their website
    linkedin_on_site = False
    try:
        response = requests.get(f"https://{domain}", timeout=10)
        if 'linkedin.com/company/' in response.text:
            linkedin_on_site = True
            # Extract the actual URL
            match = re.search(r'linkedin\.com/company/([^"\'<>\s]+)', response.text)
            if match and not found_url:
                found_url = f"https://www.linkedin.com/company/{match.group(1)}"
    except Exception:
        pass

    has_page = found_url is not None or linkedin_on_site
    score = 25 if has_page else 0

    return {
        "has_page": has_page,
        "url": found_url,
        "score": score,
        "findings": [
            "LinkedIn company page found" if has_page else "No LinkedIn company page found",
            f"URL: {found_url}" if found_url else "Consider creating a LinkedIn company page"
        ]
    }


def find_social_profiles(domain: str) -> dict[str, Any]:
    """
    Find social media profiles linked from website.

    Args:
        domain: Company website domain

    Returns:
        Dict with social profiles found
    """
    profiles = {
        "linkedin": None,
        "twitter": None,
        "facebook": None,
        "instagram": None,
        "youtube": None
    }

    try:
        response = requests.get(f"https://{domain}", timeout=10)
        html = response.text

        # LinkedIn
        match = re.search(r'linkedin\.com/company/([^"\'<>\s]+)', html)
        if match:
            profiles["linkedin"] = f"https://www.linkedin.com/company/{match.group(1)}"

        # Twitter/X
        match = re.search(r'(?:twitter|x)\.com/([^"\'<>\s]+)', html)
        if match:
            profiles["twitter"] = f"https://twitter.com/{match.group(1)}"

        # Facebook
        match = re.search(r'facebook\.com/([^"\'<>\s]+)', html)
        if match:
            profiles["facebook"] = f"https://www.facebook.com/{match.group(1)}"

        # Instagram
        match = re.search(r'instagram\.com/([^"\'<>\s]+)', html)
        if match:
            profiles["instagram"] = f"https://www.instagram.com/{match.group(1)}"

        # YouTube
        match = re.search(r'youtube\.com/(?:c/|channel/|user/)?([^"\'<>\s]+)', html)
        if match:
            profiles["youtube"] = f"https://www.youtube.com/{match.group(1)}"

    except Exception as e:
        print(f"Error fetching social profiles: {e}")

    # Calculate score (20 points per platform)
    found_count = sum(1 for p in profiles.values() if p)
    score = found_count * 20

    return {
        "profiles": profiles,
        "found_count": found_count,
        "score": score,
        "findings": [
            f"Found {found_count}/5 social media profiles",
            *[f"{platform.title()}: {url}" for platform, url in profiles.items() if url]
        ]
    }


def check_social_consistency(domain: str, profiles: dict[str, str]) -> dict[str, Any]:
    """
    Check if social profiles are consistently linked and active.

    Args:
        domain: Company website
        profiles: Dict of social profiles

    Returns:
        Consistency score and findings
    """
    issues = []
    score = 100

    # Check if profiles link back to website
    for platform, url in profiles.items():
        if not url:
            continue

        try:
            response = requests.get(url, timeout=10)
            if domain not in response.text:
                issues.append(f"{platform.title()} profile doesn't link back to website")
                score -= 10
        except Exception:
            issues.append(f"Could not verify {platform.title()} profile")
            score -= 5

    # Check if all profiles use same branding
    # (This would require image analysis - placeholder for now)

    return {
        "score": max(0, score),
        "issues": issues,
        "findings": [
            "Social profiles are consistent" if score >= 80 else "Social profiles need consistency improvements",
            *issues
        ]
    }



def get_grok_sentiment(company_name: str, domain: str) -> dict[str, Any]:
    """
    Get real-time sentiment analysis from Grok (xAI).
    Grok has direct access to X/Twitter data, making it ideal for this.
    """
    import os

    from openai import OpenAI

    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        return {
            "sentiment": "Unknown",
            "score": 0,
            "summary": "Grok API key not configured.",
            "available": False
        }

    try:
        # standard OpenAI-compatible client for xAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )

        prompt = f"""Analyze the current social media sentiment for:
Company: {company_name}
Website: {domain}

Based on recent discussions and brand presence on X (Twitter), provide:
1. Overall Sentiment (Positive/Neutral/Negative)
2. A sentiment score (0-100)
3. Key discussion themes or brand perception
4. A brief 2-sentence summary

Return JSON:
{{
  "sentiment": "Positive|Neutral|Negative",
  "score": 75,
  "themes": ["theme1", "theme2"],
  "summary": "Brief summary..."
}}
"""

        completion = client.chat.completions.create(
            model=os.environ.get("XAI_MODEL", "grok-4-1-fast-reasoning"),
            messages=[
                {"role": "system", "content": "You are a social media analyst with access to real-time X/Twitter data."},
                {"role": "user", "content": prompt}
            ]
        )

        content = completion.choices[0].message.content

        # Clean up code blocks if present
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        import json
        data = json.loads(content.strip())
        return {**data, "available": True}

    except Exception as e:
        print(f"Grok estimate failed: {e}")
        return {
            "sentiment": "Error",
            "score": 0,
            "summary": f"Could not analyze sentiment: {str(e)}",
            "available": False
        }


def run_social_audit(company_name: str, domain: str) -> dict[str, Any]:
    """
    Run complete social media presence audit.

    Args:
        company_name: Company name
        domain: Company website domain

    Returns:
        Complete social audit results
    """
    # Remove protocol from domain if present
    domain = domain.replace('https://', '').replace('http://', '').split('/')[0]

    # Check LinkedIn
    linkedin_result = check_linkedin_presence(company_name, domain)

    # Find all social profiles
    profiles_result = find_social_profiles(domain)

    # Check consistency
    consistency_result = check_social_consistency(
        domain,
        profiles_result['profiles']
    )

    # Check Grok Sentiment
    sentiment_result = get_grok_sentiment(company_name, domain)

    # Calculate overall score
    # Adjusted weights to include sentiment if available
    if sentiment_result.get("available"):
        overall_score = int(
            (linkedin_result['score'] * 0.25) +
            (profiles_result['score'] * 0.45) +
            (consistency_result['score'] * 0.1) +
            (sentiment_result.get("score", 50) * 0.2)
        )
    else:
        overall_score = int(
            (linkedin_result['score'] * 0.3) +
            (profiles_result['score'] * 0.5) +
            (consistency_result['score'] * 0.2)
        )

    findings = [
        f"Overall social media score: {overall_score}/100",
        *linkedin_result['findings'],
        *profiles_result['findings'][:3],
    ]

    if sentiment_result.get("available"):
        findings.append(f"Grok Sentiment: {sentiment_result['sentiment']} ({sentiment_result['summary']})")

    return {
        "score": overall_score,
        "max": 100,
        "grade": "A" if overall_score >= 90 else
                 "B" if overall_score >= 80 else
                 "C" if overall_score >= 70 else
                 "D" if overall_score >= 60 else "F",
        "components": {
            "linkedin": linkedin_result,
            "profiles": profiles_result,
            "consistency": consistency_result,
            "sentiment": sentiment_result
        },
        "findings": findings,
        "recommendations": generate_social_recommendations(
            linkedin_result,
            profiles_result,
            consistency_result
        )
    }


def generate_social_recommendations(
    linkedin: dict,
    profiles: dict,
    consistency: dict
) -> list[dict[str, Any]]:
    """Generate prioritized social media recommendations."""
    recommendations = []

    # LinkedIn recommendations
    if not linkedin['has_page']:
        recommendations.append({
            "priority": "high",
            "category": "linkedin",
            "action": "Create LinkedIn company page",
            "details": "LinkedIn is essential for B2B credibility and SEO",
            "impact": "high",
            "effort": "low"
        })

    # Profile completeness
    missing_count = 5 - profiles['found_count']
    if missing_count > 0:
        recommendations.append({
            "priority": "medium",
            "category": "social_presence",
            "action": f"Add {missing_count} missing social profiles",
            "details": "Complete social presence improves brand credibility",
            "impact": "medium",
            "effort": "low"
        })

    # Consistency issues
    if consistency['issues']:
        recommendations.append({
            "priority": "medium",
            "category": "consistency",
            "action": "Fix social profile consistency",
            "details": "; ".join(consistency['issues'][:2]),
            "impact": "medium",
            "effort": "low"
        })

    return recommendations


# CLI interface
if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 3:
        print("Usage: python social_media_audit.py <company_name> <domain>")
        sys.exit(1)

    company_name = sys.argv[1]
    domain = sys.argv[2]

    print(f"Running social media audit for {company_name} ({domain})...")
    result = run_social_audit(company_name, domain)

    print(json.dumps(result, indent=2))
