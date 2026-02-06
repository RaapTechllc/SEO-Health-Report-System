import logging
from typing import Any, Optional

from models import ReportTier, TierRecommendation

# Import formatting utilities
try:
    from packages.core.formatting import pluralize
except ImportError:
    def pluralize(value, singular, plural=None):
        if plural is None:
            plural = singular + 's'
        return singular if value == 1 else plural


class PricingOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Market pricing intelligence
        self.market_data = {
            "competitor_pricing": {
                "basic_seo_audit": {"min": 500, "max": 2000, "avg": 1200},
                "comprehensive_audit": {"min": 2000, "max": 8000, "avg": 4500},
                "enterprise_audit": {"min": 5000, "max": 15000, "avg": 9000}
            },
            "value_multipliers": {
                "ai_visibility": 1.3,  # 30% premium for AI focus
                "competitive_analysis": 1.2,  # 20% premium for competitive intel
                "custom_branding": 1.15,  # 15% premium for branding
                "ongoing_monitoring": 1.25  # 25% premium for monitoring
            }
        }

    def optimize_pricing(self, tier_recommendation: TierRecommendation,
                        market_context: dict[str, Any] = None) -> dict[str, Any]:
        """Optimize pricing based on tier, complexity, and market context."""

        try:
            tier = tier_recommendation.recommended_tier
            complexity = tier_recommendation.site_complexity_score

            # Get base pricing
            base_pricing = self._get_base_pricing(tier, complexity)

            # Apply market adjustments
            market_adjusted = self._apply_market_adjustments(base_pricing, market_context)

            # Calculate value proposition
            value_prop = self._calculate_value_proposition(tier, complexity, market_adjusted)

            # Generate pricing strategy
            strategy = self._generate_pricing_strategy(tier, market_adjusted, value_prop)

            return {
                "recommended_pricing": market_adjusted,
                "value_proposition": value_prop,
                "pricing_strategy": strategy,
                "competitive_positioning": self._get_competitive_positioning(tier, market_adjusted),
                "upsell_opportunities": self._identify_upsell_opportunities(tier, complexity)
            }

        except Exception as e:
            self.logger.error(f"Pricing optimization failed: {e}")
            return self._get_default_pricing(tier_recommendation.recommended_tier)

    def _get_base_pricing(self, tier: ReportTier, complexity: int) -> dict[str, int]:
        """Get base pricing for tier adjusted by complexity."""

        base_prices = {
            ReportTier.BASIC: {"base": 800, "min": 500, "max": 1500},
            ReportTier.PRO: {"base": 2500, "min": 1500, "max": 4000},
            ReportTier.ENTERPRISE: {"base": 6000, "min": 4000, "max": 10000}
        }

        tier_pricing = base_prices[tier]

        # Adjust for complexity
        complexity_factor = 0.8 + (complexity / 100) * 0.4  # 0.8 to 1.2 multiplier

        adjusted_base = int(tier_pricing["base"] * complexity_factor)
        adjusted_min = max(tier_pricing["min"], int(adjusted_base * 0.8))
        adjusted_max = min(tier_pricing["max"], int(adjusted_base * 1.3))

        return {
            "recommended": adjusted_base,
            "min": adjusted_min,
            "max": adjusted_max
        }

    def _apply_market_adjustments(self, base_pricing: dict[str, int],
                                 market_context: Optional[dict[str, Any]]) -> dict[str, int]:
        """Apply market-based pricing adjustments."""

        if not market_context:
            return base_pricing

        multiplier = 1.0

        # Geographic adjustments
        if market_context.get("region") == "high_cost":
            multiplier *= 1.2
        elif market_context.get("region") == "low_cost":
            multiplier *= 0.9

        # Industry adjustments
        industry = market_context.get("industry", "")
        if industry in ["finance", "healthcare", "legal"]:
            multiplier *= 1.3  # Premium industries
        elif industry in ["nonprofit", "education"]:
            multiplier *= 0.8  # Discount for nonprofits

        # Urgency adjustments
        if market_context.get("urgency") == "high":
            multiplier *= 1.2
        elif market_context.get("urgency") == "low":
            multiplier *= 0.9

        # Apply adjustments
        return {
            "recommended": int(base_pricing["recommended"] * multiplier),
            "min": int(base_pricing["min"] * multiplier),
            "max": int(base_pricing["max"] * multiplier)
        }

    def _calculate_value_proposition(self, tier: ReportTier, complexity: int,
                                   pricing: dict[str, int]) -> dict[str, Any]:
        """Calculate value proposition for the pricing."""

        # Estimate potential traffic/revenue impact
        if tier == ReportTier.BASIC:
            traffic_improvement = 0.15  # 15%
            implementation_time = 30  # days
        elif tier == ReportTier.PRO:
            traffic_improvement = 0.35  # 35% (includes AI visibility)
            implementation_time = 60  # days
        else:  # Enterprise
            traffic_improvement = 0.50  # 50%
            implementation_time = 90  # days

        # Calculate ROI (assuming baseline metrics)
        monthly_visitors = 10000  # Assumed baseline
        conversion_rate = 0.02
        avg_order_value = 100

        current_monthly_revenue = monthly_visitors * conversion_rate * avg_order_value
        improved_monthly_revenue = current_monthly_revenue * (1 + traffic_improvement)
        monthly_revenue_increase = improved_monthly_revenue - current_monthly_revenue

        annual_revenue_increase = monthly_revenue_increase * 12
        roi_multiple = annual_revenue_increase / pricing["recommended"]

        return {
            "traffic_improvement_percent": traffic_improvement * 100,
            "estimated_monthly_revenue_increase": monthly_revenue_increase,
            "estimated_annual_revenue_increase": annual_revenue_increase,
            "roi_multiple": roi_multiple,
            "payback_period_months": pricing["recommended"] / monthly_revenue_increase if monthly_revenue_increase > 0 else 12,
            "implementation_timeline_days": implementation_time
        }

    def _generate_pricing_strategy(self, tier: ReportTier, pricing: dict[str, int],
                                  value_prop: dict[str, Any]) -> dict[str, Any]:
        """Generate pricing strategy and messaging."""

        strategy = {
            "anchor_price": pricing["max"],  # Start high
            "recommended_price": pricing["recommended"],
            "minimum_acceptable": pricing["min"],
            "negotiation_room": pricing["recommended"] - pricing["min"]
        }

        # Pricing justification
        if value_prop["roi_multiple"] > 5:
            strategy["justification"] = f"Delivers {value_prop['roi_multiple']:.1f}x ROI - exceptional value"
        elif value_prop["roi_multiple"] > 3:
            payback_months = int(value_prop['payback_period_months'])
            strategy["justification"] = f"Strong {value_prop['roi_multiple']:.1f}x ROI with {payback_months} {pluralize(payback_months, 'month')} payback"
        else:
            strategy["justification"] = "Comprehensive analysis with measurable business impact"

        # Pricing tactics
        strategy["tactics"] = []

        if tier == ReportTier.BASIC:
            strategy["tactics"].extend([
                "Position as 'essential SEO foundation'",
                "Emphasize quick wins and immediate fixes",
                "Compare to cost of hiring SEO consultant ($150/hour)"
            ])
        elif tier == ReportTier.PRO:
            strategy["tactics"].extend([
                "Lead with AI visibility differentiator",
                "Emphasize competitive advantage",
                "Compare to traditional agency retainer ($3K-5K/month)"
            ])
        else:  # Enterprise
            strategy["tactics"].extend([
                "Focus on executive-level insights",
                "Emphasize custom branding and presentation",
                "Compare to enterprise consulting ($10K-20K projects)"
            ])

        return strategy

    def _get_competitive_positioning(self, tier: ReportTier, pricing: dict[str, int]) -> dict[str, Any]:
        """Get competitive positioning for the pricing."""

        market_avg = self.market_data["competitor_pricing"]

        if tier == ReportTier.BASIC:
            competitor_avg = market_avg["basic_seo_audit"]["avg"]
            positioning = "Premium value"
        elif tier == ReportTier.PRO:
            competitor_avg = market_avg["comprehensive_audit"]["avg"]
            positioning = "Competitive with AI advantage"
        else:
            competitor_avg = market_avg["enterprise_audit"]["avg"]
            positioning = "Premium positioning"

        price_vs_market = (pricing["recommended"] / competitor_avg - 1) * 100

        return {
            "vs_market_average": f"{price_vs_market:+.0f}%",
            "positioning": positioning,
            "competitive_advantage": "AI search visibility analysis not offered by competitors",
            "value_differentiators": [
                "Real-time competitive monitoring",
                "AI search optimization (ChatGPT, Claude, Perplexity)",
                "Automated battlecard generation",
                "ROI projections with business impact"
            ]
        }

    def _identify_upsell_opportunities(self, tier: ReportTier, complexity: int) -> list[dict[str, Any]]:
        """Identify upsell opportunities."""

        opportunities = []

        # Add-on services
        opportunities.extend([
            {
                "service": "Ongoing Monitoring Setup",
                "price": 500,
                "description": "3-month competitive monitoring with alerts",
                "roi": "Catch competitive threats before they impact rankings"
            },
            {
                "service": "Implementation Support",
                "price": 1000,
                "description": "30-day implementation guidance and support",
                "roi": "Ensure recommendations are properly executed"
            }
        ])

        # Tier upgrades
        if tier == ReportTier.BASIC and complexity > 40:
            opportunities.append({
                "service": "Upgrade to Pro",
                "price": 1500,
                "description": "Add AI visibility analysis and competitive benchmarking",
                "roi": "AI optimization typically increases traffic by 20-40%"
            })

        if tier in [ReportTier.BASIC, ReportTier.PRO] and complexity > 60:
            opportunities.append({
                "service": "Enterprise Features",
                "price": 2500,
                "description": "Custom branding, executive presentation, ROI projections",
                "roi": "Executive-ready materials for securing SEO budget approval"
            })

        return opportunities

    def _get_default_pricing(self, tier: ReportTier) -> dict[str, Any]:
        """Get default pricing if optimization fails."""

        defaults = {
            ReportTier.BASIC: 800,
            ReportTier.PRO: 2500,
            ReportTier.ENTERPRISE: 6000
        }

        price = defaults[tier]

        return {
            "recommended_pricing": {
                "recommended": price,
                "min": int(price * 0.8),
                "max": int(price * 1.3)
            },
            "value_proposition": {
                "roi_multiple": 3.0,
                "payback_period_months": 6
            },
            "pricing_strategy": {
                "justification": "Standard market pricing for comprehensive SEO analysis"
            }
        }

# Global pricing optimizer
pricing_optimizer = PricingOptimizer()
