#!/usr/bin/env python3
"""
Verification Test: Sheet Metal Werks HIGH Tier Audit

Tests the complete audit pipeline including:
- Browser crawler (Playwright)
- Technical, Content, and AI Visibility audits
- Premium PDF report generation

Usage:
    python apps/cli/verify_sheetmetal.py
    python -m apps.cli.verify_sheetmetal
"""

import json
import logging
import sys
from pathlib import Path

# Centralized environment loading (must happen before package imports)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages.core.env import init  # noqa: E402

init()

from packages.seo_health_report.scripts.calculate_scores import (
    calculate_composite_score,  # noqa: E402
)
from packages.seo_health_report.scripts.orchestrate import run_full_audit_sync  # noqa: E402
from packages.seo_health_report.tier_config import load_tier_config  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_verification():
    """Run the full verification test."""

    # 1. Load HIGH tier config
    print("🚀 Loading HIGH tier configuration...")
    load_tier_config("high")

    # 2. Define target
    url = "https://www.sheetmetalwerks.com"
    company = "Sheet Metal Werks"

    # 3. Run Audit
    print(f"🕵️ Starting HIGH tier audit for {company} ({url})...")
    print("   This includes browser crawl, Grok sentiment, and premium analysis.")
    print("   TARGETING COMMERCIAL/INDUSTRIAL KEYWORDS (No Residential)")

    # B2B Strategy Keywords
    keywords = [
        "Data Center cooling ductwork fabrication",
        "Mission critical HVAC sheet metal",
        "Prefabricated commercial ductwork",
        "Industrial sheet metal fabrication shop",
        "Hospital grade stainless steel ductwork"
    ]

    try:
        result = run_full_audit_sync(
            target_url=url,
            company_name=company,
            primary_keywords=keywords,
            competitor_urls=None  # Auto-discovery
        )

        # Calculate composite scores
        if "overall_score" not in result:
            scores = calculate_composite_score(result)
            result.update(scores)

        # Verify browser_data was captured
        browser_data = result.get("browser_data")
        if browser_data:
            print("\n✅ Browser Crawl Data Captured:")
            print(f"   Load Time: {browser_data.get('page_load_time_ms', 0):.0f}ms")
            print(f"   Images: {browser_data.get('images_total', 0)} total, {browser_data.get('images_without_alt', 0)} without alt")
            print(f"   Canonical: {browser_data.get('canonical_url', 'Not set')}")
            print(f"   Schema.org: {len(browser_data.get('schema_json', []))} blocks")
        else:
            print("\n⚠️ Browser crawl data not available")

        # 4. Save JSON
        output_json = Path("sheetmetal_audit_verify.json")
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✅ Audit data saved to {output_json}")

        # 5. Generate PDF (import here to avoid circular deps)
        print("\n📄 Generating Premium PDF Report...")

        # Import the refactored package-based generator
        from packages.seo_health_report.premium_report import generate_premium_report

        pdf_path = generate_premium_report(str(output_json))
        print(f"✅ SUCCESS! Full stack report generated: {pdf_path}")

        # 6. Print summary
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        print(f"Overall Score: {result.get('overall_score', 'N/A')}/100")
        print(f"Grade: {result.get('grade', 'N/A')}")

        audits = result.get("audits", {})
        if audits.get("technical"):
            print(f"Technical Score: {audits['technical'].get('score', 'N/A')}")
        if audits.get("content"):
            print(f"Content Score: {audits['content'].get('score', 'N/A')}")
        if audits.get("ai_visibility"):
            print(f"AI Visibility Score: {audits['ai_visibility'].get('score', 'N/A')}")

        return 0

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_verification())
