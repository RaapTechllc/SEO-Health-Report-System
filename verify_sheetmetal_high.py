
import json
import logging
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from packages.seo_health_report.tier_config import load_tier_config

try:
    from packages.seo_health_report.scripts.orchestrate import run_full_audit_sync
except ImportError:
    # Fallback to direct import if package structure is tricky during dev
    sys.path.append('packages/seo_health_report')
    from scripts.orchestrate import run_full_audit_sync

from generate_premium_report import generate_premium_report

# Configure logging
logging.basicConfig(level=logging.INFO)

def run_test():
    # 1. Load HIGH tier config
    print("🚀 Loading HIGH tier configuration...")
    load_tier_config("high")

    # 2. Define target
    url = "https://www.sheetmetalwerks.com"
    company = "Sheet Metal Werks"

    # 3. Run Audit
    print(f"🕵️ Starting HIGH tier audit for {company} ({url})...")
    print("   This includes Grok sentiment, competitor discovery, and premium analysis.")
    print("   TARGETING COMMERCIAL/INDUSTRIAL KEYWORDS (No Residential)")

    # Updated B2B Strategy Keywords
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
            # Pass None for competitors so auto-discovery runs
            competitor_urls=None
        )

        # Calculate composite scores (needed for report)
        # Note: run_full_audit_sync might return raw data, need to check if scoring is included
        # logic from run_audit.py suggests we need to calculate them explicitly if not already there,
        # but generate_premium_report might handle it. Use calculate_scores just in case.
        if "overall_score" not in result:
             # Try to import scorer
             try:
                 from packages.seo_health_report.scripts.calculate_scores import (
                     calculate_composite_score,
                 )
                 scores = calculate_composite_score(result)
                 result.update(scores)
             except ImportError:
                 print("⚠️ Could not import score calculator, proceeding with raw results")

        # 4. Save JSON
        output_json = "sheetmetal_audit_commercial.json"
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"✅ Audit data saved to {output_json}")

        # 5. Generate PDF
        print("📄 Generating Premium PDF Report...")
        pdf_path = generate_premium_report(output_json)
        print(f"✅ SUCCESS! Full stack report generated: {pdf_path}")

    except Exception as e:
        print(f"❌ Error running audit: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
