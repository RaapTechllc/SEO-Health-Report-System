"""
SEO ROI Calculator - High Priority Business Impact Module

Converts technical SEO findings into dollar projections and ROI prioritization.
Designed for C-suite presentations and business justification.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import math

@dataclass
class ROIProjection:
    """ROI projection for a specific SEO recommendation."""
    recommendation: str
    traffic_lift_percent: float
    current_monthly_traffic: int
    revenue_per_visitor: float
    implementation_cost: int
    implementation_days: int
    confidence_score: float  # 0.0-1.0
    
    @property
    def monthly_traffic_increase(self) -> int:
        return int(self.current_monthly_traffic * (self.traffic_lift_percent / 100))
    
    @property
    def monthly_revenue_increase(self) -> float:
        return self.monthly_traffic_increase * self.revenue_per_visitor
    
    @property
    def annual_revenue_increase(self) -> float:
        return self.monthly_revenue_increase * 12
    
    @property
    def roi_percentage(self) -> float:
        if self.implementation_cost == 0:
            return float('inf')
        return ((self.annual_revenue_increase - self.implementation_cost) / self.implementation_cost) * 100
    
    @property
    def payback_months(self) -> float:
        if self.monthly_revenue_increase == 0:
            return float('inf')
        return self.implementation_cost / self.monthly_revenue_increase
    
    @property
    def priority_score(self) -> float:
        """Weighted priority score: ROI × confidence ÷ implementation time"""
        if self.implementation_days == 0:
            time_factor = 1
        else:
            time_factor = 30 / self.implementation_days  # Favor faster implementation
        
        roi_factor = min(self.roi_percentage / 100, 10)  # Cap at 1000% ROI for scoring
        return roi_factor * self.confidence_score * time_factor


def calculate_seo_roi(
    audit_results: Dict[str, Any],
    business_metrics: Dict[str, Any]
) -> List[ROIProjection]:
    """
    Calculate ROI projections for SEO audit recommendations.
    
    Args:
        audit_results: Technical, content, and AI audit results
        business_metrics: Current traffic, conversion rate, AOV, etc.
        
    Returns:
        List of ROI projections sorted by priority score
    """
    
    # Extract business metrics
    monthly_traffic = business_metrics.get('monthly_organic_traffic', 10000)
    conversion_rate = business_metrics.get('conversion_rate', 0.02)
    avg_order_value = business_metrics.get('avg_order_value', 100)
    revenue_per_visitor = conversion_rate * avg_order_value
    
    projections = []
    
    # Technical SEO ROI projections
    technical = audit_results.get('audits', {}).get('technical', {})
    if technical.get('score', 0) < 80:
        projections.extend(_calculate_technical_roi(technical, monthly_traffic, revenue_per_visitor))
    
    # Content ROI projections  
    content = audit_results.get('audits', {}).get('content', {})
    if content.get('score', 0) < 80:
        projections.extend(_calculate_content_roi(content, monthly_traffic, revenue_per_visitor))
    
    # AI Visibility ROI projections
    ai = audit_results.get('audits', {}).get('ai_visibility', {})
    if ai.get('score', 0) < 80:
        projections.extend(_calculate_ai_roi(ai, monthly_traffic, revenue_per_visitor))
    
    # Sort by priority score (highest first)
    projections.sort(key=lambda x: x.priority_score, reverse=True)
    
    return projections


def _calculate_technical_roi(technical: Dict, monthly_traffic: int, revenue_per_visitor: float) -> List[ROIProjection]:
    """Calculate ROI for technical SEO fixes."""
    projections = []
    
    # Core Web Vitals improvement
    speed_score = technical.get('components', {}).get('speed', {}).get('score', 100)
    if speed_score < 20:
        projections.append(ROIProjection(
            recommendation="Fix Core Web Vitals (LCP, FID, CLS)",
            traffic_lift_percent=15.0,  # Poor CWV can lose 15% traffic
            current_monthly_traffic=monthly_traffic,
            revenue_per_visitor=revenue_per_visitor,
            implementation_cost=5000,  # Developer time
            implementation_days=14,
            confidence_score=0.85
        ))
    
    # Mobile optimization
    mobile_score = technical.get('components', {}).get('mobile', {}).get('score', 100)
    if mobile_score < 12:
        projections.append(ROIProjection(
            recommendation="Mobile optimization and responsive design fixes",
            traffic_lift_percent=12.0,  # Mobile-first indexing impact
            current_monthly_traffic=monthly_traffic,
            revenue_per_visitor=revenue_per_visitor,
            implementation_cost=3000,
            implementation_days=10,
            confidence_score=0.80
        ))
    
    # Crawlability issues
    crawl_score = technical.get('components', {}).get('crawlability', {}).get('score', 100)
    if crawl_score < 15:
        projections.append(ROIProjection(
            recommendation="Fix crawlability issues (robots.txt, sitemaps, internal links)",
            traffic_lift_percent=8.0,
            current_monthly_traffic=monthly_traffic,
            revenue_per_visitor=revenue_per_visitor,
            implementation_cost=2000,
            implementation_days=7,
            confidence_score=0.90
        ))
    
    return projections


def _calculate_content_roi(content: Dict, monthly_traffic: int, revenue_per_visitor: float) -> List[ROIProjection]:
    """Calculate ROI for content improvements."""
    projections = []
    
    # Content quality improvement
    content_score = content.get('components', {}).get('content_quality', {}).get('score', 100)
    if content_score < 20:
        projections.append(ROIProjection(
            recommendation="Improve content quality and depth (thin content, keyword optimization)",
            traffic_lift_percent=20.0,  # Quality content drives significant traffic
            current_monthly_traffic=monthly_traffic,
            revenue_per_visitor=revenue_per_visitor,
            implementation_cost=4000,  # Content writer + SEO specialist
            implementation_days=21,
            confidence_score=0.75
        ))
    
    # E-E-A-T signals
    eeat_score = content.get('components', {}).get('eeat', {}).get('score', 100)
    if eeat_score < 15:
        projections.append(ROIProjection(
            recommendation="Build E-E-A-T signals (author pages, credentials, trust signals)",
            traffic_lift_percent=10.0,
            current_monthly_traffic=monthly_traffic,
            revenue_per_visitor=revenue_per_visitor,
            implementation_cost=2500,
            implementation_days=14,
            confidence_score=0.70
        ))
    
    return projections


def _calculate_ai_roi(ai: Dict, monthly_traffic: int, revenue_per_visitor: float) -> List[ROIProjection]:
    """Calculate ROI for AI visibility improvements."""
    projections = []
    
    # AI presence optimization
    ai_score = ai.get('components', {}).get('ai_presence', {}).get('score', 100)
    if ai_score < 20:
        projections.append(ROIProjection(
            recommendation="Optimize content for AI search engines (ChatGPT, Perplexity, Claude)",
            traffic_lift_percent=25.0,  # AI search is growing rapidly
            current_monthly_traffic=monthly_traffic,
            revenue_per_visitor=revenue_per_visitor,
            implementation_cost=3500,
            implementation_days=18,
            confidence_score=0.65  # Newer channel, less certainty
        ))
    
    # Parseability for AI systems
    parse_score = ai.get('components', {}).get('parseability', {}).get('score', 100)
    if parse_score < 12:
        projections.append(ROIProjection(
            recommendation="Improve content structure for AI crawlers (clean HTML, semantic markup)",
            traffic_lift_percent=8.0,
            current_monthly_traffic=monthly_traffic,
            revenue_per_visitor=revenue_per_visitor,
            implementation_cost=2000,
            implementation_days=10,
            confidence_score=0.80
        ))
    
    return projections


def generate_roi_summary(projections: List[ROIProjection]) -> Dict[str, Any]:
    """Generate executive summary of ROI projections."""
    
    if not projections:
        return {
            "total_investment": 0,
            "total_annual_revenue": 0,
            "overall_roi": 0,
            "payback_months": 0,
            "top_opportunities": []
        }
    
    total_investment = sum(p.implementation_cost for p in projections)
    total_annual_revenue = sum(p.annual_revenue_increase for p in projections)
    overall_roi = ((total_annual_revenue - total_investment) / total_investment * 100) if total_investment > 0 else 0
    
    # Weighted average payback period
    total_monthly_revenue = sum(p.monthly_revenue_increase for p in projections)
    avg_payback_months = total_investment / total_monthly_revenue if total_monthly_revenue > 0 else 0
    
    return {
        "total_investment": total_investment,
        "total_annual_revenue": int(total_annual_revenue),
        "overall_roi": round(overall_roi, 1),
        "payback_months": round(avg_payback_months, 1),
        "top_opportunities": [
            {
                "recommendation": p.recommendation,
                "monthly_revenue": int(p.monthly_revenue_increase),
                "annual_revenue": int(p.annual_revenue_increase),
                "investment": p.implementation_cost,
                "roi": round(p.roi_percentage, 1),
                "payback_months": round(p.payback_months, 1),
                "priority_score": round(p.priority_score, 2)
            }
            for p in projections[:5]  # Top 5 opportunities
        ]
    }
