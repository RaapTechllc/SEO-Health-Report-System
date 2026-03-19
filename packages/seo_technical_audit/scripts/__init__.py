"""
SEO Technical Audit Scripts

Core functionality for technical SEO analysis.
"""

from .analyze_speed import (
    analyze_core_web_vitals,
    check_resource_optimization,
    get_pagespeed_insights,
)
from .check_security import (
    analyze_security,
    analyze_security_headers,
    check_https,
    check_mixed_content,
)
from .crawl_site import (
    analyze_crawlability,
    analyze_internal_links,
    check_redirects,
    check_robots,
    check_sitemaps,
)
from .validate_schema import (
    check_rich_results_eligibility,
    extract_structured_data,
    validate_schema,
    validate_structured_data,
)

__all__ = [
    'check_robots',
    'check_sitemaps',
    'analyze_crawlability',
    'check_redirects',
    'analyze_internal_links',
    'get_pagespeed_insights',
    'analyze_core_web_vitals',
    'check_resource_optimization',
    'check_https',
    'analyze_security_headers',
    'check_mixed_content',
    'analyze_security',
    'extract_structured_data',
    'validate_schema',
    'check_rich_results_eligibility',
    'validate_structured_data'
]
