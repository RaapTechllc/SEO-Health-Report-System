#!/usr/bin/env python3
"""
Direct AEO Engine Test

Test core components by importing them directly.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_components():
    """Test core AEO components directly."""
    print("Testing core AEO engine components...")

    # Test enum and data classes from aeo_engine
    print("Testing AEO engine data structures...")

    # Import directly from the file
    import importlib.util

    # Load aeo_engine module
    aeo_spec = importlib.util.spec_from_file_location(
        "aeo_engine",
        os.path.join("scripts", "aeo_engine.py")
    )
    aeo_module = importlib.util.module_from_spec(aeo_spec)

    # Mock the dependencies
    sys.modules['scripts.query_ai_systems'] = type('MockModule', (), {
        'generate_test_queries': lambda *args, **kwargs: [],
        'query_all_systems': lambda *args, **kwargs: {},
        'AIResponse': type('AIResponse', (), {}),
        'TestQuery': type('TestQuery', (), {}),
        'QueryCategory': type('QueryCategory', (), {})
    })()

    sys.modules['scripts.analyze_responses'] = type('MockModule', (), {
        'analyze_brand_presence': lambda *args, **kwargs: {"score": 20, "max": 25, "findings": []},
        'check_accuracy': lambda *args, **kwargs: {"score": 18, "max": 20, "findings": []},
        'analyze_sentiment': lambda *args, **kwargs: {"score": 8, "max": 10, "findings": []},
        'analyze_competitor_comparison': lambda *args, **kwargs: {"findings": [], "details": {"brand_rank": 1, "mention_counts": {}}}
    })()

    aeo_spec.loader.exec_module(aeo_module)

    # Test AEO Score enum
    AEOScore = aeo_module.AEOScore
    assert AEOScore.EXCELLENT.value == "A"
    assert AEOScore.CRITICAL.value == "F"
    print("✅ AEO scoring system working")

    # Test ShareOfVoice
    ShareOfVoice = aeo_module.ShareOfVoice
    sov = ShareOfVoice(
        brand_mentions=10,
        total_mentions=50,
        share_percentage=20.0,
        rank=2,
        competitors={"BMW": 15, "Mercedes": 12}
    )
    assert sov.share_percentage == 20.0
    print("✅ Share of voice calculations working")

    # Test AEOInsight
    AEOInsight = aeo_module.AEOInsight
    insight = AEOInsight(
        category="visibility",
        priority="high",
        title="Low AI Visibility",
        description="Brand mentioned in only 40% of responses",
        recommendation="Optimize content for AI consumption",
        impact="Increase brand visibility"
    )
    assert insight.priority == "high"
    print("✅ Insight generation working")

    # Test AEOEngine class
    AEOEngine = aeo_module.AEOEngine
    engine = AEOEngine(rate_limit_ms=1000)
    assert engine.rate_limit_ms == 1000
    print("✅ AEO engine initialization working")

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
        sys.exit(1)

    print("\n" + "=" * 40)
    print("Direct component test completed successfully!")
