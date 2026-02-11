#!/usr/bin/env python3
"""
Tier Comparison Report Generator

Generates SEO reports using LOW, MEDIUM, and HIGH cost tiers
to compare quality vs cost tradeoffs.

Usage:
    python generate_tier_comparison.py <json_report_path> [tier]

    # Generate all tiers:
    python generate_tier_comparison.py reports/example.json all

    # Generate specific tier:
    python generate_tier_comparison.py reports/example.json low
    python generate_tier_comparison.py reports/example.json medium
    python generate_tier_comparison.py reports/example.json high
"""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

# Tier configurations
TIERS = {
    "low": {
        "name": "Budget Watchdog",
        "env_file": "config/tier_low.env",
        "description": "~$0.023/report | Cheapest models everywhere",
        "monthly_cost_3k": "$69"
    },
    "medium": {
        "name": "Smart Balance",
        "env_file": "config/tier_medium.env",
        "description": "~$0.051/report | Quality where it matters",
        "monthly_cost_3k": "$153"
    },
    "high": {
        "name": "Premium Agency",
        "env_file": "config/tier_high.env",
        "description": "~$0.158/report | Maximum quality",
        "monthly_cost_3k": "$474"
    }
}


def load_tier_config(tier: str) -> dict:
    """Load tier-specific environment variables."""
    if tier not in TIERS:
        raise ValueError(f"Unknown tier: {tier}. Must be one of: {list(TIERS.keys())}")

    tier_info = TIERS[tier]
    env_file = Path(tier_info["env_file"])

    if not env_file.exists():
        raise FileNotFoundError(f"Tier config not found: {env_file}")

    return dotenv_values(env_file)


def generate_report_for_tier(json_path: str, tier: str) -> str:
    """Generate a premium report using the specified tier configuration."""
    tier_info = TIERS[tier]
    tier_config = load_tier_config(tier)

    # Create tier-specific output filename
    json_file = Path(json_path)

    print(f"\n{'='*60}")
    print(f"🏷️  TIER: {tier.upper()} — {tier_info['name']}")
    print(f"📊 {tier_info['description']}")
    print(f"💰 Monthly @ 3,000 reports: {tier_info['monthly_cost_3k']}")
    print(f"{'='*60}")

    # Set environment variables for this tier
    env = os.environ.copy()
    env.update(tier_config)

    # Print key models being used
    print("\n📦 Models:")
    print(f"   OpenAI:     {tier_config.get('OPENAI_MODEL', 'default')}")
    print(f"   Anthropic:  {tier_config.get('ANTHROPIC_MODEL', 'default')}")
    print(f"   Gemini:     {tier_config.get('GOOGLE_MODEL', 'default')}")
    print(f"   Grok:       {tier_config.get('XAI_MODEL', 'default')}")
    print(f"   Perplexity: {tier_config.get('PERPLEXITY_MODEL', 'default')}")
    print(f"   Image:      {tier_config.get('GOOGLE_IMAGE_MODEL', 'default')}")

    # Run the report generator with tier-specific config
    print("\n⏳ Generating report...")

    result = subprocess.run(
        ["python3", "generate_premium_report.py", json_path],
        env=env,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )

    if result.returncode != 0:
        print("❌ Error generating report:")
        print(result.stderr)
        return None

    # Find the generated PDF
    print(result.stdout)

    # Rename to include tier
    generated_files = list(json_file.parent.glob(f"{json_file.stem}*PREMIUM*.pdf"))
    if generated_files:
        latest = max(generated_files, key=lambda p: p.stat().st_mtime)
        new_name = json_file.parent / f"{json_file.stem}_TIER_{tier.upper()}.pdf"
        latest.rename(new_name)
        print(f"✅ Report saved: {new_name}")
        return str(new_name)

    return None


def generate_comparison_summary(results: dict) -> str:
    """Generate a text summary comparing all tier results."""
    summary = []
    summary.append("\n" + "="*70)
    summary.append("📊 TIER COMPARISON SUMMARY")
    summary.append("="*70)

    for tier, info in results.items():
        tier_data = TIERS[tier]
        status = "✅" if info.get("success") else "❌"
        summary.append(f"\n{status} {tier.upper()} — {tier_data['name']}")
        summary.append(f"   Cost: {tier_data['description']}")
        if info.get("file"):
            summary.append(f"   File: {info['file']}")

    summary.append("\n" + "="*70)
    summary.append("💡 RECOMMENDATIONS:")
    summary.append("   • LOW:    Best for bulk operations, internal audits")
    summary.append("   • MEDIUM: Ideal for client-facing reports at scale")
    summary.append("   • HIGH:   Enterprise clients, maximum quality")
    summary.append("="*70 + "\n")

    return "\n".join(summary)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    json_path = sys.argv[1]
    tier_arg = sys.argv[2] if len(sys.argv) > 2 else "all"

    if not Path(json_path).exists():
        print(f"❌ File not found: {json_path}")
        sys.exit(1)

    results = {}

    if tier_arg == "all":
        tiers_to_run = ["low", "medium", "high"]
    elif tier_arg in TIERS:
        tiers_to_run = [tier_arg]
    else:
        print(f"❌ Unknown tier: {tier_arg}")
        print("   Valid options: all, low, medium, high")
        sys.exit(1)

    for tier in tiers_to_run:
        try:
            output_file = generate_report_for_tier(json_path, tier)
            results[tier] = {"success": True, "file": output_file}
        except Exception as e:
            print(f"❌ Failed to generate {tier} tier: {e}")
            results[tier] = {"success": False, "error": str(e)}

    # Print comparison summary
    if len(tiers_to_run) > 1:
        print(generate_comparison_summary(results))


if __name__ == "__main__":
    main()
