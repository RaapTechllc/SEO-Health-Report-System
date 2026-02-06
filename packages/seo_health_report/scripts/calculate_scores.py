"""
Calculate Composite Scores

Calculate weighted composite scores from individual audits.
"""

import os
import sys
from typing import Any

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config

# Get configuration
_config = get_config()

# Default weights from config
WEIGHTS = {
    "technical": _config.score_weight_technical,
    "content": _config.score_weight_content,
    "ai_visibility": _config.score_weight_ai,
}


def calculate_composite_score(
    audit_results: dict[str, Any], weights: dict[str, float] = None
) -> dict[str, Any]:
    """
    Calculate weighted composite score from audit results.

    Args:
        audit_results: Results from run_full_audit()
        weights: Optional custom weights (must sum to 1.0)

    Returns:
        Dict with composite score details
    """
    weights = weights or WEIGHTS

    result = {
        "overall_score": 0,
        "grade": "F",
        "component_scores": {},
        "weights_used": weights,
    }

    audits = audit_results.get("audits", {})

    # Map audit keys to weight keys
    audit_to_weight = {
        "technical": "technical",
        "content": "content",
        "ai_visibility": "ai_visibility",
    }

    total_weighted = 0
    total_weight = 0

    for audit_key, weight_key in audit_to_weight.items():
        audit_data = audits.get(audit_key, {})
        weight = weights.get(weight_key, 0)

        if audit_data:
            score = audit_data.get("score")

            # Skip audits with None score (failed audits)
            if score is None:
                continue

            max_score = audit_data.get("max", 100)

            # Normalize to 100-point scale if needed
            if max_score != 100 and max_score > 0:
                normalized_score = (score / max_score) * 100
            else:
                normalized_score = score

            weighted_score = normalized_score * weight

            result["component_scores"][audit_key] = {
                "score": round(normalized_score, 1),
                "max": 100,
                "weight": weight,
                "weighted_score": round(weighted_score, 1),
            }

            total_weighted += weighted_score
            total_weight += weight

    # Calculate overall
    if total_weight > 0:
        result["overall_score"] = round(total_weighted / total_weight, 0)
    else:
        result["overall_score"] = 0

    # Ensure it's an integer
    result["overall_score"] = int(result["overall_score"])

    # Determine grade
    result["grade"] = determine_grade(result["overall_score"])

    return result


def determine_grade(score: int) -> str:
    """
    Determine letter grade from numerical score.

    Args:
        score: Numerical score (0-100)

    Returns:
        Letter grade (A, B, C, D, F)
    """
    config = get_config()

    if score >= config.grade_a_threshold:
        return "A"
    elif score >= config.grade_b_threshold:
        return "B"
    elif score >= config.grade_c_threshold:
        return "C"
    elif score >= config.grade_d_threshold:
        return "D"
    else:
        return "F"


def get_grade_description(grade: str) -> str:
    """
    Get description for a letter grade.

    Args:
        grade: Letter grade

    Returns:
        Description string
    """
    descriptions = {
        "A": "Excellent - Your site has strong SEO health across all areas.",
        "B": "Good - Your site is performing well with some room for improvement.",
        "C": "Needs Work - There are significant gaps that should be addressed.",
        "D": "Poor - Major issues are impacting your SEO performance.",
        "F": "Critical - Urgent attention required to fix fundamental issues.",
    }
    return descriptions.get(grade, "Unknown grade")


def get_component_status(score: float, max_score: float = 100) -> str:
    """
    Get status indicator for a component score.

    Args:
        score: Component score
        max_score: Maximum possible score

    Returns:
        Status string (good, fair, poor)
    """
    ratio = score / max_score if max_score > 0 else 0

    if ratio >= 0.8:
        return "good"
    elif ratio >= 0.5:
        return "fair"
    else:
        return "poor"


def compare_scores(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    """
    Compare current scores with previous audit.

    Args:
        current: Current audit scores
        previous: Previous audit scores

    Returns:
        Dict with comparison data
    """
    comparison = {
        "overall_change": 0,
        "component_changes": {},
        "improved": [],
        "declined": [],
        "unchanged": [],
    }

    # Overall change
    current_score = current.get("overall_score", 0)
    previous_score = previous.get("overall_score", 0)
    comparison["overall_change"] = current_score - previous_score

    # Component changes
    current_components = current.get("component_scores", {})
    previous_components = previous.get("component_scores", {})

    for comp_name in set(current_components.keys()) | set(previous_components.keys()):
        curr = current_components.get(comp_name, {}).get("score", 0)
        prev = previous_components.get(comp_name, {}).get("score", 0)
        change = curr - prev

        comparison["component_changes"][comp_name] = {
            "previous": prev,
            "current": curr,
            "change": change,
        }

        if change > 0:
            comparison["improved"].append(comp_name)
        elif change < 0:
            comparison["declined"].append(comp_name)
        else:
            comparison["unchanged"].append(comp_name)

    return comparison


def calculate_benchmark_comparison(
    scores: dict[str, Any], benchmarks: dict[str, float] = None
) -> dict[str, Any]:
    """
    Compare scores against industry benchmarks.

    Args:
        scores: Calculated scores
        benchmarks: Optional custom benchmarks

    Returns:
        Dict with benchmark comparison
    """
    # Default benchmarks (can be customized)
    default_benchmarks = {
        "technical": 75,
        "content": 70,
        "ai_visibility": 50,  # Lower because it's new
        "overall": 70,
    }

    benchmarks = benchmarks or default_benchmarks

    comparison = {
        "overall": {
            "score": scores.get("overall_score", 0),
            "benchmark": benchmarks.get("overall", 70),
            "vs_benchmark": scores.get("overall_score", 0)
            - benchmarks.get("overall", 70),
        },
        "components": {},
    }

    for comp_name, comp_data in scores.get("component_scores", {}).items():
        comp_score = comp_data.get("score", 0)
        comp_benchmark = benchmarks.get(comp_name, 70)

        comparison["components"][comp_name] = {
            "score": comp_score,
            "benchmark": comp_benchmark,
            "vs_benchmark": comp_score - comp_benchmark,
            "status": "above" if comp_score >= comp_benchmark else "below",
        }

    return comparison


__all__ = [
    "WEIGHTS",
    "calculate_composite_score",
    "determine_grade",
    "get_grade_description",
    "get_component_status",
    "compare_scores",
    "calculate_benchmark_comparison",
]
