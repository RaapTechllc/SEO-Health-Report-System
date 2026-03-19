import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pricing_optimizer import pricing_optimizer
from pydantic import BaseModel, HttpUrl
from report_customizer import report_customizer
from tier_classifier import tier_classifier


# Pydantic models
class TierRecommendationRequest(BaseModel):
    target_url: HttpUrl
    budget_range: Optional[str] = None
    custom_requirements: Optional[dict[str, Any]] = None
    market_context: Optional[dict[str, Any]] = None

class TierRecommendationResponse(BaseModel):
    success: bool
    tier_recommendation: dict[str, Any]
    report_config: dict[str, Any]
    pricing_optimization: dict[str, Any]
    tier_comparison: dict[str, Any]

# Router for multi-tier reports
router = APIRouter(prefix="/tier-recommendation", tags=["multi-tier-reports"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=dict[str, Any])
async def get_tier_recommendation(request: TierRecommendationRequest):
    """Get comprehensive tier recommendation with pricing optimization."""

    try:
        target_url = str(request.target_url)
        logger.info(f"Generating tier recommendation for {target_url}")

        # Step 1: Classify site tier
        tier_recommendation = tier_classifier.classify_site_tier(
            target_url,
            request.budget_range
        )

        # Step 2: Customize report configuration
        report_config = report_customizer.customize_report_config(
            tier_recommendation,
            request.custom_requirements
        )

        # Step 3: Optimize pricing
        pricing_optimization = pricing_optimizer.optimize_pricing(
            tier_recommendation,
            request.market_context
        )

        # Step 4: Get tier comparison
        tier_comparison = report_customizer.get_tier_comparison()

        # Step 5: Calculate upsell opportunities
        upsell_opportunities = report_customizer.calculate_upsell_opportunities(
            tier_recommendation.recommended_tier,
            tier_recommendation.site_complexity_score
        )

        return {
            "success": True,
            "tier_recommendation": {
                "recommended_tier": tier_recommendation.recommended_tier.value,
                "confidence": tier_recommendation.confidence,
                "reasoning": tier_recommendation.reasoning,
                "site_complexity_score": tier_recommendation.site_complexity_score,
                "estimated_report_time": tier_recommendation.estimated_report_time
            },
            "report_config": {
                "tier": report_config.tier.value,
                "include_sections": report_config.include_sections,
                "analysis_depth": report_config.analysis_depth,
                "branding_level": report_config.branding_level,
                "competitive_analysis": report_config.competitive_analysis,
                "ai_visibility_focus": report_config.ai_visibility_focus,
                "estimated_time": report_config.estimated_time
            },
            "pricing_optimization": pricing_optimization,
            "tier_comparison": tier_comparison,
            "upsell_opportunities": upsell_opportunities,
            "metadata": {
                "analysis_date": "2026-01-12",
                "methodology": "Site complexity analysis with market pricing intelligence"
            }
        }

    except Exception as e:
        logger.error(f"Tier recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@router.get("/tiers")
async def get_tier_comparison():
    """Get comparison of all available tiers."""

    try:
        comparison = report_customizer.get_tier_comparison()

        return {
            "success": True,
            "tier_comparison": comparison,
            "pricing_ranges": {
                "basic": {"min": 500, "max": 1500, "typical": 800},
                "pro": {"min": 1500, "max": 4000, "typical": 2500},
                "enterprise": {"min": 4000, "max": 10000, "typical": 6000}
            },
            "key_differentiators": {
                "ai_visibility": "Unique AI search optimization not offered by competitors",
                "competitive_intelligence": "Real-time competitive monitoring and battlecards",
                "roi_projections": "Data-driven business impact analysis"
            }
        }

    except Exception as e:
        logger.error(f"Tier comparison failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tier comparison")

@router.post("/sample")
async def get_sample_recommendation():
    """Get sample tier recommendation for demo purposes."""

    try:
        # Generate sample recommendation
        sample_recommendation = tier_classifier.classify_site_tier("https://example.com")
        report_customizer.customize_report_config(sample_recommendation)
        sample_pricing = pricing_optimizer.optimize_pricing(sample_recommendation)

        return {
            "success": True,
            "note": "This is sample data for demonstration",
            "tier_recommendation": {
                "recommended_tier": sample_recommendation.recommended_tier.value,
                "confidence": sample_recommendation.confidence,
                "reasoning": sample_recommendation.reasoning,
                "site_complexity_score": sample_recommendation.site_complexity_score
            },
            "pricing_optimization": sample_pricing,
            "tier_comparison": report_customizer.get_tier_comparison()
        }

    except Exception as e:
        logger.error(f"Sample recommendation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate sample")

@router.get("/health")
async def health_check():
    """Health check for multi-tier reports service."""
    return {
        "status": "healthy",
        "service": "multi-tier-reports",
        "features": [
            "tier_classification",
            "report_customization",
            "pricing_optimization",
            "upsell_identification"
        ]
    }
