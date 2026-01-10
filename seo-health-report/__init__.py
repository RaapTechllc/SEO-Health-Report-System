"""
SEO Health Report - Master Orchestrator

Generate comprehensive, branded SEO health reports by orchestrating
technical, content, and AI visibility audits.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from .scripts.orchestrate import (
    run_full_audit,
    collect_all_issues,
    collect_all_recommendations,
    identify_quick_wins,
    identify_critical_issues
)
from .scripts.calculate_scores import (
    calculate_composite_score,
    determine_grade,
    get_grade_description
)
from .scripts.generate_summary import generate_executive_summary
from .scripts.build_report import build_report_document
from .scripts.apply_branding import apply_branding


__version__ = "1.0.0"


def clear_all_caches():
    """Clear all cached data."""
    try:
        from .scripts.cache import clear_cache
        clear_cache()
        print("All caches cleared successfully")
    except ImportError:
        print("Cache module not available")
    except Exception as e:
        print(f"Error clearing caches: {e}")


def get_cache_stats():
    """Get cache statistics."""
    try:
        from .scripts.cache import get_cache_stats
        return get_cache_stats()
    except ImportError:
        return {"error": "Cache module not available"}
    except Exception as e:
        return {"error": str(e)}


def generate_report(
    target_url: str,
    company_name: str,
    logo_file: str,
    primary_keywords: List[str],
    brand_colors: Optional[Dict[str, str]] = None,
    competitor_urls: Optional[List[str]] = None,
    output_format: str = "docx",
    output_dir: Optional[str] = None,
    preparer_name: str = "SEO Health Report System",
    ground_truth: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive SEO health report.

    This is the main entry point that orchestrates the full audit process.

    Args:
        target_url: Root domain to audit
        company_name: Client company name
        logo_file: Path to company logo (PNG/SVG)
        primary_keywords: 5-10 target keywords
        brand_colors: Optional brand color config {"primary": "#hex", "secondary": "#hex"}
        competitor_urls: Optional competitor URLs (up to 3)
        output_format: "docx", "pdf", or "md"
        output_dir: Output directory (defaults to current dir)
        preparer_name: Name shown as report preparer
        ground_truth: Optional facts about company for accuracy checking

    Returns:
        Dict with:
        - overall_score: Composite score (0-100)
        - grade: Letter grade (A-F)
        - component_scores: Individual audit scores
        - critical_issues: List of urgent issues
        - quick_wins: High-impact, low-effort opportunities
        - report: Output file information
        - audit_data: Full audit results
    """
    result = {
        "overall_score": 0,
        "grade": "F",
        "component_scores": {},
        "critical_issues": [],
        "quick_wins": [],
        "report": {},
        "audit_data": {},
        "warnings": [],
        "errors": []
    }

    print("=" * 60)
    print("SEO HEALTH REPORT GENERATOR")
    print("=" * 60)
    print(f"Target: {target_url}")
    print(f"Company: {company_name}")
    print("=" * 60)

    # Step 1: Run all audits
    print("\n[Step 1/5] Running audits...")
    audit_results = run_full_audit(
        target_url=target_url,
        company_name=company_name,
        primary_keywords=primary_keywords,
        competitor_urls=competitor_urls,
        ground_truth=ground_truth
    )

    result["audit_data"] = audit_results.get("audits", {})
    result["warnings"].extend(audit_results.get("warnings", []))
    result["errors"].extend(audit_results.get("errors", []))

    # Step 2: Calculate composite scores
    print("\n[Step 2/5] Calculating scores...")
    scores = calculate_composite_score(audit_results)
    result["overall_score"] = scores.get("overall_score", 0)
    result["grade"] = scores.get("grade", "F")
    result["component_scores"] = scores.get("component_scores", {})

    print(f"Overall Score: {result['overall_score']}/100 (Grade: {result['grade']})")

    # Step 3: Collect issues and recommendations
    print("\n[Step 3/5] Analyzing findings...")
    all_issues = collect_all_issues(audit_results)
    all_recommendations = collect_all_recommendations(audit_results)

    result["critical_issues"] = identify_critical_issues(all_issues)
    result["quick_wins"] = identify_quick_wins(all_recommendations)

    print(f"Found {len(result['critical_issues'])} critical issues")
    print(f"Identified {len(result['quick_wins'])} quick wins")

    # Step 4: Generate executive summary
    print("\n[Step 4/5] Generating summary...")
    executive_summary = generate_executive_summary(
        scores=scores,
        critical_issues=result["critical_issues"],
        quick_wins=result["quick_wins"],
        company_name=company_name
    )

    # Step 5: Build report document
    print("\n[Step 5/5] Building report document...")
    report_result = build_report_document(
        audit_results=audit_results,
        scores=scores,
        executive_summary=executive_summary,
        company_name=company_name,
        logo_file=logo_file,
        brand_colors=brand_colors,
        output_format=output_format,
        output_dir=output_dir,
        preparer_name=preparer_name
    )

    if report_result.get("success"):
        # Apply branding
        if logo_file or brand_colors:
            branding_result = apply_branding(
                document_path=report_result["output_path"],
                logo_file=logo_file,
                brand_colors=brand_colors,
                company_name=company_name
            )
            if not branding_result.get("success"):
                result["warnings"].append(f"Branding not fully applied: {branding_result.get('error')}")

    result["report"] = {
        "success": report_result.get("success", False),
        "format": output_format,
        "output_path": report_result.get("output_path"),
        "pages": report_result.get("pages", 0)
    }

    # Final summary
    print("\n" + "=" * 60)
    print("REPORT COMPLETE")
    print("=" * 60)
    print(f"Overall Score: {result['overall_score']}/100 ({result['grade']})")
    print(f"Report saved: {result['report'].get('output_path', 'N/A')}")

    if result["warnings"]:
        print(f"\nWarnings: {len(result['warnings'])}")
        for w in result["warnings"][:3]:
            print(f"  - {w}")

    if result["errors"]:
        print(f"\nErrors: {len(result['errors'])}")
        for e in result["errors"][:3]:
            print(f"  - {e}")

    print("=" * 60)

    return result


def format_text_report(result: Dict[str, Any]) -> str:
    """
    Format results as a plain text report for console output.

    Args:
        result: Results from generate_report()

    Returns:
        Formatted text string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("SEO HEALTH REPORT SUMMARY")
    lines.append("=" * 60)

    lines.append(f"\nOVERALL SCORE: {result['overall_score']}/100 (Grade: {result['grade']})")
    lines.append(f"\n{get_grade_description(result['grade'])}")

    lines.append("\n" + "-" * 60)
    lines.append("COMPONENT SCORES")
    lines.append("-" * 60)

    for name, data in result.get("component_scores", {}).items():
        score = data.get("score", 0)
        weight = data.get("weight", 0) * 100
        lines.append(f"  {name.replace('_', ' ').title()}: {score:.0f}/100 ({weight:.0f}% weight)")

    if result.get("critical_issues"):
        lines.append("\n" + "-" * 60)
        lines.append("CRITICAL ISSUES")
        lines.append("-" * 60)
        for issue in result["critical_issues"][:5]:
            lines.append(f"  - {issue.get('description', 'Unknown issue')}")

    if result.get("quick_wins"):
        lines.append("\n" + "-" * 60)
        lines.append("QUICK WINS")
        lines.append("-" * 60)
        for win in result["quick_wins"][:5]:
            lines.append(f"  - {win.get('action', 'Unknown action')}")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)


# CLI interface
def main():
    """Command-line interface for generating reports."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate comprehensive SEO health reports"
    )
    parser.add_argument("--url", required=True, help="Target URL to audit")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--logo", required=True, help="Path to logo file")
    parser.add_argument("--keywords", required=True, help="Comma-separated keywords")
    parser.add_argument("--competitors", help="Comma-separated competitor URLs")
    parser.add_argument("--output", default="report.docx", help="Output filename")
    parser.add_argument("--format", default="docx", choices=["docx", "pdf", "md"])
    parser.add_argument("--primary-color", help="Primary brand color (hex)")
    parser.add_argument("--secondary-color", help="Secondary brand color (hex)")

    args = parser.parse_args()

    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(",")]

    # Parse competitors
    competitors = None
    if args.competitors:
        competitors = [c.strip() for c in args.competitors.split(",")]

    # Parse colors
    colors = None
    if args.primary_color:
        colors = {"primary": args.primary_color}
        if args.secondary_color:
            colors["secondary"] = args.secondary_color

    # Determine output directory
    output_dir = os.path.dirname(args.output) or "."
    output_format = args.format

    # Generate report
    result = generate_report(
        target_url=args.url,
        company_name=args.company,
        logo_file=args.logo,
        primary_keywords=keywords,
        brand_colors=colors,
        competitor_urls=competitors,
        output_format=output_format,
        output_dir=output_dir
    )

    # Print summary
    print(format_text_report(result))


if __name__ == "__main__":
    main()


__all__ = [
    'generate_report',
    'format_text_report',
    'clear_all_caches',
    'get_cache_stats',
    'run_full_audit',
    'calculate_composite_score',
    'determine_grade',
    'generate_executive_summary',
    'build_report_document',
    'apply_branding'
]
