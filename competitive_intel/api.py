import logging
from typing import Any

from analyzer import analyzer
from battlecards import battlecard_generator
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl


# Pydantic models
class CompetitiveAnalysisRequest(BaseModel):
    prospect_url: HttpUrl
    competitor_urls: list[HttpUrl]

class CompetitiveAnalysisResponse(BaseModel):
    analysis: dict[str, Any]
    battlecard: dict[str, Any]
    success: bool

# Router for competitive intelligence
router = APIRouter(prefix="/competitive-analysis", tags=["competitive-intelligence"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=dict[str, Any])
async def analyze_competitive_landscape(request: CompetitiveAnalysisRequest):
    """Generate comprehensive competitive analysis and battlecard."""

    try:
        prospect_url = str(request.prospect_url)
        competitor_urls = [str(url) for url in request.competitor_urls]

        logger.info(f"Starting competitive analysis: {prospect_url} vs {len(competitor_urls)} competitors")

        # Run competitive analysis
        analysis = analyzer.analyze_competitive_landscape(prospect_url, competitor_urls)

        # Generate battlecard
        battlecard = battlecard_generator.generate_battlecard(analysis)

        return {
            "success": True,
            "analysis": {
                "prospect_url": analysis.prospect_url,
                "competitor_urls": analysis.competitor_urls,
                "analysis_date": analysis.analysis_date.isoformat(),
                "comparison_matrix": analysis.comparison_matrix,
                "ai_visibility_gaps": analysis.ai_visibility_gaps,
                "win_probability": analysis.win_probability,
                "key_differentiators": analysis.key_differentiators,
                "recommendations": analysis.recommendations
            },
            "battlecard": battlecard,
            "metadata": {
                "processing_time": "< 2 minutes",
                "confidence_level": "High",
                "methodology": "Comprehensive SEO health analysis with AI visibility focus"
            }
        }

    except Exception as e:
        logger.error(f"Competitive analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/sample")
async def get_sample_analysis():
    """Get sample competitive analysis for demo purposes."""

    try:
        # Generate sample analysis
        sample_analysis = analyzer.analyze_competitive_landscape(
            "https://example.com",
            ["https://competitor1.com", "https://competitor2.com"]
        )

        sample_battlecard = battlecard_generator.generate_battlecard(sample_analysis)

        return {
            "success": True,
            "note": "This is sample data for demonstration",
            "analysis": {
                "prospect_url": sample_analysis.prospect_url,
                "competitor_urls": sample_analysis.competitor_urls,
                "comparison_matrix": sample_analysis.comparison_matrix,
                "ai_visibility_gaps": sample_analysis.ai_visibility_gaps,
                "win_probability": sample_analysis.win_probability,
                "key_differentiators": sample_analysis.key_differentiators
            },
            "battlecard": sample_battlecard
        }

    except Exception as e:
        logger.error(f"Sample analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate sample")

@router.get("/health")
async def health_check():
    """Health check for competitive intelligence service."""
    return {
        "status": "healthy",
        "service": "competitive-intelligence",
        "features": [
            "competitive_analysis",
            "battlecard_generation",
            "ai_visibility_gaps",
            "win_probability_calculation"
        ]
    }
