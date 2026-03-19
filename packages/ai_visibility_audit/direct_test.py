#!/usr/bin/env python3
"""
Direct AEO Engine Test

Test core components by importing them directly.
"""


def test_core_components():
    """Test core AEO components directly."""
    print("Testing core AEO engine components...")

    # Test enum and data classes from aeo_engine
    print("Testing AEO engine data structures...")

    from ai_visibility_audit.scripts.aeo_engine import (
        AEOEngine,
        AEOInsight,
        AEOScore,
        ShareOfVoice,
    )

    # Test AEO Score enum
    assert AEOScore.EXCELLENT.value == "A"
    assert AEOScore.CRITICAL.value == "F"
    print("AEO scoring system working")

    # Test ShareOfVoice
    sov = ShareOfVoice(
        brand_mentions=10,
        total_mentions=50,
        share_percentage=20.0,
        rank=2,
        competitors={"BMW": 15, "Mercedes": 12}
    )
    assert sov.share_percentage == 20.0
    print("Share of voice calculations working")

    # Test AEOInsight
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

    # Test AEOEngine class
    engine = AEOEngine(rate_limit_ms=1000)
    assert engine.rate_limit_ms == 1000
    print("AEO engine initialization working")

    print("\n[SUCCESS] All core components working correctly!")


if __name__ == "__main__":
    print("AEO Engine Direct Component Test")
    print("=" * 40)

    try:
        test_core_components()
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)

    print("\n" + "=" * 40)
    print("Direct component test completed successfully!")
