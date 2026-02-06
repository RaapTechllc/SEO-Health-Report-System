"""
Generate Executive Summary

Create executive summary content for the report.
"""

from typing import Any

from .calculate_scores import get_component_status, get_grade_description


def generate_executive_summary(
    scores: dict[str, Any],
    critical_issues: list[dict[str, Any]],
    quick_wins: list[dict[str, Any]],
    company_name: str
) -> dict[str, Any]:
    """
    Generate executive summary content.

    Args:
        scores: Composite scores from calculate_composite_score()
        critical_issues: List of critical issues
        quick_wins: List of quick win opportunities
        company_name: Company name for personalization

    Returns:
        Dict with executive summary content
    """
    overall_score = scores.get("overall_score", 0)
    grade = scores.get("grade", "F")

    summary = {
        "headline": generate_headline(overall_score, grade),
        "score_display": {
            "overall": overall_score,
            "grade": grade,
            "grade_description": get_grade_description(grade)
        },
        "component_summary": [],
        "what_this_means": generate_interpretation(overall_score, grade, company_name),
        "top_actions": [],
        "key_strengths": [],
        "key_weaknesses": []
    }

    # Component summaries
    for comp_name, comp_data in scores.get("component_scores", {}).items():
        comp_score = comp_data.get("score", 0)
        status = get_component_status(comp_score)

        summary["component_summary"].append({
            "name": format_component_name(comp_name),
            "score": comp_score,
            "status": status,
            "status_icon": get_status_icon(status)
        })

        # Track strengths and weaknesses
        if comp_score >= 80:
            summary["key_strengths"].append(format_component_name(comp_name))
        elif comp_score < 50:
            summary["key_weaknesses"].append(format_component_name(comp_name))

    # Top 5 actions (mix of critical issues and quick wins)
    actions = []

    # Add critical issues first
    for issue in critical_issues[:3]:
        actions.append({
            "type": "critical",
            "action": issue.get("description", "Fix critical issue"),
            "impact": "high",
            "source": issue.get("source", "")
        })

    # Fill remaining with quick wins
    for win in quick_wins[:5 - len(actions)]:
        actions.append({
            "type": "quick_win",
            "action": win.get("action", ""),
            "impact": win.get("impact", "medium"),
            "source": win.get("source", "")
        })

    summary["top_actions"] = actions[:5]

    return summary


def generate_headline(score: int, grade: str) -> str:
    """
    Generate a headline based on the overall score.

    Args:
        score: Overall score
        grade: Letter grade

    Returns:
        Headline string
    """
    if grade == "A":
        return "Excellent SEO Health"
    elif grade == "B":
        return "Good SEO Health with Room to Grow"
    elif grade == "C":
        return "SEO Health Needs Attention"
    elif grade == "D":
        return "SEO Health Requires Improvement"
    else:
        return "SEO Health Needs Urgent Action"


def generate_interpretation(score: int, grade: str, company_name: str) -> str:
    """
    Generate a human-readable interpretation of the score.

    Args:
        score: Overall score
        grade: Letter grade
        company_name: Company name

    Returns:
        Interpretation paragraph
    """
    interpretations = {
        "A": f"{company_name}'s website demonstrates excellent SEO fundamentals across technical, content, and AI visibility dimensions. The site is well-positioned to compete in search results and AI-powered discovery. Focus on maintaining these strengths while pursuing incremental optimizations.",

        "B": f"{company_name}'s website shows solid SEO health with some areas for improvement. The foundation is strong, and addressing the identified opportunities could push performance to the next level. Prioritize the recommended actions to maximize search visibility.",

        "C": f"{company_name}'s website has notable SEO gaps that may be limiting search visibility and AI discovery. Several key areas need attention to compete effectively. The action plan below prioritizes the most impactful improvements.",

        "D": f"{company_name}'s website has significant SEO issues that are likely impacting search performance. Multiple critical areas require attention. We recommend addressing the high-priority items immediately to prevent further visibility loss.",

        "F": f"{company_name}'s website has fundamental SEO problems that require urgent attention. Critical issues are preventing the site from being properly indexed, ranked, or discovered by AI systems. Immediate action is recommended on the items below."
    }

    return interpretations.get(grade, interpretations["F"])


def format_component_name(name: str) -> str:
    """
    Format component name for display.

    Args:
        name: Raw component name

    Returns:
        Formatted name
    """
    name_map = {
        "technical": "Technical Health",
        "content": "Content & Authority",
        "ai_visibility": "AI Visibility"
    }
    return name_map.get(name, name.replace("_", " ").title())


def get_status_icon(status: str) -> str:
    """
    Get status icon/emoji for display.

    Args:
        status: Status string (good, fair, poor)

    Returns:
        Icon string
    """
    icons = {
        "good": "green",
        "fair": "yellow",
        "poor": "red"
    }
    return icons.get(status, "gray")


def generate_score_gauge_data(score: int) -> dict[str, Any]:
    """
    Generate data for score gauge visualization.

    Args:
        score: Overall score (0-100)

    Returns:
        Dict with gauge configuration
    """
    # Determine color based on score
    if score >= 80:
        color = "#34a853"  # Green
    elif score >= 60:
        color = "#fbbc04"  # Yellow
    else:
        color = "#ea4335"  # Red

    return {
        "value": score,
        "min": 0,
        "max": 100,
        "color": color,
        "segments": [
            {"start": 0, "end": 60, "color": "#ea4335"},
            {"start": 60, "end": 80, "color": "#fbbc04"},
            {"start": 80, "end": 100, "color": "#34a853"}
        ]
    }


def generate_component_chart_data(component_scores: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Generate data for component comparison chart.

    Args:
        component_scores: Component scores dict

    Returns:
        List of chart data points
    """
    chart_data = []

    for comp_name, comp_data in component_scores.items():
        score = comp_data.get("score", 0)

        chart_data.append({
            "label": format_component_name(comp_name),
            "value": score,
            "color": get_score_color(score)
        })

    return chart_data


def get_score_color(score: float) -> str:
    """
    Get color for a score value.

    Args:
        score: Score value (0-100)

    Returns:
        Hex color string
    """
    if score >= 80:
        return "#34a853"  # Green
    elif score >= 60:
        return "#fbbc04"  # Yellow
    else:
        return "#ea4335"  # Red


__all__ = [
    'generate_executive_summary',
    'generate_headline',
    'generate_interpretation',
    'format_component_name',
    'get_status_icon',
    'generate_score_gauge_data',
    'generate_component_chart_data',
    'get_score_color'
]
