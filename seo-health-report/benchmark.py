"""
Benchmark command for measuring performance before/after async conversion.
"""

import time
import argparse
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def measure_baseline(
    url: str = "https://example.com",
    company_name: str = "Test Corp",
    keywords: list = ["test"],
) -> dict:
    """
    Measure baseline sync performance.

    Returns:
        Dict with execution time and metadata
    """
    print(f"\n{'=' * 60}")
    print("PERFORMANCE BASELINE MEASUREMENT")
    print(f"{'=' * 60}")
    print(f"URL: {url}")
    print(f"Company: {company_name}")
    print(f"Keywords: {', '.join(keywords)}")
    print(f"{'=' * 60}\n")

    start_time = time.time()

    try:
        from seo_health_report import generate_report

        result = generate_report(
            target_url=url,
            company_name=company_name,
            logo_file="",  # No logo for speed
            primary_keywords=keywords,
            output_format="markdown",
            output_dir=".",
        )

        elapsed_time = time.time() - start_time

        print(f"\n{'=' * 60}")
        print("BASELINE RESULTS")
        print(f"{'=' * 60}")
        print(f"Execution Time: {elapsed_time:.2f} seconds")
        print(f"Overall Score: {result.get('overall_score', 0)}/100")
        print(f"Grade: {result.get('grade', 'N/A')}")
        print(f"Critical Issues: {len(result.get('critical_issues', []))}")
        print(f"Quick Wins: {len(result.get('quick_wins', []))}")
        print(f"{'=' * 60}\n")

        return {
            "execution_time": elapsed_time,
            "score": result.get("overall_score", 0),
            "grade": result.get("grade", "N/A"),
            "mode": "sync_baseline",
        }

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n{'=' * 60}")
        print("BASELINE MEASUREMENT FAILED")
        print(f"{'=' * 60}")
        print(f"Execution Time: {elapsed_time:.2f} seconds")
        print(f"Error: {str(e)}")
        print(f"{'=' * 60}\n")

        return {
            "execution_time": elapsed_time,
            "error": str(e),
            "mode": "sync_baseline",
        }


def compare_with_async(
    baseline_time: float, current_time: float, mode: str = "async"
) -> dict:
    """
    Compare async performance with baseline.

    Returns:
        Dict with improvement metrics
    """
    improvement = ((baseline_time - current_time) / baseline_time) * 100
    speedup = baseline_time / current_time if current_time > 0 else 0

    print(f"\n{'=' * 60}")
    print(f"PERFORMANCE COMPARISON")
    print(f"{'=' * 60}")
    print(f"Baseline (sync): {baseline_time:.2f}s")
    print(f"Current ({mode}): {current_time:.2f}s")
    print(f"Improvement: {improvement:.1f}%")
    print(f"Speedup: {speedup:.1f}x faster")
    print(f"{'=' * 60}\n")

    return {
        "baseline_time": baseline_time,
        "current_time": current_time,
        "improvement_percent": improvement,
        "speedup_factor": speedup,
        "mode": mode,
    }


def main():
    """CLI entry point for benchmarking."""
    parser = argparse.ArgumentParser(
        description="Benchmark SEO Health Report performance"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Baseline command
    baseline_parser = subparsers.add_parser(
        "baseline", help="Measure baseline sync performance"
    )
    baseline_parser.add_argument(
        "--url", default="https://example.com", help="URL to audit"
    )
    baseline_parser.add_argument("--company", default="Test Corp", help="Company name")
    baseline_parser.add_argument(
        "--keywords", default="test", help="Comma-separated keywords"
    )

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare with baseline")
    compare_parser.add_argument(
        "--baseline", required=True, type=float, help="Baseline time in seconds"
    )
    compare_parser.add_argument(
        "--current", required=True, type=float, help="Current time in seconds"
    )
    compare_parser.add_argument(
        "--mode", default="async", help="Current mode (default: async)"
    )

    args = parser.parse_args()

    if args.command == "baseline":
        keywords = [k.strip() for k in args.keywords.split(",")]
        result = measure_baseline(
            url=args.url, company_name=args.company, keywords=keywords
        )
        print(f"\n[INFO] Save baseline time for comparison:")
        print(
            f"   python -m seo_health_report.benchmark compare --baseline {result['execution_time']:.2f} --current <NEW_TIME>\n"
        )

    elif args.command == "compare":
        compare_with_async(
            baseline_time=args.baseline, current_time=args.current, mode=args.mode
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
