from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class CompetitiveAnalysis:
    prospect_url: str
    competitor_urls: list[str]
    analysis_date: datetime
    comparison_matrix: dict[str, Any]
    ai_visibility_gaps: list[str]
    win_probability: float
    key_differentiators: list[str]
    recommendations: list[str]

@dataclass
class ComparisonMatrix:
    prospect_score: int
    competitor_scores: dict[str, int]  # url -> score
    technical_comparison: dict[str, dict[str, int]]
    content_comparison: dict[str, dict[str, int]]
    ai_visibility_comparison: dict[str, dict[str, int]]
    grade_comparison: dict[str, str]  # url -> grade

@dataclass
class TalkingPoint:
    category: str  # "strength", "weakness", "opportunity", "threat"
    title: str
    description: str
    supporting_data: str
    confidence: float  # 0.0 to 1.0
