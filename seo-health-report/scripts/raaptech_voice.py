"""
RaapTech Brand Voice Integration

Applies RaapTech voice, tone, and persuasion framework to SEO report content.
"""

import os
import re
from typing import Dict, Any, List
from pathlib import Path


# Load branding prompt
BRANDING_PROMPT_PATH = Path(__file__).parent.parent.parent / ".kiro" / "prompts" / "raaptech-report-writer.md"


def load_branding_prompt() -> str:
    """Load the RaapTech report writer prompt."""
    if BRANDING_PROMPT_PATH.exists():
        return BRANDING_PROMPT_PATH.read_text()
    return ""


def apply_raaptech_voice(text: str, context: Dict[str, Any] = None) -> str:
    """
    Apply RaapTech voice transformations to text.
    
    Args:
        text: Original text
        context: Optional context (score, industry, etc.)
    
    Returns:
        Text with RaapTech voice applied
    """
    context = context or {}
    
    # Replace startup-speak with construction language
    replacements = {
        r'\bfounder(s)?\b': 'operator\\1',
        r'\bscale\b': 'grow',
        r'\bleverage\b': 'use',
        r'\bdisrupt\b': 'change',
        r'\bautomate\b': 'systematize',
        r'\boffice\b': 'shop',
        r'\buser(s)?\b': 'customer\\1',
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Remove hedging language
    hedging = [
        r'\bmight\b', r'\bcould\b', r'\bseems?\b', r'\bperhaps\b',
        r'\bpossibly\b', r'\bmaybe\b', r'\bprobably\b'
    ]
    
    for pattern in hedging:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def generate_executive_summary_raaptech(
    score: int,
    grade: str,
    critical_issues: List[Dict],
    market_position: int = None,
    competitors_count: int = None,
    revenue_impact: tuple = None,
    company_name: str = "Your company"
) -> str:
    """
    Generate executive summary with RaapTech voice.
    
    Args:
        score: Overall SEO score (0-100)
        grade: Letter grade (A-F)
        critical_issues: List of critical issues
        market_position: Position among competitors (e.g., 9)
        competitors_count: Total competitors analyzed
        revenue_impact: Tuple of (min, max) monthly revenue impact
        company_name: Company name
    
    Returns:
        Executive summary text with RaapTech voice
    """
    
    # HOOK: Pattern interrupt + specific number
    if market_position and competitors_count:
        hook = f"Your competitors are showing up in AI search results. You're not.\n\n"
    else:
        hook = f"Your SEO health score: {score}/100 (Grade: {grade}). Here's what that means for your business.\n\n"
    
    # PROBLEM: Their specific situation
    if revenue_impact:
        min_rev, max_rev = revenue_impact
        problem = (
            f"When a contractor searches for fabricators in your area, "
            f"AI systems like ChatGPT and Perplexity show your competitors. "
            f"Not you. That's ${min_rev:,}-${max_rev:,} in lost monthly revenue "
            f"from customers who never find you.\n\n"
        )
    else:
        problem = (
            f"Your website has critical SEO issues that are costing you business. "
            f"Every day these issues persist, potential customers find your competitors instead.\n\n"
        )
    
    # INSIGHT: What they don't realize
    if score < 50:
        insight = (
            f"Here's what's happening: AI systems can't parse your website. "
            f"No schema markup. No structured data. No way for AI to understand "
            f"what you do, where you are, or why you're qualified. "
            f"Result: You're invisible in 35% of searches.\n\n"
        )
    elif score < 70:
        insight = (
            f"Most fabricators think SEO is about Google rankings. But 35% of "
            f"searches now happen in AI systems. Your Google ranking doesn't "
            f"matter if AI systems don't know you exist.\n\n"
        )
    else:
        insight = (
            f"You're doing better than most. But there's still money on the table. "
            f"Small improvements in AI visibility and technical SEO translate "
            f"directly to more qualified leads.\n\n"
        )
    
    # PROOF: Their actual numbers
    proof_lines = [
        f"Your overall SEO health score: {score}/100 (Grade: {grade})"
    ]
    
    if market_position and competitors_count:
        proof_lines.append(f"Market position: #{market_position} out of {competitors_count} competitors")
    
    if critical_issues:
        proof_lines.append(f"Critical issues: {len(critical_issues)}")
    
    if revenue_impact:
        min_rev, max_rev = revenue_impact
        proof_lines.append(f"Estimated monthly impact: ${min_rev:,}-${max_rev:,}")
    
    proof = "\n".join(proof_lines) + "\n\n"
    
    # OUTCOME: What changes in 90 days
    if score < 50:
        outcome = (
            f"In 90 days, you could be the shop that shows up in AI search. "
            f"Bids come to you. Your phone rings. You're not chasing work—work finds you.\n\n"
        )
    elif score < 70:
        outcome = (
            f"In 90 days, you could be ranking above your competitors. "
            f"More qualified leads. Better conversion. Less time chasing bids.\n\n"
        )
    else:
        outcome = (
            f"In 90 days, you could be the dominant player in your market. "
            f"First choice for contractors. Premium pricing. Work comes to you.\n\n"
        )
    
    # CTA
    cta = "Here's what we found—and how to fix it."
    
    return hook + problem + insight + proof + outcome + cta


def format_recommendation_raaptech(
    priority: str,
    action: str,
    impact: str,
    effort: str,
    roi: str = None,
    mechanism: str = None
) -> str:
    """
    Format a recommendation with RaapTech voice.
    
    Args:
        priority: HIGH, MEDIUM, or LOW
        action: What to do
        impact: Business impact
        effort: Time/resource estimate
        roi: Optional ROI calculation
        mechanism: Optional explanation of why this matters
    
    Returns:
        Formatted recommendation text
    """
    lines = [
        f"**{priority.upper()} PRIORITY** {action}",
        f"Impact: {impact}",
        f"Effort: {effort}"
    ]
    
    if roi:
        lines.append(f"ROI: {roi}")
    
    if mechanism:
        lines.append(f"\nWhy this matters: {mechanism}")
    
    return "\n".join(lines)


def translate_technical_finding(
    technical_term: str,
    business_impact: str,
    specific_data: str = None
) -> str:
    """
    Translate technical SEO finding to business language.
    
    Args:
        technical_term: Technical SEO term
        business_impact: What it means for business
        specific_data: Optional specific numbers/data
    
    Returns:
        Business-friendly explanation
    """
    
    # Technical to business translations
    translations = {
        "schema markup": "structured data that helps AI understand your services",
        "page speed": "how fast your site loads",
        "mobile optimization": "how your site works on phones",
        "crawlability": "how easily search engines can read your site",
        "backlinks": "other websites linking to you",
        "meta descriptions": "the preview text in search results",
        "alt text": "image descriptions for search engines",
        "canonical tags": "signals that prevent duplicate content issues",
        "robots.txt": "instructions for search engine crawlers",
        "sitemap": "map of all your pages for search engines"
    }
    
    translated = translations.get(technical_term.lower(), technical_term)
    
    result = f"{technical_term.title()} ({translated}): {business_impact}"
    
    if specific_data:
        result += f" {specific_data}"
    
    return result


# Example usage
if __name__ == "__main__":
    # Test executive summary generation
    summary = generate_executive_summary_raaptech(
        score=29,
        grade="F",
        critical_issues=[{"description": "No schema markup"}, {"description": "Slow page speed"}],
        market_position=9,
        competitors_count=9,
        revenue_impact=(26250, 48750),
        company_name="Sheet Metal Werks"
    )
    
    print("=" * 60)
    print("RAAPTECH EXECUTIVE SUMMARY")
    print("=" * 60)
    print(summary)
    print()
    
    # Test recommendation formatting
    rec = format_recommendation_raaptech(
        priority="HIGH",
        action="Reduce page load time from 8.2s to under 3s",
        impact="40% fewer customers bouncing = 12 more qualified leads/month",
        effort="4-6 hours (compress images, enable caching, minify code)",
        roi="$18,000 annual revenue increase",
        mechanism=(
            "When your site takes 8 seconds to load, 4 out of 10 potential "
            "customers leave before seeing your services. That's 4 bids you "
            "never get to submit. Every month. Your competitors' sites load "
            "in 2-3 seconds. They're getting those bids."
        )
    )
    
    print("=" * 60)
    print("RAAPTECH RECOMMENDATION")
    print("=" * 60)
    print(rec)
