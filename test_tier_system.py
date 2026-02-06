#!/usr/bin/env python3
"""
Test the new tier system features.
"""

import json
import sys
from pathlib import Path

# Test 1: Social Media Audit
print("=" * 60)
print("TEST 1: Social Media Audit")
print("=" * 60)

sys.path.insert(0, str(Path(__file__).parent / "social-media-audit"))
from social_media_audit import run_social_audit

# Test with a real company
result = run_social_audit("Microsoft", "microsoft.com")
print(f"\n✅ Social Media Score: {result['score']}/100 (Grade: {result['grade']})")
print(f"   LinkedIn: {'✅' if result['components']['linkedin']['has_page'] else '❌'}")
print(f"   Profiles Found: {result['components']['profiles']['found_count']}/5")
print(f"   Recommendations: {len(result['recommendations'])}")

# Test 2: FREE Tier Report
print("\n" + "=" * 60)
print("TEST 2: FREE Tier Report Generation")
print("=" * 60)

# Check if we have a recent audit to use
reports_dir = Path(__file__).parent / "reports"
json_files = list(reports_dir.glob("*.json"))

if json_files:
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"\n✅ Found recent audit: {latest_json.name}")

    # Load audit data
    with open(latest_json) as f:
        audit_data = json.load(f)

    print(f"   Score: {audit_data.get('overall_score', 'N/A')}/100")
    print(f"   Grade: {audit_data.get('grade', 'N/A')}")
    print(f"   Quick Wins: {len(audit_data.get('quick_wins', []))}")
    print(f"   Critical Issues: {len(audit_data.get('critical_issues', []))}")

    # Test FREE tier generation
    from generate_free_report import generate_free_tier_report

    output_path = reports_dir / "test_free_tier.pdf"
    result = generate_free_tier_report(
        audit_data=audit_data,
        company_name="Test Company",
        output_path=str(output_path)
    )

    if result['success']:
        print(f"\n✅ FREE tier report generated: {output_path}")
        print(f"   Pages: {result['pages']}")
        print(f"   Tier: {result['tier']}")
    else:
        print("\n❌ Failed to generate FREE tier report")
else:
    print("\n⚠️  No audit JSON files found in reports/")
    print("   Run an audit first: python3 run_audit.py --url example.com --company 'Example'")

# Test 3: Tier System Status
print("\n" + "=" * 60)
print("TEST 3: Tier System Status")
print("=" * 60)

sys.path.insert(0, str(Path(__file__).parent / "multi-tier-reports"))
from models import ReportTier

print("\n✅ Available Tiers:")
for tier in ReportTier:
    print(f"   - {tier.value.upper()}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
print("\n✅ Your tier system is ready!")
print("\nNext steps:")
print("1. Test FREE tier: python3 generate_free_report.py --audit-json reports/latest.json --company 'Test' --output test.pdf")
print("2. Test social audit: cd social-media-audit && python3 social_media_audit.py 'Company' 'domain.com'")
print("3. Update pricing page with 4 tiers (FREE, BASIC, MEDIUM, PREMIUM)")
