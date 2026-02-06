#!/usr/bin/env python3
"""
Premium SEO Audit with Market Intelligence

This is the premium audit workflow that justifies $2,000-$10,000 engagements.
It includes:
- Full SEO health audit (technical, content, AI visibility)
- Industry classification and niche identification
- Competitor discovery and analysis
- Market benchmarking
- Premium executive summary
- Professional PDF report with competitive insights

Usage:
    python run_premium_audit.py --url https://example.com --company "Example Co" --services "service1,service2"
    python run_premium_audit.py --config premium_config.json
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for package imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv('.env')


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Premium SEO Audit with Market Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_premium_audit.py --url https://example.com --company "Example Co" --services "web design,seo"
    python run_premium_audit.py --config premium_config.json
    python run_premium_audit.py --url https://example.com --company "Example" --location "Chicago, IL"
        """
    )

    parser.add_argument("--url", help="Target URL to audit")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--services", help="Comma-separated products/services")
    parser.add_argument("--location", help="Geographic location/service area")
    parser.add_argument("--competitors", help="Comma-separated known competitor URLs (optional)")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--output", default="./reports", help="Output directory (default: ./reports)")
    parser.add_argument("--skip-market-intel", action="store_true", help="Skip market intelligence (faster, basic report)")

    return parser.parse_args()


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    with open(config_path) as f:
        return json.load(f)


async def run_premium_audit(
    target_url: str,
    company_name: str,
    products_services: list,
    location: str = None,
    competitor_urls: list = None,
    output_dir: Path = None,
    skip_market_intel: bool = False
) -> dict:
    """
    Run the complete premium audit workflow.

    Returns:
        Dict with audit results and paths to generated reports
    """
    from packages.seo_health_report.scripts.calculate_scores import calculate_composite_score
    from packages.seo_health_report.scripts.orchestrate import run_full_audit

    print("=" * 70)
    print("PREMIUM SEO AUDIT WITH MARKET INTELLIGENCE")
    print("=" * 70)
    print(f"Company: {company_name}")
    print(f"URL: {target_url}")
    print(f"Services: {', '.join(products_services)}")
    if location:
        print(f"Location: {location}")
    print("=" * 70)

    # Step 1: Run base SEO audit
    print("\n[1/4] Running SEO Health Audit...")
    audit_result = await run_full_audit(
        target_url=target_url,
        company_name=company_name,
        primary_keywords=products_services,
        competitor_urls=competitor_urls or [],
    )

    # Calculate scores
    scores = calculate_composite_score(audit_result)
    audit_result["overall_score"] = scores.get("overall_score", 0)
    audit_result["grade"] = scores.get("grade", "N/A")
    audit_result["component_scores"] = scores.get("component_scores", {})

    print(f"    Overall Score: {audit_result['overall_score']}/100 (Grade: {audit_result['grade']})")

    # Step 2: Run market intelligence (unless skipped)
    if not skip_market_intel:
        print("\n[2/4] Running Market Intelligence Analysis...")
        try:
            # Import here to avoid circular imports
            sys.path.insert(0, str(project_root / "competitive_intel"))
            from dataclasses import asdict

            from market_intelligence import (
                analyze_market_landscape,
                benchmark_against_competitors,
                generate_premium_executive_summary,
            )

            # Analyze market landscape
            print("    - Classifying industry and discovering competitors...")
            market_landscape = await analyze_market_landscape(
                company_name=company_name,
                url=target_url,
                products_services=products_services,
                location=location
            )

            print(f"    - Industry: {market_landscape.classification.industry} > {market_landscape.classification.vertical}")
            print(f"    - Niche: {market_landscape.classification.niche}")
            print(f"    - Found {len(market_landscape.competitors)} competitors")

            # Run REAL audits on competitors (limited to 5 for performance)
            max_competitors = 5
            competitors_to_audit = market_landscape.competitors[:max_competitors]
            print(f"    - Running REAL audits on {len(competitors_to_audit)} competitors (this may take a few minutes)...")
            competitor_audits = []
            for comp in competitors_to_audit:
                comp_audit = await _run_real_competitor_audit(comp, market_landscape.classification)
                competitor_audits.append(comp_audit)

            # Filter out failed audits for benchmarking
            successful_audits = [a for a in competitor_audits if a.get("data_source") == "real_audit"]
            print(f"    - Successfully audited {len(successful_audits)} of {len(competitors_to_audit)} competitors")

            # Benchmark
            benchmark_report = await benchmark_against_competitors(
                client_audit=audit_result,
                competitor_audits=competitor_audits,
                classification=market_landscape.classification
            )

            print(f"    - Market Position: #{benchmark_report.market_position_rank} of {len(competitor_audits) + 1}")
            print(f"    - AI Visibility Rank: #{benchmark_report.ai_visibility_rank}")

            # Generate premium summary
            print("    - Generating premium executive summary...")
            executive_summary = await generate_premium_executive_summary(
                client_audit=audit_result,
                benchmark_report=benchmark_report,
                market_landscape=market_landscape
            )

            # Add market intelligence to audit result
            audit_result["market_intelligence"] = {
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

            # Calculate ROI projection
            print("    - Calculating ROI projections...")
            try:
                from roi_calculator import calculate_roi_projection, format_roi_for_report
                roi_projection = calculate_roi_projection(
                    audit_data=audit_result,
                    market_intel=audit_result["market_intelligence"]
                )
                audit_result["roi_projection"] = format_roi_for_report(roi_projection)
                print(f"    - Estimated monthly lost revenue: {roi_projection.estimated_monthly_lost_revenue}")
            except Exception as roi_err:
                print(f"    [WARNING] ROI calculation failed: {roi_err}")

            print("    [OK] Market intelligence complete")

        except Exception as e:
            print(f"    [WARNING] Market intelligence failed: {e}")
            print("    Continuing with basic report...")
    else:
        print("\n[2/4] Skipping Market Intelligence (--skip-market-intel)")

    # Step 3: Save JSON results
    print("\n[3/4] Saving audit results...")
    output_dir = output_dir or Path("./reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_company = "".join(c if c.isalnum() else "_" for c in company_name)[:30]

    json_path = output_dir / f"{safe_company}_SEO_Report_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(audit_result, f, indent=2, default=str)
    print(f"    JSON: {json_path}")

    # Step 4: Generate premium PDF
    print("\n[4/4] Generating Premium PDF Report...")
    try:
        from generate_premium_report import generate_premium_report
        pdf_path = str(json_path).replace(".json", "_PREMIUM.pdf")
        generate_premium_report(str(json_path), pdf_path)
        print(f"    PDF: {pdf_path}")
    except Exception as e:
        print(f"    [WARNING] PDF generation failed: {e}")
        pdf_path = None

    # Summary
    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)
    print(f"Overall Score: {audit_result['overall_score']}/100 (Grade: {audit_result['grade']})")

    if "market_intelligence" in audit_result:
        mi = audit_result["market_intelligence"]
        print(f"Market Position: #{mi['benchmark']['market_position_rank']}")
        print(f"AI Visibility Rank: #{mi['benchmark']['ai_visibility_rank']}")
        if mi['benchmark']['critical_gaps']:
            print(f"Critical Gaps: {len(mi['benchmark']['critical_gaps'])}")

    print(f"\nReports saved to: {output_dir}")

    return {
        "audit_result": audit_result,
        "json_path": str(json_path),
        "pdf_path": pdf_path,
    }


async def _run_real_competitor_audit(competitor, classification, rate_limiter_delay: float = 2.0):
    """
    Run a REAL SEO audit on a competitor URL.

    This replaces the old fake/mock scoring with actual crawls and analysis.
    Rate-limited to prevent abuse.
    """
    import asyncio

    from packages.seo_health_report.scripts.calculate_scores import calculate_composite_score
    from packages.seo_health_report.scripts.orchestrate import run_full_audit

    print(f"        → Auditing {competitor.name} ({competitor.url})...")

    try:
        # Rate limit: wait before each competitor audit
        await asyncio.sleep(rate_limiter_delay)

        # Run the REAL audit - same as we do for the client
        competitor_result = await run_full_audit(
            target_url=competitor.url,
            company_name=competitor.name,
            primary_keywords=[classification.niche] if classification.niche else ["services"],
            competitor_urls=[],  # Don't recurse into competitor's competitors
        )

        # Calculate real scores
        scores = calculate_composite_score(competitor_result)
        overall_score = scores.get("overall_score", 0)
        grade = scores.get("grade", "N/A")

        # Extract component scores
        tech_score = competitor_result.get("audits", {}).get("technical", {}).get("score")
        content_score = competitor_result.get("audits", {}).get("content", {}).get("score")
        ai_score = competitor_result.get("audits", {}).get("ai_visibility", {}).get("score")

        print(f"          ✓ {competitor.name}: {overall_score}/100 (Grade: {grade})")

        return {
            "company_name": competitor.name,
            "url": competitor.url,
            "overall_score": overall_score,
            "grade": grade,
            "data_source": "real_audit",  # Flag that this is REAL data
            "audits": {
                "technical": {"score": tech_score},
                "content": {"score": content_score},
                "ai_visibility": {"score": ai_score},
            }
        }

    except Exception as e:
        print(f"          ✗ {competitor.name}: Audit failed ({str(e)[:50]})")
        # Return a clearly marked failure - NOT fake data
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


def main():
    """Main entry point."""
    args = parse_args()

    # Load config from file or args
    if args.config:
        config = load_config(args.config)
    else:
        if not args.url or not args.company:
            print("[ERROR] Either --config or both --url and --company are required")
            sys.exit(1)

        config = {
            "target_url": args.url,
            "company_name": args.company,
            "products_services": args.services.split(",") if args.services else ["services"],
            "location": args.location,
            "competitor_urls": args.competitors.split(",") if args.competitors else [],
        }

    output_dir = Path(args.output)

    # Run the premium audit
    asyncio.run(run_premium_audit(
        target_url=config["target_url"],
        company_name=config["company_name"],
        products_services=config.get("products_services", ["services"]),
        location=config.get("location"),
        competitor_urls=config.get("competitor_urls", []),
        output_dir=output_dir,
        skip_market_intel=args.skip_market_intel,
    ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
