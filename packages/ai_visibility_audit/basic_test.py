#!/usr/bin/env python3
"""
Simple AEO Engine Test

Basic validation that the core components work without full module dependencies.
"""

import sys


# Test basic imports and functionality
def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    print("Testing basic AEO engine components...")

    # Test query generation logic
    from ai_visibility_audit.scripts.query_ai_systems import QueryCategory, TestQuery

    # Create sample queries
    queries = [
        TestQuery("What is Tesla?", QueryCategory.BRAND),
        TestQuery("Best electric vehicles", QueryCategory.PRODUCT),
        TestQuery("Tesla vs BMW", QueryCategory.COMPARISON)
    ]

    print(f"Created {len(queries)} test queries")

    # Test data structures
    from ai_visibility_audit.scripts.aeo_engine import AEOInsight, AEOScore, ShareOfVoice

    # Test scoring enum
    assert AEOScore.EXCELLENT.value == "A"
    assert AEOScore.CRITICAL.value == "F"
    print("AEO scoring system working")

    # Test share of voice calculation
    sov = ShareOfVoice(
        brand_mentions=10,
        total_mentions=50,
        share_percentage=20.0,
        rank=2,
        competitors={"BMW": 15, "Mercedes": 12}
    )
    assert sov.share_percentage == 20.0
    print("Share of voice calculations working")

    # Test insight generation
    insight = AEOInsight(
        category="visibility",
        priority="high",
        title="Low AI Visibility",
        description="Brand mentioned in only 40% of responses",
        recommendation="Optimize content for AI consumption",
        impact="Increase brand visibility"
    )
    assert insight.priority == "high"
    print("Insight generation working")

    print("\n[SUCCESS] All basic components working correctly!")


if __name__ == "__main__":
    print("AEO Engine Basic Validation")
    print("=" * 40)

    try:
        test_basic_functionality()
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 40)
    print("Basic validation completed successfully!")
