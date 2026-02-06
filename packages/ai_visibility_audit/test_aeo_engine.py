#!/usr/bin/env python3
"""
AEO Engine Test Script

Quick validation of the AEO analysis engine implementation.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.aeo_engine import run_aeo_analysis_sync
from scripts.query_ai_systems import generate_test_queries


def test_query_generation():
    """Test query generation functionality."""
    print("Testing query generation...")

    queries = generate_test_queries(
        brand_name="Tesla",
        products_services=["Electric Vehicles", "Solar Panels", "Energy Storage"],
        competitors=["BMW", "Mercedes", "Ford"],
        custom_queries=["What makes Tesla unique?"]
    )

    print(f"Generated {len(queries)} test queries")

    # Show sample queries by category
    categories = {}
    for query in queries:
        cat = query.category.value
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(query.query)

    for category, cat_queries in categories.items():
        print(f"\n{category.upper()} queries ({len(cat_queries)}):")
        for i, query in enumerate(cat_queries[:3], 1):  # Show first 3
            print(f"  {i}. {query}")
        if len(cat_queries) > 3:
            print(f"  ... and {len(cat_queries) - 3} more")


def test_aeo_analysis():
    """Test full AEO analysis (requires API keys)."""
    print("\nTesting AEO analysis...")

    # Check for API keys
    api_keys = {
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "PERPLEXITY_API_KEY": os.environ.get("PERPLEXITY_API_KEY"),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
        "XAI_API_KEY": os.environ.get("XAI_API_KEY"),
    }

    available_keys = [k for k, v in api_keys.items() if v]
    print(f"Available API keys: {', '.join(available_keys) if available_keys else 'None'}")

    if not available_keys:
        print("No API keys found. Set at least ANTHROPIC_API_KEY to test analysis.")
        return

    # Run minimal analysis
    try:
        result = run_aeo_analysis_sync(
            brand_name="Tesla",
            products_services=["Electric Vehicles"],
            competitors=["BMW"],
            ground_truth={
                "founded": "2003",
                "founder": "Elon Musk",
                "headquarters": "Austin"
            },
            ai_systems=["claude"] if "ANTHROPIC_API_KEY" in available_keys else None,
            rate_limit_ms=2000  # Slower for testing
        )

        print("\nAEO Analysis Results:")
        print(f"Overall Score: {result.overall_score}/100 (Grade: {result.grade.value})")
        print(f"Execution Time: {result.execution_time_ms}ms")
        print(f"API Calls Made: {result.api_calls_made}")

        print("\nComponent Scores:")
        for component, scores in result.component_scores.items():
            print(f"  {component}: {scores['score']}/{scores['max']}")

        print("\nShare of Voice:")
        print(f"  Brand mentions: {result.share_of_voice.brand_mentions}")
        print(f"  Market rank: #{result.share_of_voice.rank}")
        print(f"  Share: {result.share_of_voice.share_percentage:.1f}%")

        print(f"\nTop Insights ({len(result.insights)}):")
        for i, insight in enumerate(result.insights[:3], 1):
            print(f"  {i}. [{insight.priority.upper()}] {insight.title}")
            print(f"     {insight.description}")

        print("\n[SUCCESS] AEO analysis completed successfully!")

    except Exception as e:
        print(f"[ERROR] AEO analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("AEO Engine Validation Test")
    print("=" * 40)

    test_query_generation()
    test_aeo_analysis()

    print("\n" + "=" * 40)
    print("Test completed!")
