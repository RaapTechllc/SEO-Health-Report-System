"""
AI Visibility Audit

Audit brand visibility in AI systems (ChatGPT, Claude, Perplexity, Google AI).
Outputs AI Visibility Score (0-100) with optimization playbook.

This is the differentiator - most SEO agencies don't offer this.
"""

from typing import Dict, Any, List, Optional
import json

from .scripts.query_ai_systems import (
    generate_test_queries,
    query_all_systems,
    calculate_presence_score,
    TestQuery,
    AIResponse
)
from .scripts.analyze_responses import (
    analyze_brand_presence,
    check_accuracy,
    analyze_sentiment,
    analyze_competitor_comparison
)
from .scripts.check_parseability import analyze_site_structure
from .scripts.check_knowledge import check_all_sources
from .scripts.score_citability import analyze_content_citability


__version__ = "1.0.0"


def run_audit(
    brand_name: str,
    target_url: str,
    products_services: List[str],
    competitor_names: Optional[List[str]] = None,
    test_queries: Optional[List[str]] = None,
    ground_truth: Optional[Dict[str, Any]] = None,
    ai_systems: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run a complete AI visibility audit.

    Args:
        brand_name: Company/brand name
        target_url: Primary website URL
        products_services: Key offerings (5-10 recommended)
        competitor_names: Optional competitor brands to compare
        test_queries: Optional specific queries to test
        ground_truth: Optional dict of known facts for accuracy checking
        ai_systems: Which AI systems to query (default: ["claude"])

    Returns:
        Dict with complete audit results including:
        - score: Overall AI Visibility Score (0-100)
        - grade: Letter grade (A-F)
        - components: Detailed scores per component
        - ai_responses: Raw AI response data
        - accuracy_issues: List of inaccuracies found
        - recommendations: Prioritized action items
    """
    results = {
        "brand_name": brand_name,
        "target_url": target_url,
        "score": 0,
        "grade": "F",
        "components": {},
        "ai_responses": [],
        "accuracy_issues": [],
        "recommendations": []
    }

    # Default to Claude only if no systems specified
    ai_systems = ai_systems or ["claude"]

    # Step 1: Generate test queries
    queries = generate_test_queries(
        brand_name=brand_name,
        products_services=products_services,
        competitors=competitor_names,
        custom_queries=test_queries
    )

    # Step 2: Query AI systems
    responses = query_all_systems(
        queries=queries,
        brand_name=brand_name,
        systems=ai_systems
    )

    # Flatten responses for storage
    for system, system_responses in responses.items():
        for response in system_responses:
            if not response.error:
                results["ai_responses"].append({
                    "query": response.query,
                    "system": response.system,
                    "response": response.response,
                    "brand_mentioned": response.brand_mentioned,
                    "position": response.position,
                    "sentiment": response.sentiment
                })

    # Step 3: Analyze AI presence (25 points)
    presence_result = analyze_brand_presence(
        responses=responses,
        brand_name=brand_name,
        competitors=competitor_names
    )
    results["components"]["ai_presence"] = presence_result

    # Step 4: Check accuracy (20 points)
    if ground_truth:
        accuracy_result = check_accuracy(
            responses=responses,
            ground_truth=ground_truth,
            brand_name=brand_name
        )
    else:
        accuracy_result = {
            "score": 10,  # Neutral score if no ground truth
            "max": 20,
            "findings": ["No ground truth provided - accuracy partially assessed"],
            "issues": []
        }
    results["components"]["accuracy"] = accuracy_result
    results["accuracy_issues"] = accuracy_result.get("issues", [])

    # Step 5: Check LLM parseability (15 points)
    parseability_result = analyze_site_structure(target_url)
    results["components"]["parseability"] = parseability_result

    # Step 6: Check knowledge graph presence (15 points)
    knowledge_result = check_all_sources(brand_name, target_url)
    results["components"]["knowledge_graph"] = knowledge_result

    # Step 7: Score citation likelihood (15 points)
    citation_result = analyze_content_citability(target_url)
    results["components"]["citation_likelihood"] = citation_result

    # Step 8: Analyze sentiment (10 points)
    sentiment_result = analyze_sentiment(responses, brand_name)
    results["components"]["sentiment"] = sentiment_result

    # Calculate total score
    total_score = (
        presence_result["score"] +
        accuracy_result["score"] +
        parseability_result["score"] +
        knowledge_result["score"] +
        citation_result["score"] +
        sentiment_result["score"]
    )
    results["score"] = total_score

    # Assign grade
    if total_score >= 90:
        results["grade"] = "A"
    elif total_score >= 80:
        results["grade"] = "B"
    elif total_score >= 70:
        results["grade"] = "C"
    elif total_score >= 60:
        results["grade"] = "D"
    else:
        results["grade"] = "F"

    # Generate recommendations
    results["recommendations"] = generate_recommendations(results)

    return results


def generate_recommendations(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate prioritized recommendations based on audit results.

    Args:
        results: Complete audit results

    Returns:
        List of prioritized recommendations
    """
    recommendations = []

    components = results.get("components", {})

    # AI Presence recommendations
    ai_presence = components.get("ai_presence", {})
    if ai_presence.get("score", 0) < 15:
        recommendations.append({
            "priority": "high",
            "category": "ai_presence",
            "action": "Increase brand mentions in AI responses",
            "details": "Create more authoritative content that AI systems will reference. Focus on comprehensive guides and original research.",
            "impact": "high",
            "effort": "high"
        })

    # Knowledge graph recommendations
    kg = components.get("knowledge_graph", {})
    sources = kg.get("sources", {})

    if not sources.get("wikipedia", {}).get("found"):
        recommendations.append({
            "priority": "high",
            "category": "knowledge_graph",
            "action": "Work toward Wikipedia presence",
            "details": "Build notability through press coverage, awards, and industry recognition. Do not create your own Wikipedia article.",
            "impact": "high",
            "effort": "high"
        })

    if not sources.get("wikidata", {}).get("found"):
        recommendations.append({
            "priority": "medium",
            "category": "knowledge_graph",
            "action": "Create Wikidata item",
            "details": "Add your organization to Wikidata with proper structured properties.",
            "impact": "medium",
            "effort": "low"
        })

    # Parseability recommendations
    parseability = components.get("parseability", {})
    if parseability.get("score", 0) < 10:
        recommendations.append({
            "priority": "high",
            "category": "parseability",
            "action": "Improve website semantic structure",
            "details": "Add semantic HTML elements (main, article, section), proper heading hierarchy, and structured data.",
            "impact": "medium",
            "effort": "medium"
        })

    # Citation recommendations
    citation = components.get("citation_likelihood", {})
    if citation.get("score", 0) < 8:
        recommendations.append({
            "priority": "medium",
            "category": "citation_likelihood",
            "action": "Create citation-worthy content",
            "details": "Publish original research, comprehensive guides, or free tools that AI systems would reference.",
            "impact": "high",
            "effort": "high"
        })

    # Accuracy recommendations
    accuracy = components.get("accuracy", {})
    if accuracy.get("issues"):
        recommendations.append({
            "priority": "high",
            "category": "accuracy",
            "action": "Correct inaccurate AI information",
            "details": f"Found {len(accuracy['issues'])} accuracy issues. Update source information and create authoritative fact pages.",
            "impact": "high",
            "effort": "medium"
        })

    # Sentiment recommendations
    sentiment = components.get("sentiment", {})
    if sentiment.get("score", 0) < 5:
        recommendations.append({
            "priority": "medium",
            "category": "sentiment",
            "action": "Address negative sentiment",
            "details": "Investigate sources of negative sentiment and create positive content to balance perception.",
            "impact": "medium",
            "effort": "medium"
        })

    # Quick wins
    recommendations.append({
        "priority": "quick_win",
        "category": "parseability",
        "action": "Add Organization schema to homepage",
        "details": "Implement JSON-LD Organization schema with accurate company information.",
        "impact": "medium",
        "effort": "low"
    })

    recommendations.append({
        "priority": "quick_win",
        "category": "accuracy",
        "action": "Create a facts/media page",
        "details": "Publish official company facts (founding date, founders, HQ, etc.) that AI can reference.",
        "impact": "medium",
        "effort": "low"
    })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "quick_win": 2, "low": 3}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))

    return recommendations


def format_report(results: Dict[str, Any]) -> str:
    """
    Format audit results as a readable report.

    Args:
        results: Complete audit results

    Returns:
        Formatted string report
    """
    lines = []
    lines.append("=" * 60)
    lines.append("AI VISIBILITY AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"\nBrand: {results['brand_name']}")
    lines.append(f"URL: {results['target_url']}")
    lines.append(f"\nOVERALL SCORE: {results['score']}/100 (Grade: {results['grade']})")
    lines.append("\n" + "-" * 60)
    lines.append("COMPONENT SCORES")
    lines.append("-" * 60)

    components = results.get("components", {})
    for name, data in components.items():
        score = data.get("score", 0)
        max_score = data.get("max", 0)
        lines.append(f"  {name.replace('_', ' ').title()}: {score}/{max_score}")

    lines.append("\n" + "-" * 60)
    lines.append("KEY FINDINGS")
    lines.append("-" * 60)

    for name, data in components.items():
        findings = data.get("findings", [])[:3]  # Top 3 findings
        if findings:
            lines.append(f"\n{name.replace('_', ' ').title()}:")
            for finding in findings:
                lines.append(f"  • {finding}")

    lines.append("\n" + "-" * 60)
    lines.append("RECOMMENDATIONS")
    lines.append("-" * 60)

    for rec in results.get("recommendations", [])[:5]:  # Top 5 recommendations
        priority = rec.get("priority", "").upper()
        lines.append(f"\n[{priority}] {rec['action']}")
        lines.append(f"  {rec['details']}")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)


__all__ = [
    'run_audit',
    'generate_recommendations',
    'format_report',
    'generate_test_queries',
    'query_all_systems',
    'analyze_brand_presence',
    'check_accuracy',
    'analyze_sentiment',
    'analyze_site_structure',
    'check_all_sources',
    'analyze_content_citability'
]
