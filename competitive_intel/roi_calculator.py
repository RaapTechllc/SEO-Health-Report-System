"""
ROI Calculator for SEO Reports

Calculates estimated revenue impact and ROI projections to strengthen
the business case in premium reports. This addresses the key gap identified
in report reviews: lack of explicit financial impact.

DISCLOSURE: All ROI projections are based on published industry benchmarks
and standard conversion rate assumptions. These are ESTIMATES intended to
illustrate potential impact, not guarantees. Actual results will vary based
on the client's specific business model, market conditions, and execution.

Data sources for industry benchmarks:
- HubSpot State of Marketing Report
- Demand Gen Report B2B Buyer Behavior Survey
- MarketingSherpa B2B Benchmark Report
- Industry-specific trade publications
"""

from dataclasses import dataclass
from typing import Any, Optional

# Import formatting utilities
try:
    from packages.core.formatting import pluralize
except ImportError:
    def pluralize(value, singular, plural=None):
        if plural is None:
            plural = singular + 's'
        return singular if value == 1 else plural


@dataclass
class ROIProjection:
    """Financial impact projection for SEO improvements."""
    # Current state
    current_visibility_score: int
    current_market_rank: int
    estimated_monthly_missed_leads: int
    estimated_monthly_lost_revenue: str  # Range like "$50,000-$150,000"

    # Projected improvements
    projected_visibility_score: int
    projected_market_rank: int
    projected_lead_increase_pct: int
    projected_monthly_revenue_gain: str

    # ROI calculation
    engagement_cost_range: str  # "$5,000-$15,000"
    estimated_roi_multiple: str  # "3-5x"
    payback_period_months: int

    # Cost of inaction
    monthly_opportunity_cost: str
    six_month_inaction_cost: str
    competitor_advantage_risk: str


# Industry benchmarks for lead value estimation
INDUSTRY_LEAD_VALUES = {
    "Manufacturing": {
        "Metal Fabrication": {"avg_deal_size": 25000, "close_rate": 0.15, "leads_per_1000_visits": 8},
        "Industrial Equipment": {"avg_deal_size": 75000, "close_rate": 0.10, "leads_per_1000_visits": 5},
        "Plastics & Composites": {"avg_deal_size": 35000, "close_rate": 0.12, "leads_per_1000_visits": 7},
        "default": {"avg_deal_size": 30000, "close_rate": 0.12, "leads_per_1000_visits": 6},
    },
    "Professional Services": {
        "Legal": {"avg_deal_size": 8000, "close_rate": 0.20, "leads_per_1000_visits": 15},
        "Accounting": {"avg_deal_size": 5000, "close_rate": 0.25, "leads_per_1000_visits": 12},
        "Consulting": {"avg_deal_size": 20000, "close_rate": 0.15, "leads_per_1000_visits": 10},
        "default": {"avg_deal_size": 10000, "close_rate": 0.20, "leads_per_1000_visits": 12},
    },
    "Healthcare": {
        "Medical Practice": {"avg_deal_size": 2000, "close_rate": 0.40, "leads_per_1000_visits": 25},
        "Dental": {"avg_deal_size": 1500, "close_rate": 0.45, "leads_per_1000_visits": 30},
        "default": {"avg_deal_size": 1800, "close_rate": 0.40, "leads_per_1000_visits": 25},
    },
    "Home Services": {
        "Construction": {"avg_deal_size": 15000, "close_rate": 0.20, "leads_per_1000_visits": 20},
        "HVAC": {"avg_deal_size": 3000, "close_rate": 0.30, "leads_per_1000_visits": 25},
        "Plumbing": {"avg_deal_size": 800, "close_rate": 0.35, "leads_per_1000_visits": 30},
        "Electrical": {"avg_deal_size": 1200, "close_rate": 0.30, "leads_per_1000_visits": 28},
        "default": {"avg_deal_size": 5000, "close_rate": 0.28, "leads_per_1000_visits": 25},
    },
    "Technology": {
        "Software Development": {"avg_deal_size": 50000, "close_rate": 0.08, "leads_per_1000_visits": 4},
        "IT Services": {"avg_deal_size": 15000, "close_rate": 0.15, "leads_per_1000_visits": 8},
        "Digital Marketing": {"avg_deal_size": 5000, "close_rate": 0.20, "leads_per_1000_visits": 12},
        "default": {"avg_deal_size": 20000, "close_rate": 0.12, "leads_per_1000_visits": 8},
    },
    "default": {"avg_deal_size": 10000, "close_rate": 0.15, "leads_per_1000_visits": 10},
}

# Visibility score to traffic/lead multipliers
VISIBILITY_IMPACT = {
    # Score range: (traffic_multiplier, lead_quality_multiplier)
    (0, 40): (0.3, 0.7),    # Very poor visibility = 30% of potential traffic
    (40, 55): (0.5, 0.8),   # Poor visibility = 50% of potential
    (55, 70): (0.7, 0.9),   # Average visibility = 70% of potential
    (70, 85): (0.9, 1.0),   # Good visibility = 90% of potential
    (85, 100): (1.0, 1.1),  # Excellent = full potential + quality bonus
}


def get_industry_benchmarks(industry: str, vertical: str) -> dict[str, Any]:
    """Get lead value benchmarks for an industry/vertical."""
    industry_data = INDUSTRY_LEAD_VALUES.get(industry, INDUSTRY_LEAD_VALUES["default"])

    if isinstance(industry_data, dict) and "avg_deal_size" not in industry_data:
        # Has sub-verticals
        return industry_data.get(vertical, industry_data.get("default", INDUSTRY_LEAD_VALUES["default"]))

    return industry_data if isinstance(industry_data, dict) else INDUSTRY_LEAD_VALUES["default"]


def get_visibility_multiplier(score: int) -> tuple:
    """Get traffic and lead quality multipliers based on visibility score."""
    for (low, high), multipliers in VISIBILITY_IMPACT.items():
        if low <= score < high:
            return multipliers
    return (1.0, 1.0)


def calculate_roi_projection(
    audit_data: dict[str, Any],
    market_intel: Optional[dict[str, Any]] = None,
    engagement_cost: int = 7500  # Default mid-range engagement
) -> ROIProjection:
    """
    Calculate ROI projection based on audit data and market intelligence.

    This creates the financial justification that was missing from reports.
    """
    # Extract scores
    overall_score = audit_data.get("overall_score", 50) or 50
    audit_data.get("audits", {}).get("ai_visibility", {}).get("score", 50) or 50

    # Get industry context
    if market_intel:
        classification = market_intel.get("classification", {})
        industry = classification.get("industry", "default")
        vertical = classification.get("vertical", "default")
        benchmark = market_intel.get("benchmark", {})
        market_rank = benchmark.get("market_position_rank", 5)
        benchmark.get("ai_visibility_rank", 5)
        benchmark.get("ai_visibility_gap_to_leader", 20)
        len(market_intel.get("competitors", [])) + 1
    else:
        industry = "default"
        vertical = "default"
        market_rank = 5

    # Get industry benchmarks
    benchmarks = get_industry_benchmarks(industry, vertical)
    avg_deal_size = benchmarks["avg_deal_size"]
    close_rate = benchmarks["close_rate"]
    leads_per_1000 = benchmarks["leads_per_1000_visits"]

    # Calculate current state impact
    current_multiplier, quality_mult = get_visibility_multiplier(overall_score)

    # Estimate monthly website visits (rough estimate based on typical B2B)
    # Companies ranking poorly typically get 500-2000 visits/month
    # Leaders get 5000-20000
    base_monthly_visits = 1500  # Conservative baseline
    current_visits = int(base_monthly_visits * current_multiplier)

    # Calculate missed leads due to poor visibility
    potential_visits = int(base_monthly_visits * 1.0)  # What they could get at 100%
    potential_visits - current_visits

    # Leads calculation
    current_leads = int(current_visits * leads_per_1000 / 1000 * quality_mult)
    potential_leads = int(potential_visits * leads_per_1000 / 1000)
    missed_leads = potential_leads - current_leads

    # Revenue calculation
    lead_value = avg_deal_size * close_rate
    monthly_lost_revenue_low = int(missed_leads * lead_value * 0.7)
    monthly_lost_revenue_high = int(missed_leads * lead_value * 1.3)

    # Project improvements (realistic 6-month targets)
    # Typically can improve 15-25 points in 6 months with focused effort
    projected_score = min(85, overall_score + 20)
    projected_multiplier, proj_quality = get_visibility_multiplier(projected_score)

    projected_visits = int(base_monthly_visits * projected_multiplier)
    projected_leads = int(projected_visits * leads_per_1000 / 1000 * proj_quality)
    lead_increase = projected_leads - current_leads
    lead_increase_pct = int((lead_increase / max(current_leads, 1)) * 100)

    monthly_revenue_gain_low = int(lead_increase * lead_value * 0.7)
    monthly_revenue_gain_high = int(lead_increase * lead_value * 1.3)

    # ROI calculation
    annual_gain_low = monthly_revenue_gain_low * 12
    annual_gain_high = monthly_revenue_gain_high * 12

    roi_low = annual_gain_low / engagement_cost if engagement_cost > 0 else 0
    roi_high = annual_gain_high / engagement_cost if engagement_cost > 0 else 0

    # Payback period
    if monthly_revenue_gain_low > 0:
        payback_months = max(1, int(engagement_cost / monthly_revenue_gain_low))
    else:
        payback_months = 12

    # Cost of inaction
    six_month_cost_low = monthly_lost_revenue_low * 6
    six_month_cost_high = monthly_lost_revenue_high * 6

    # Projected market rank improvement
    # If we close the gap, we move up roughly 1 position per 5-8 points gained
    positions_gained = min(market_rank - 1, (projected_score - overall_score) // 6)
    projected_rank = max(1, market_rank - positions_gained)

    return ROIProjection(
        current_visibility_score=overall_score,
        current_market_rank=market_rank,
        estimated_monthly_missed_leads=missed_leads,
        estimated_monthly_lost_revenue=f"${monthly_lost_revenue_low:,}-${monthly_lost_revenue_high:,}",

        projected_visibility_score=projected_score,
        projected_market_rank=projected_rank,
        projected_lead_increase_pct=lead_increase_pct,
        projected_monthly_revenue_gain=f"${monthly_revenue_gain_low:,}-${monthly_revenue_gain_high:,}",

        engagement_cost_range=f"${int(engagement_cost * 0.7):,}-${int(engagement_cost * 1.5):,}",
        estimated_roi_multiple=f"{roi_low:.1f}-{roi_high:.1f}x",
        payback_period_months=payback_months,

        monthly_opportunity_cost=f"${monthly_lost_revenue_low:,}-${monthly_lost_revenue_high:,}",
        six_month_inaction_cost=f"${six_month_cost_low:,}-${six_month_cost_high:,}",
        competitor_advantage_risk=f"Each month of delay allows competitors to capture {missed_leads} additional leads"
    )


def format_roi_for_report(projection: ROIProjection) -> dict[str, Any]:
    """Format ROI projection for inclusion in report data."""
    return {
        "disclosure": "These projections are based on published industry benchmarks and standard conversion assumptions. Actual results will vary based on your specific business model and execution.",
        "data_source": "industry_benchmarks",
        "current_state": {
            "visibility_score": projection.current_visibility_score,
            "market_rank": projection.current_market_rank,
            "monthly_missed_leads": projection.estimated_monthly_missed_leads,
            "monthly_lost_revenue": projection.estimated_monthly_lost_revenue,
        },
        "projected_improvement": {
            "visibility_score": projection.projected_visibility_score,
            "market_rank": projection.projected_market_rank,
            "lead_increase_pct": projection.projected_lead_increase_pct,
            "monthly_revenue_gain": projection.projected_monthly_revenue_gain,
        },
        "roi_analysis": {
            "engagement_cost_range": projection.engagement_cost_range,
            "estimated_roi": projection.estimated_roi_multiple,
            "payback_period_months": projection.payback_period_months,
        },
        "cost_of_inaction": {
            "monthly_opportunity_cost": projection.monthly_opportunity_cost,
            "six_month_cost": projection.six_month_inaction_cost,
            "competitor_risk": projection.competitor_advantage_risk,
        }
    }


def generate_roi_narrative(projection: ROIProjection, company_name: str) -> str:
    """Generate a narrative paragraph about ROI for the executive summary."""
    return f"""**Revenue Impact Analysis:** {company_name}'s current visibility gap is costing an estimated {projection.estimated_monthly_lost_revenue} in missed revenue each month. By improving from a score of {projection.current_visibility_score} to {projection.projected_visibility_score}, we project a {projection.projected_lead_increase_pct}% increase in qualified leads, translating to {projection.projected_monthly_revenue_gain} in additional monthly revenue.

**Cost of Inaction:** Every month of delay costs {projection.monthly_opportunity_cost} in lost opportunities. Over six months, this compounds to {projection.six_month_inaction_cost} in unrealized revenue—while competitors strengthen their position.

**Investment ROI:** A typical engagement ({projection.engagement_cost_range}) delivers an estimated {projection.estimated_roi_multiple} return within the first year, with payback typically achieved within {projection.payback_period_months} {pluralize(projection.payback_period_months, 'month')}."""


__all__ = [
    'ROIProjection',
    'calculate_roi_projection',
    'format_roi_for_report',
    'generate_roi_narrative',
    'INDUSTRY_LEAD_VALUES',
]
