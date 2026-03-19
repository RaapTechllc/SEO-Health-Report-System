#!/usr/bin/env python3
"""
Premium PDF Report Generator - Thin Wrapper

DEPRECATED: This file is a backwards-compatibility wrapper.
Use the package version directly:
    from packages.seo_health_report.premium_report import generate_premium_report

The original ~1900 line monolith has been refactored into:
    packages/seo_health_report/premium_report.py (professional B2B, no emojis)
"""

import sys

from packages.seo_health_report.premium_report import (
    PremiumReportGenerator,
    generate_premium_report,
)

__all__ = ["generate_premium_report", "PremiumReportGenerator"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_premium_report.py <json_file> [output_file]")
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    generate_premium_report(json_path, output_path)
