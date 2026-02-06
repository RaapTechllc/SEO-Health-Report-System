#!/usr/bin/env python3
"""
SEO Health Report - Main CLI Entry Point

Run comprehensive SEO audits using the orchestration system.

Usage:
    python -m apps.cli.run_audit --url https://example.com --company "Example Co"
    python apps/cli/run_audit.py --config audit_config.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Centralized environment loading (must happen before package imports)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages.core.env import init  # noqa: E402

init()

from packages.seo_health_report.scripts.calculate_scores import (
    calculate_composite_score,  # noqa: E402
)
from packages.seo_health_report.scripts.logger import get_logger  # noqa: E402
from packages.seo_health_report.scripts.orchestrate import run_full_audit_sync  # noqa: E402

logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run SEO Health Report audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python apps/cli/run_audit.py --url https://example.com --company "Example Co"
    python apps/cli/run_audit.py --config audit_config.json
    python apps/cli/run_audit.py --url https://example.com --company "Example" --keywords "seo,marketing"
        """
    )

    parser.add_argument("--url", help="Target URL to audit")
    parser.add_argument("--company", help="Company name for AI visibility queries")
    parser.add_argument("--keywords", help="Comma-separated primary keywords")
    parser.add_argument("--competitors", help="Comma-separated competitor URLs")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--output", default="./reports", help="Output directory")
    parser.add_argument("--format", choices=["json", "pdf", "both"], default="json")

    return parser.parse_args()


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    with open(config_path) as f:
        return json.load(f)


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
            "primary_keywords": args.keywords.split(",") if args.keywords else [],
            "competitor_urls": args.competitors.split(",") if args.competitors else [],
        }

    # Ensure output directory exists
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SEO Health Report Audit")
    print("=" * 60)
    print(f"Target URL: {config['target_url']}")
    print(f"Company: {config['company_name']}")
    print(f"Keywords: {', '.join(config.get('primary_keywords', []))}")
    print(f"Output: {output_dir}")
    print("=" * 60)

    try:
        # Run the audit
        result = run_full_audit_sync(
            target_url=config["target_url"],
            company_name=config["company_name"],
            primary_keywords=config.get("primary_keywords", []),
            competitor_urls=config.get("competitor_urls", []),
            ground_truth=config.get("ground_truth"),
        )

        # Calculate overall score
        scores = calculate_composite_score(result)
        result["overall_score"] = scores.get("overall_score", 0)
        result["grade"] = scores.get("grade", "N/A")
        result["component_scores"] = scores.get("component_scores", {})

        # Save JSON output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = config["target_url"].replace("https://", "").replace("http://", "").replace("/", "_")
        output_file = output_dir / f"seo_audit_{domain}_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)

        # Print summary
        print("\n" + "=" * 60)
        print("AUDIT COMPLETE")
        print("=" * 60)
        print(f"Overall Score: {result['overall_score']}/100")
        print(f"Grade: {result['grade']}")
        print("\nComponent Scores:")
        for component, data in result.get("component_scores", {}).items():
            score = data.get("score", "N/A") if isinstance(data, dict) else data
            print(f"  - {component.replace('_', ' ').title()}: {score}")

        print(f"\nResults saved to: {output_file}")

        if result.get("warnings"):
            print(f"\n[WARNING] {len(result['warnings'])} warnings during audit")
        if result.get("errors"):
            print(f"[ERROR] {len(result['errors'])} errors during audit")

        return 0

    except Exception as e:
        logger.error(f"Audit failed: {e}")
        print(f"\n[ERROR] Audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
