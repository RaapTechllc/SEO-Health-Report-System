"""
Analyze AI Responses

Analyze AI system responses for brand presence, accuracy, and sentiment.
"""

import re
from dataclasses import dataclass
from typing import Any, Optional

# Import from sibling module
from .query_ai_systems import AIResponse


@dataclass
class AccuracyIssue:
    """An accuracy issue found in AI responses."""
    claim: str
    actual: str
    source: str  # Which AI system
    query: str
    severity: str  # "critical", "high", "medium", "low"


@dataclass
class SentimentResult:
    """Sentiment analysis result for a response."""
    query: str
    system: str
    sentiment: str  # "positive", "neutral", "negative"
    confidence: float
    key_phrases: list[str]


def analyze_brand_presence(
    responses: dict[str, list[AIResponse]],
    brand_name: str,
    competitors: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Analyze brand presence across AI responses.

    Args:
        responses: Dict of system -> list of AIResponse
        brand_name: Brand name to analyze
        competitors: Optional list of competitor names

    Returns:
        Dict with presence analysis including score, findings, and details
    """
    competitors = competitors or []
    brand_name.lower()

    total_responses = 0
    brand_mentions = 0
    competitor_mentions = dict.fromkeys(competitors, 0)
    position_distribution = {"first": 0, "middle": 0, "last": 0}

    findings = []

    for _system, system_responses in responses.items():
        for response in system_responses:
            if response.error:
                continue

            total_responses += 1

            if response.brand_mentioned:
                brand_mentions += 1
                if response.position:
                    position_distribution[response.position] += 1

            # Check competitor mentions
            response_lower = response.response.lower()
            for competitor in competitors:
                if competitor.lower() in response_lower:
                    competitor_mentions[competitor] += 1

    # Generate findings
    if total_responses > 0:
        mention_rate = brand_mentions / total_responses
        findings.append(f"Brand mentioned in {brand_mentions}/{total_responses} responses ({mention_rate:.0%})")

        if position_distribution["first"] > 0:
            first_rate = position_distribution["first"] / brand_mentions if brand_mentions > 0 else 0
            findings.append(f"Mentioned first in {position_distribution['first']} responses ({first_rate:.0%} of mentions)")

        # Compare with competitors
        for competitor, count in competitor_mentions.items():
            if count > brand_mentions:
                findings.append(f"CONCERN: {competitor} mentioned more often ({count} vs {brand_mentions})")
            elif count > 0:
                findings.append(f"{competitor} mentioned {count} times")

    # Calculate score (0-25)
    if total_responses == 0:
        score = 0
    else:
        mention_rate = brand_mentions / total_responses
        if mention_rate >= 0.8:
            score = 25
        elif mention_rate >= 0.6:
            score = 20
        elif mention_rate >= 0.4:
            score = 15
        elif mention_rate >= 0.2:
            score = 10
        elif mention_rate > 0:
            score = 5
        else:
            score = 0

    return {
        "score": score,
        "max": 25,
        "findings": findings,
        "details": {
            "total_responses": total_responses,
            "brand_mentions": brand_mentions,
            "position_distribution": position_distribution,
            "competitor_mentions": competitor_mentions
        }
    }


def check_accuracy(
    responses: dict[str, list[AIResponse]],
    ground_truth: dict[str, Any],
    brand_name: str
) -> dict[str, Any]:
    """
    Check accuracy of AI responses against known facts.

    Args:
        responses: Dict of system -> list of AIResponse
        ground_truth: Dict of known facts about the brand
            Example: {
                "founded": "2012",
                "founder": "John Smith",
                "headquarters": "San Francisco",
                "products": ["Widget", "Gadget"],
                "description": "A technology company..."
            }
        brand_name: Brand name being checked

    Returns:
        Dict with accuracy analysis including score, findings, and issues
    """
    issues: list[AccuracyIssue] = []
    findings = []

    # Common patterns to check
    patterns = {
        "founded": [
            r"founded in (\d{4})",
            r"established in (\d{4})",
            r"started in (\d{4})",
            r"launched in (\d{4})"
        ],
        "founder": [
            r"founded by ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"co-founded by ([A-Z][a-z]+ [A-Z][a-z]+)"
        ],
        "headquarters": [
            r"based in ([A-Z][a-z]+(?:,? [A-Z][a-z]+)?)",
            r"headquartered in ([A-Z][a-z]+(?:,? [A-Z][a-z]+)?)"
        ]
    }

    checked_facts = 0
    accurate_facts = 0

    for system, system_responses in responses.items():
        for response in system_responses:
            if response.error or not response.brand_mentioned:
                continue

            response_text = response.response

            # Check each ground truth item
            for fact_key, fact_value in ground_truth.items():
                if fact_key in patterns:
                    for pattern in patterns[fact_key]:
                        matches = re.findall(pattern, response_text, re.IGNORECASE)
                        for match in matches:
                            checked_facts += 1
                            if str(fact_value).lower() in str(match).lower():
                                accurate_facts += 1
                            else:
                                # Determine severity
                                if fact_key in ["founded", "founder"]:
                                    severity = "high"
                                else:
                                    severity = "medium"

                                issues.append(AccuracyIssue(
                                    claim=f"{fact_key}: {match}",
                                    actual=f"{fact_key}: {fact_value}",
                                    source=system,
                                    query=response.query,
                                    severity=severity
                                ))

    # Generate findings
    if checked_facts > 0:
        accuracy_rate = accurate_facts / checked_facts
        findings.append(f"Verified {accurate_facts}/{checked_facts} facts ({accuracy_rate:.0%} accurate)")

    if issues:
        critical_count = sum(1 for i in issues if i.severity == "critical")
        high_count = sum(1 for i in issues if i.severity == "high")
        medium_count = sum(1 for i in issues if i.severity == "medium")

        if critical_count > 0:
            findings.append(f"CRITICAL: {critical_count} critical accuracy issues found")
        if high_count > 0:
            findings.append(f"WARNING: {high_count} high-severity accuracy issues")
        if medium_count > 0:
            findings.append(f"NOTE: {medium_count} medium-severity accuracy issues")

        # Add specific issues
        for issue in issues[:5]:  # Top 5 issues
            findings.append(f"  - {issue.source}: Claims '{issue.claim}', actual is '{issue.actual}'")
    else:
        findings.append("No accuracy issues detected in verifiable claims")

    # Calculate score (0-20)
    if checked_facts == 0:
        score = 10  # Neutral score if can't verify
        findings.append("Could not verify any specific facts - consider adding ground truth data")
    else:
        accuracy_rate = accurate_facts / checked_facts

        # Deduct points for issues by severity
        score = 20
        for issue in issues:
            if issue.severity == "critical":
                score -= 5
            elif issue.severity == "high":
                score -= 3
            elif issue.severity == "medium":
                score -= 1

        score = max(0, score)

    return {
        "score": score,
        "max": 20,
        "findings": findings,
        "issues": [
            {
                "claim": i.claim,
                "actual": i.actual,
                "source": i.source,
                "query": i.query,
                "severity": i.severity
            }
            for i in issues
        ],
        "details": {
            "checked_facts": checked_facts,
            "accurate_facts": accurate_facts,
            "accuracy_rate": accurate_facts / checked_facts if checked_facts > 0 else None
        }
    }


def analyze_sentiment(
    responses: dict[str, list[AIResponse]],
    brand_name: str
) -> dict[str, Any]:
    """
    Analyze sentiment of AI responses about the brand.

    Uses keyword-based sentiment analysis. For production, consider
    integrating a proper NLP model.

    Args:
        responses: Dict of system -> list of AIResponse
        brand_name: Brand name being analyzed

    Returns:
        Dict with sentiment analysis including score, findings, and details
    """
    # Sentiment keywords (basic approach - can be enhanced with NLP)
    positive_keywords = [
        "excellent", "great", "best", "leading", "innovative", "trusted",
        "reliable", "quality", "recommended", "popular", "successful",
        "top", "premier", "outstanding", "exceptional", "impressive",
        "well-known", "respected", "reputable", "highly rated"
    ]

    negative_keywords = [
        "poor", "bad", "worst", "complaints", "issues", "problems",
        "concerns", "criticized", "controversial", "failed", "struggling",
        "unreliable", "expensive", "overpriced", "disappointing",
        "lawsuit", "scandal", "avoid"
    ]


    results: list[SentimentResult] = []
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    findings = []

    for system, system_responses in responses.items():
        for response in system_responses:
            if response.error or not response.brand_mentioned:
                continue

            response_lower = response.response.lower()

            # Count keyword occurrences
            positive_count = sum(1 for kw in positive_keywords if kw in response_lower)
            negative_count = sum(1 for kw in negative_keywords if kw in response_lower)

            # Determine sentiment (adjusted thresholds for typical AI responses)
            if positive_count > 0 and negative_count == 0:
                sentiment = "positive"
                confidence = min(1.0, positive_count / 3)
            elif negative_count > 0 and positive_count == 0:
                sentiment = "negative"
                confidence = min(1.0, negative_count / 3)
            elif positive_count > negative_count:
                sentiment = "positive"
                confidence = min(1.0, (positive_count - negative_count) / 3)
            elif negative_count > positive_count:
                sentiment = "negative"
                confidence = min(1.0, (negative_count - positive_count) / 3)
            else:
                sentiment = "neutral"
                confidence = 0.5

            sentiment_counts[sentiment] += 1

            # Extract key phrases
            key_phrases = []
            for kw in positive_keywords + negative_keywords:
                if kw in response_lower:
                    key_phrases.append(kw)

            results.append(SentimentResult(
                query=response.query,
                system=system,
                sentiment=sentiment,
                confidence=confidence,
                key_phrases=key_phrases[:5]
            ))

    # Generate findings
    total = sum(sentiment_counts.values())
    if total > 0:
        for sentiment, count in sentiment_counts.items():
            rate = count / total
            findings.append(f"{sentiment.capitalize()}: {count}/{total} responses ({rate:.0%})")

        # Flag concerns
        if sentiment_counts["negative"] > sentiment_counts["positive"]:
            findings.append("CONCERN: More negative than positive sentiment detected")

        if sentiment_counts["negative"] > total * 0.3:
            findings.append("WARNING: Significant negative sentiment (>30%)")

    # Calculate score (0-10)
    if total == 0:
        score = 5  # Neutral if no data
    else:
        positive_rate = sentiment_counts["positive"] / total
        negative_rate = sentiment_counts["negative"] / total

        if negative_rate > 0.5:
            score = 0
        elif negative_rate > 0.3:
            score = 3
        elif positive_rate > 0.7:
            score = 10
        elif positive_rate > 0.5:
            score = 7
        else:
            score = 5

    return {
        "score": score,
        "max": 10,
        "findings": findings,
        "details": {
            "sentiment_counts": sentiment_counts,
            "total_analyzed": total,
            "results": [
                {
                    "query": r.query,
                    "system": r.system,
                    "sentiment": r.sentiment,
                    "confidence": r.confidence,
                    "key_phrases": r.key_phrases
                }
                for r in results
            ]
        }
    }


def analyze_competitor_comparison(
    responses: dict[str, list[AIResponse]],
    brand_name: str,
    competitors: list[str]
) -> dict[str, Any]:
    """
    Analyze how the brand compares to competitors in AI responses.

    Args:
        responses: Dict of system -> list of AIResponse
        brand_name: Brand name being analyzed
        competitors: List of competitor names

    Returns:
        Dict with competitive analysis
    """
    brand_lower = brand_name.lower()
    mention_counts = {brand_name: 0}
    for c in competitors:
        mention_counts[c] = 0

    first_mentions = {brand_name: 0}
    for c in competitors:
        first_mentions[c] = 0

    total_responses = 0

    for _system, system_responses in responses.items():
        for response in system_responses:
            if response.error:
                continue

            total_responses += 1
            response_lower = response.response.lower()

            # Count mentions
            if brand_lower in response_lower:
                mention_counts[brand_name] += 1

            for competitor in competitors:
                if competitor.lower() in response_lower:
                    mention_counts[competitor] += 1

            # Track who's mentioned first
            first_pos = {brand_name: response_lower.find(brand_lower)}
            for competitor in competitors:
                first_pos[competitor] = response_lower.find(competitor.lower())

            # Find who's mentioned first (excluding -1 which means not found)
            valid_positions = {k: v for k, v in first_pos.items() if v >= 0}
            if valid_positions:
                first_mentioned = min(valid_positions, key=valid_positions.get)
                first_mentions[first_mentioned] += 1

    findings = []

    # Rank by mentions
    sorted_mentions = sorted(mention_counts.items(), key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (name, _) in enumerate(sorted_mentions) if name == brand_name), len(sorted_mentions))

    findings.append(f"Brand ranks #{rank} in mention frequency among competitors")

    for name, count in sorted_mentions:
        marker = " (your brand)" if name == brand_name else ""
        findings.append(f"  {name}: {count} mentions{marker}")

    # First mention analysis
    if first_mentions[brand_name] > 0:
        first_rate = first_mentions[brand_name] / total_responses if total_responses > 0 else 0
        findings.append(f"Brand mentioned first in {first_mentions[brand_name]} responses ({first_rate:.0%})")

    return {
        "findings": findings,
        "details": {
            "mention_counts": mention_counts,
            "first_mentions": first_mentions,
            "brand_rank": rank,
            "total_responses": total_responses
        }
    }


__all__ = [
    'AccuracyIssue',
    'SentimentResult',
    'analyze_brand_presence',
    'check_accuracy',
    'analyze_sentiment',
    'analyze_competitor_comparison'
]
