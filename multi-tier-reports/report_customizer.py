import logging
from typing import Any

from models import ReportConfig, ReportTier, TierRecommendation


class ReportCustomizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Define tier configurations
        self.tier_configs = {
            ReportTier.BASIC: {
                "include_sections": [
                    "executive_summary",
                    "technical_audit",
                    "basic_recommendations"
                ],
                "analysis_depth": "basic",
                "branding_level": "none",
                "competitive_analysis": False,
                "ai_visibility_focus": False,
                "estimated_time": 30,
                "features": [
                    "Technical SEO audit",
                    "Basic recommendations",
                    "PDF report"
                ]
            },
            ReportTier.PRO: {
                "include_sections": [
                    "executive_summary",
                    "technical_audit",
                    "content_analysis",
                    "ai_visibility_audit",
                    "competitive_overview",
                    "prioritized_recommendations",
                    "implementation_roadmap"
                ],
                "analysis_depth": "standard",
                "branding_level": "basic",
                "competitive_analysis": True,
                "ai_visibility_focus": True,
                "estimated_time": 60,
                "features": [
                    "Complete SEO health audit",
                    "AI search visibility analysis",
                    "Competitive benchmarking",
                    "Branded PDF report",
                    "Implementation roadmap"
                ]
            },
            ReportTier.ENTERPRISE: {
                "include_sections": [
                    "executive_summary",
                    "technical_audit",
                    "content_analysis",
                    "ai_visibility_audit",
                    "comprehensive_competitive_analysis",
                    "market_positioning",
                    "roi_projections",
                    "detailed_recommendations",
                    "implementation_roadmap",
                    "ongoing_monitoring_setup"
                ],
                "analysis_depth": "comprehensive",
                "branding_level": "custom",
                "competitive_analysis": True,
                "ai_visibility_focus": True,
                "estimated_time": 90,
                "features": [
                    "Comprehensive SEO audit",
                    "Advanced AI visibility optimization",
                    "Detailed competitive analysis",
                    "Custom branded reports",
                    "ROI projections",
                    "Ongoing monitoring setup",
                    "Executive presentation deck"
                ]
            }
        }

    def customize_report_config(self, tier_recommendation: TierRecommendation,
                               custom_requirements: dict[str, Any] = None) -> ReportConfig:
        """Create customized report configuration based on tier and requirements."""

        try:
            tier = tier_recommendation.recommended_tier
            base_config = self.tier_configs[tier].copy()

            # Apply custom requirements if provided
            if custom_requirements:
                base_config = self._apply_custom_requirements(base_config, custom_requirements)

            # Adjust based on site complexity
            base_config = self._adjust_for_complexity(base_config, tier_recommendation.site_complexity_score)

            return ReportConfig(
                tier=tier,
                include_sections=base_config["include_sections"],
                analysis_depth=base_config["analysis_depth"],
                branding_level=base_config["branding_level"],
                competitive_analysis=base_config["competitive_analysis"],
                ai_visibility_focus=base_config["ai_visibility_focus"],
                estimated_time=base_config["estimated_time"],
                target_price=tier_recommendation.pricing_suggestion["recommended"]
            )

        except Exception as e:
            self.logger.error(f"Report customization failed: {e}")
            # Return safe default
            return ReportConfig(
                tier=ReportTier.PRO,
                include_sections=self.tier_configs[ReportTier.PRO]["include_sections"],
                analysis_depth="standard",
                branding_level="basic",
                competitive_analysis=True,
                ai_visibility_focus=True,
                estimated_time=60,
                target_price=2500
            )

    def _apply_custom_requirements(self, config: dict[str, Any], requirements: dict[str, Any]) -> dict[str, Any]:
        """Apply custom requirements to base configuration."""

        # Budget constraints
        if requirements.get("budget_max"):
            budget = requirements["budget_max"]
            if budget < 1500:
                config["branding_level"] = "none"
                config["competitive_analysis"] = False
            elif budget < 4000:
                config["branding_level"] = "basic"

        # Timeline constraints
        if requirements.get("timeline_days"):
            timeline = requirements["timeline_days"]
            if timeline < 3:
                config["analysis_depth"] = "basic"
                config["estimated_time"] = min(config["estimated_time"], 30)
            elif timeline < 7:
                config["analysis_depth"] = "standard"
                config["estimated_time"] = min(config["estimated_time"], 60)

        # Specific focus areas
        if requirements.get("focus_areas"):
            focus_areas = requirements["focus_areas"]

            if "ai_visibility" in focus_areas:
                config["ai_visibility_focus"] = True
                if "ai_visibility_audit" not in config["include_sections"]:
                    config["include_sections"].append("ai_visibility_audit")

            if "competitive" in focus_areas:
                config["competitive_analysis"] = True
                if "competitive_overview" not in config["include_sections"]:
                    config["include_sections"].append("competitive_overview")

            if "technical_only" in focus_areas:
                config["include_sections"] = ["executive_summary", "technical_audit", "basic_recommendations"]
                config["competitive_analysis"] = False
                config["ai_visibility_focus"] = False

        # Branding requirements
        if requirements.get("custom_branding"):
            config["branding_level"] = "custom"

        return config

    def _adjust_for_complexity(self, config: dict[str, Any], complexity_score: int) -> dict[str, Any]:
        """Adjust configuration based on site complexity."""

        # High complexity sites need more time
        if complexity_score > 80:
            config["estimated_time"] = int(config["estimated_time"] * 1.3)
            config["analysis_depth"] = "comprehensive"

        # Low complexity sites can be streamlined
        elif complexity_score < 30:
            config["estimated_time"] = int(config["estimated_time"] * 0.8)
            if config["analysis_depth"] == "comprehensive":
                config["analysis_depth"] = "standard"

        return config

    def get_tier_comparison(self) -> dict[str, Any]:
        """Get comparison of all tiers for client presentation."""

        comparison = {}

        for tier in ReportTier:
            config = self.tier_configs[tier]
            comparison[tier.value] = {
                "name": tier.value.title(),
                "estimated_time": f"{config['estimated_time']} minutes",
                "analysis_depth": config["analysis_depth"].title(),
                "features": config["features"],
                "includes_ai_visibility": config["ai_visibility_focus"],
                "includes_competitive": config["competitive_analysis"],
                "branding_level": config["branding_level"].title(),
                "best_for": self._get_best_for_description(tier)
            }

        return comparison

    def _get_best_for_description(self, tier: ReportTier) -> str:
        """Get description of what each tier is best for."""

        descriptions = {
            ReportTier.BASIC: "Small businesses and startups needing essential SEO insights",
            ReportTier.PRO: "Growing companies wanting comprehensive analysis with AI optimization",
            ReportTier.ENTERPRISE: "Large organizations requiring detailed competitive intelligence and custom reporting"
        }

        return descriptions.get(tier, "Standard SEO analysis")

    def calculate_upsell_opportunities(self, current_tier: ReportTier,
                                     complexity_score: int) -> list[dict[str, Any]]:
        """Calculate upsell opportunities to higher tiers."""

        opportunities = []

        if current_tier == ReportTier.BASIC:
            # Upsell to Pro
            pro_benefits = [
                "AI search visibility analysis (capture ChatGPT/Claude traffic)",
                "Competitive benchmarking against top competitors",
                "Branded report with your logo and colors",
                "Implementation roadmap with priorities"
            ]

            opportunities.append({
                "target_tier": "Pro",
                "additional_cost": 1000,
                "benefits": pro_benefits,
                "roi_justification": "AI visibility alone can increase traffic by 20-40%"
            })

            # Upsell to Enterprise
            if complexity_score > 60:
                enterprise_benefits = [
                    "Comprehensive competitive intelligence",
                    "ROI projections and business impact analysis",
                    "Custom executive presentation deck",
                    "Ongoing monitoring setup"
                ]

                opportunities.append({
                    "target_tier": "Enterprise",
                    "additional_cost": 3000,
                    "benefits": enterprise_benefits,
                    "roi_justification": "Enterprise analysis typically delivers 3-6x ROI in first year"
                })

        elif current_tier == ReportTier.PRO:
            # Upsell to Enterprise
            if complexity_score > 50:
                enterprise_benefits = [
                    "Advanced competitive intelligence with market positioning",
                    "Detailed ROI projections and business case",
                    "Custom branded executive presentation",
                    "Ongoing competitive monitoring setup"
                ]

                opportunities.append({
                    "target_tier": "Enterprise",
                    "additional_cost": 2000,
                    "benefits": enterprise_benefits,
                    "roi_justification": "Enterprise features help secure executive buy-in and budget"
                })

        return opportunities

# Global report customizer
report_customizer = ReportCustomizer()
