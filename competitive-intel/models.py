from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class CompetitiveAnalysis:
    prospect_url: str
    competitor_urls: List[str]
    analysis_date: datetime
    comparison_matrix: Dict[str, Any]
    ai_visibility_gaps: List[str]
    win_probability: float
    key_differentiators: List[str]
    recommendations: List[str]

@dataclass
class ComparisonMatrix:
    prospect_score: int
    competitor_scores: Dict[str, int]  # url -> score
    technical_comparison: Dict[str, Dict[str, int]]
    content_comparison: Dict[str, Dict[str, int]]
    ai_visibility_comparison: Dict[str, Dict[str, int]]
    grade_comparison: Dict[str, str]  # url -> grade

@dataclass
class TalkingPoint:
    category: str  # "strength", "weakness", "opportunity", "threat"
    title: str
    description: str
    supporting_data: str
    confidence: float  # 0.0 to 1.0
