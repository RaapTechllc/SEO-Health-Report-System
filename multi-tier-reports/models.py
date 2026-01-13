from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class ReportTier(Enum):
    BASIC = "basic"
    PRO = "pro" 
    ENTERPRISE = "enterprise"

@dataclass
class TierRecommendation:
    recommended_tier: ReportTier
    confidence: float  # 0.0 to 1.0
    reasoning: List[str]
    site_complexity_score: int  # 0-100
    estimated_report_time: int  # minutes
    pricing_suggestion: Dict[str, int]

@dataclass
class ReportConfig:
    tier: ReportTier
    include_sections: List[str]
    analysis_depth: str  # "basic", "standard", "comprehensive"
    branding_level: str  # "none", "basic", "custom"
    competitive_analysis: bool
    ai_visibility_focus: bool
    estimated_time: int  # minutes
    target_price: int  # dollars

@dataclass
class SiteComplexity:
    estimated_pages: int
    domain_authority: int
    technical_issues_count: int
    content_volume: str  # "low", "medium", "high"
    competitive_landscape: str  # "low", "medium", "high"
    complexity_score: int  # 0-100
