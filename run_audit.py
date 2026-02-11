#!/usr/bin/env python3
"""
SEO Health Report - Main Entry Point

Run comprehensive SEO audits using the orchestration system.
For agent-based workflows, use the Kiro agents in .kiro/agents/

Usage:
    python run_audit.py --url https://example.com --company "Example Co" --keywords "seo,marketing"
    python run_audit.py --config audit_config.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for package imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from packages.seo_health_report.scripts.logger import get_logger
from packages.seo_health_report.scripts.orchestrate import run_full_audit_sync

logger = get_logger(__name__)


def generate_llm_executive_summary(
    result: dict, scores: dict, company_name: str
) -> str | None:
    """
    Generate an LLM-powered executive summary using whatever AI provider is available.
    Falls back gracefully to None if no provider works.
    """
    import os

    overall_score = scores.get("overall_score", 0)
    grade = scores.get("grade", "N/A")
    components = scores.get("component_scores", {})

    # Build findings summary for the prompt
    all_issues = []
    for audit_name, audit_data in result.get("audits", {}).items():
        if isinstance(audit_data, dict):
            for issue in audit_data.get("issues", [])[:5]:
                desc = issue.get("description", "") if isinstance(issue, dict) else str(issue)
                all_issues.append(f"[{audit_name}] {desc}")

    issues_text = "\n".join(all_issues[:15]) if all_issues else "No critical issues found."

    component_text = "\n".join(
        f"- {name.replace('_', ' ').title()}: {data.get('score', 'N/A')}/100"
        for name, data in components.items()
    )

    from packages.seo_health_report.human_copy import (
        EXECUTIVE_SUMMARY_TONE,
        HUMAN_TONE_SYSTEM,
        clean_ai_copy,
    )

    system_prompt = HUMAN_TONE_SYSTEM + "\n\n" + EXECUTIVE_SUMMARY_TONE

    user_prompt = f"""Write a 3-4 paragraph executive summary for {company_name}'s SEO health audit.

SCORES:
Overall: {overall_score}/100 (Grade: {grade})
{component_text}

TOP ISSUES FOUND:
{issues_text}

URL: {result.get('url', 'N/A')}

Write directly to the business owner. Be specific about their scores. State what's working, what's broken, and what they should fix first. Keep it under 250 words."""

    # Try Anthropic first
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import requests as req
            resp = req.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": os.environ.get("ANTHROPIC_MODEL_QUALITY", "claude-sonnet-4-5-20250929"),
                    "max_tokens": 500,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=30,
            )
            if resp.status_code == 200:
                text = resp.json()["content"][0]["text"]
                return clean_ai_copy(text)
        except Exception as e:
            logger.warning(f"Anthropic summary failed: {e}")

    # Try OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import requests as req
            resp = req.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.environ.get("OPENAI_MODEL_QUALITY", "gpt-4o"),
                    "max_tokens": 500,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=30,
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                return clean_ai_copy(text)
        except Exception as e:
            logger.warning(f"OpenAI summary failed: {e}")

    return None


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run SEO Health Report audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_audit.py --url https://example.com --company "Example Co"
    python run_audit.py --config audit_config.json
    python run_audit.py --url https://example.com --company "Example" --keywords "seo,marketing" --output ./reports
        """
    )

    parser.add_argument("--url", help="Target URL to audit")
    parser.add_argument("--company", help="Company name for AI visibility queries")
    parser.add_argument("--keywords", help="Comma-separated primary keywords")
    parser.add_argument("--competitors", help="Comma-separated competitor URLs")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--output", default="./reports", help="Output directory (default: ./reports)")
    parser.add_argument("--format", choices=["json", "pdf", "both"], default="json", help="Output format")

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
        from packages.seo_health_report.scripts.calculate_scores import calculate_composite_score
        scores = calculate_composite_score(result)
        result["overall_score"] = scores.get("overall_score", 0)
        result["grade"] = scores.get("grade", "N/A")
        result["component_scores"] = scores.get("component_scores", {})

        # Classify actions into DFY/DWY/DIY tiers
        print("\nClassifying action items (DFY/DWY/DIY)...")
        from packages.seo_health_report.actions.classifier import (
            classify_actions,
            get_action_summary,
        )
        actions = classify_actions(result)
        action_summary = get_action_summary(actions)
        result["actions"] = actions
        result["action_summary"] = action_summary

        # Generate LLM-powered executive summary
        print("Generating executive summary...")
        llm_summary = generate_llm_executive_summary(
            result, scores, config["company_name"]
        )
        if llm_summary:
            result["executive_summary"] = llm_summary
            result["executive_summary_source"] = "llm"
        else:
            # Fallback to template-based summary
            from packages.seo_health_report.scripts.raaptech_voice import (
                generate_executive_summary_raaptech,
            )
            critical = [
                i for audit in result.get("audits", {}).values()
                if isinstance(audit, dict)
                for i in audit.get("issues", [])
                if isinstance(i, dict) and i.get("severity") in ("critical", "high")
            ]
            result["executive_summary"] = generate_executive_summary_raaptech(
                score=result["overall_score"],
                grade=result["grade"],
                critical_issues=critical[:5],
                company_name=config["company_name"],
            )
            result["executive_summary_source"] = "template"

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

        print(f"\nAction Items: {action_summary['dfy_count']} DFY | "
              f"{action_summary['dwy_count']} DWY | {action_summary['diy_count']} DIY")

        if action_summary["quick_starts"]:
            print("\nQuick Wins (apply immediately):")
            for qs in action_summary["quick_starts"]:
                print(f"  -> {qs.get('title', 'N/A')}")

        print(f"\n--- Executive Summary ({result['executive_summary_source']}) ---")
        print(result["executive_summary"][:500])
        if len(result.get("executive_summary", "")) > 500:
            print("...")

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
