"""
Premium Report Integration

Integrates market intelligence into the premium PDF report generator.
This is what transforms a $500 report into a $5,000 report.
"""

import asyncio
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from competitive_intel.market_intelligence import (
    DiscoveredCompetitor,
    IndustryClassification,
    analyze_market_landscape,
    benchmark_against_competitors,
    generate_premium_executive_summary,
)

logger = logging.getLogger(__name__)


async def run_market_analysis(
    audit_data: dict[str, Any],
    products_services: Optional[list[str]] = None,
    location: Optional[str] = None,
    max_competitors: int = 8
) -> dict[str, Any]:
    """
    Run comprehensive market analysis for a completed audit.

    This adds:
    - Industry classification (niche identification)
    - Competitor discovery
    - Market landscape analysis
    - Competitive benchmarking
    - Premium executive summary

    Returns enhanced audit data with market intelligence.
    """
    company_name = audit_data.get("company_name", "Company")
    url = audit_data.get("url", "")

    # Use provided products/services or extract from audit
    if not products_services:
        products_services = audit_data.get("primary_keywords", [])
        if not products_services:
            products_services = ["services", "products"]  # Fallback

    logger.info(f"Running market analysis for {company_name}")

    # Step 1: Analyze market landscape (includes classification + competitor discovery)
    market_landscape = await analyze_market_landscape(
        company_name=company_name,
        url=url,
        products_services=products_services,
        location=location
    )

    logger.info(f"Classified as: {market_landscape.classification.industry} > {market_landscape.classification.vertical} > {market_landscape.classification.niche}")
    logger.info(f"Discovered {len(market_landscape.competitors)} competitors")

    # Step 2: Run REAL audits on competitors
    logger.info(f"Running real audits on {min(max_competitors, len(market_landscape.competitors))} competitors...")
    competitor_audits = []
    for competitor in market_landscape.competitors[:max_competitors]:
        # Run actual audit on competitor sites
        competitor_audit = await _run_real_competitor_audit(
            competitor,
            market_landscape.classification
        )
        competitor_audits.append(competitor_audit)

    # Filter to only successful audits
    successful_audits = [a for a in competitor_audits if a.get("data_source") == "real_audit"]
    logger.info(f"Successfully audited {len(successful_audits)} of {len(competitor_audits)} competitors")

    # Step 3: Benchmark against competitors
    benchmark_report = await benchmark_against_competitors(
        client_audit=audit_data,
        competitor_audits=competitor_audits,
        classification=market_landscape.classification
    )

    logger.info(f"Market position: #{benchmark_report.market_position_rank} of {len(competitor_audits) + 1}")

    # Step 4: Generate premium executive summary
    executive_summary = await generate_premium_executive_summary(
        client_audit=audit_data,
        benchmark_report=benchmark_report,
        market_landscape=market_landscape
    )

    # Step 5: Enhance audit data with market intelligence
    enhanced_data = audit_data.copy()
    enhanced_data["market_intelligence"] = {
        "classification": asdict(market_landscape.classification),
        "market_landscape": {
            "market_size_estimate": market_landscape.market_size_estimate,
            "growth_trend": market_landscape.growth_trend,
            "market_leaders": market_landscape.market_leaders,
            "emerging_players": market_landscape.emerging_players,
            "ai_visibility_opportunity": market_landscape.ai_visibility_opportunity,
            "analysis_date": market_landscape.analysis_date.isoformat(),
        },
        "competitors": [
            {
                "name": c.name,
                "url": c.url,
                "description": c.description,
                "why_competitor": c.why_competitor,
                "estimated_strength": c.estimated_strength,
                "geographic_overlap": c.geographic_overlap,
                "service_overlap": c.service_overlap,
            }
            for c in market_landscape.competitors
        ],
        "benchmark": {
            "market_position_rank": benchmark_report.market_position_rank,
            "market_position_percentile": benchmark_report.market_position_percentile,
            "vs_market_average": benchmark_report.vs_market_average,
            "competitive_advantages": benchmark_report.competitive_advantages,
            "critical_gaps": benchmark_report.critical_gaps,
            "market_opportunities": benchmark_report.market_opportunities,
            "ai_visibility_rank": benchmark_report.ai_visibility_rank,
            "ai_visibility_gap_to_leader": benchmark_report.ai_visibility_gap_to_leader,
            "ai_optimization_priorities": benchmark_report.ai_optimization_priorities,
        },
        "competitor_benchmarks": [
            {
                "competitor_name": b.competitor_name,
                "competitor_url": b.competitor_url,
                "overall_score_diff": b.overall_score_diff,
                "technical_score_diff": b.technical_score_diff,
                "content_score_diff": b.content_score_diff,
                "ai_visibility_score_diff": b.ai_visibility_score_diff,
                "strengths_vs_competitor": b.strengths_vs_competitor,
                "weaknesses_vs_competitor": b.weaknesses_vs_competitor,
                "quick_wins": b.quick_wins,
                "strategic_investments": b.strategic_investments,
            }
            for b in benchmark_report.competitor_benchmarks
        ],
        "premium_executive_summary": executive_summary,
    }

    return enhanced_data


async def _run_real_competitor_audit(
    competitor: 'DiscoveredCompetitor',
    classification: IndustryClassification,
    rate_limiter_delay: float = 2.0
) -> dict[str, Any]:
    """
    Run a REAL SEO audit on a competitor URL.

    This replaces the old fake/mock scoring with actual crawls and analysis.
    Rate-limited to prevent abuse.
    """
    import asyncio

    # Import the real audit orchestrator
    sys.path.insert(0, str(project_root / "packages" / "seo_health_report"))
    from scripts.calculate_scores import calculate_composite_score
    from scripts.orchestrate import run_full_audit

    logger.info(f"Running real audit on competitor: {competitor.name} ({competitor.url})")

    try:
        # Rate limit: wait before each competitor audit
        await asyncio.sleep(rate_limiter_delay)

        # Run the REAL audit
        competitor_result = await run_full_audit(
            target_url=competitor.url,
            company_name=competitor.name,
            primary_keywords=[classification.niche] if classification.niche else ["services"],
            competitor_urls=[],  # Don't recurse
        )

        # Calculate real scores
        scores = calculate_composite_score(competitor_result)
        overall_score = scores.get("overall_score", 0)
        grade = scores.get("grade", "N/A")

        # Extract component scores
        tech_score = competitor_result.get("audits", {}).get("technical", {}).get("score")
        content_score = competitor_result.get("audits", {}).get("content", {}).get("score")
        ai_score = competitor_result.get("audits", {}).get("ai_visibility", {}).get("score")

        logger.info(f"Competitor audit complete: {competitor.name} = {overall_score}/100")

        return {
            "company_name": competitor.name,
            "url": competitor.url,
            "overall_score": overall_score,
            "grade": grade,
            "data_source": "real_audit",
            "audits": {
                "technical": {"score": tech_score},
                "content": {"score": content_score},
                "ai_visibility": {"score": ai_score},
            }
        }

    except Exception as e:
        logger.warning(f"Competitor audit failed for {competitor.name}: {e}")
        return {
            "company_name": competitor.name,
            "url": competitor.url,
            "overall_score": None,
            "grade": "N/A",
            "data_source": "audit_failed",
            "error": str(e),
            "audits": {
                "technical": {"score": None},
                "content": {"score": None},
                "ai_visibility": {"score": None},
            }
        }


def run_market_analysis_sync(
    audit_data: dict[str, Any],
    products_services: Optional[list[str]] = None,
    location: Optional[str] = None,
    max_competitors: int = 8
) -> dict[str, Any]:
    """Sync wrapper for run_market_analysis."""
    return asyncio.run(run_market_analysis(
        audit_data, products_services, location, max_competitors
    ))


def enhance_audit_with_market_intel(json_path: str, output_path: str = None) -> str:
    """
    Enhance an existing audit JSON with market intelligence.

    Args:
        json_path: Path to existing audit JSON
        output_path: Optional output path (defaults to _ENHANCED.json)

    Returns:
        Path to enhanced JSON file
    """
    with open(json_path) as f:
        audit_data = json.load(f)

    # Run market analysis
    enhanced_data = run_market_analysis_sync(audit_data)

    # Save enhanced data
    if output_path is None:
        output_path = json_path.replace(".json", "_ENHANCED.json")

    with open(output_path, "w") as f:
        json.dump(enhanced_data, f, indent=2, default=str)

    print(f"[OK] Enhanced audit saved: {output_path}")
    return output_path


__all__ = [
    'run_market_analysis',
    'run_market_analysis_sync',
    'enhance_audit_with_market_intel',
]
