#!/usr/bin/env python3
"""
Test Premium Report Template

Quick test to verify the premium report template generates correctly.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'seo-health-report', 'scripts'))

def test_premium_report():
    """Test premium report generation with sample data."""

    # Sample data
    sample_overall = {
        "overall_score": 78,
        "grade": "B",
        "component_scores": {
            "technical": {"score": 72, "weight": 0.30},
            "content": {"score": 81, "weight": 0.35},
            "ai_visibility": {"score": 82, "weight": 0.35}
        }
    }

    sample_technical = {
        "score": 72,
        "grade": "C",
        "components": {
            "crawlability": {"score": 18, "max": 20, "findings": ["Robots.txt found", "Sitemap present"]},
            "speed": {"score": 15, "max": 25, "findings": ["LCP: 2.8s", "FID: 120ms"]},
            "security": {"score": 8, "max": 10, "findings": ["HTTPS enabled", "Security headers present"]},
            "mobile": {"score": 12, "max": 15, "findings": ["Mobile-friendly", "Viewport configured"]},
            "structured_data": {"score": 10, "max": 15, "findings": ["Basic schema present"]}
        }
    }

    sample_content = {
        "score": 81,
        "grade": "B",
        "components": {
            "content_quality": {"score": 20, "max": 25, "findings": ["Good content length", "Readable text"]},
            "eeat": {"score": 16, "max": 20, "findings": ["Author pages present", "Contact info visible"]},
            "topical_authority": {"score": 12, "max": 15, "findings": ["Good keyword coverage"]},
            "backlinks": {"score": 11, "max": 15, "findings": ["Moderate link profile"]},
            "internal_links": {"score": 8, "max": 10, "findings": ["Good internal structure"]}
        }
    }

    sample_ai = {
        "score": 82,
        "grade": "B",
        "components": {
            "ai_presence": {"score": 20, "max": 25, "findings": ["Brand mentioned in 80% of queries"]},
            "accuracy": {"score": 16, "max": 20, "findings": ["Most information accurate"]},
            "parseability": {"score": 12, "max": 15, "findings": ["Clean HTML structure"]},
            "knowledge_graph": {"score": 10, "max": 15, "findings": ["Limited KG presence"]},
            "citation_likelihood": {"score": 12, "max": 15, "findings": ["Some authoritative content"]},
            "sentiment": {"score": 8, "max": 10, "findings": ["Positive brand sentiment"]}
        }
    }

    sample_results = {
        "company": "Test Company",
        "url": "https://testcompany.com",
        "timestamp": "2026-01-12T11:51:09.769-06:00"
    }

    try:
        from premium_report_template import generate_premium_docx_report

        output_path = generate_premium_docx_report(
            results=sample_results,
            overall=sample_overall,
            technical=sample_technical,
            content=sample_content,
            ai=sample_ai,
            company_name="Test Company",
            target_url="https://testcompany.com",
            agency_name="RaapTech",
            client_logo_path=None,  # No logo for test
            agency_logo_path=None   # No logo for test
        )

        if output_path:
            print(f"✅ SUCCESS: Premium report generated at {output_path}")
            print("🎯 Template is working correctly!")
            return True
        else:
            print("❌ FAILED: No output path returned")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Premium Report Template...")
    print("=" * 50)

    success = test_premium_report()

    print("=" * 50)
    if success:
        print("🎉 Premium report template is ready!")
        print("📋 Next steps:")
        print("   1. Add RaapTech logo to reports/logos/raaptech_logo.png")
        print("   2. Add client logos as needed")
        print("   3. Run full audit with real data")
    else:
        print("⚠️ Premium report template needs fixes")
        print("💡 Check dependencies: pip install python-docx")
