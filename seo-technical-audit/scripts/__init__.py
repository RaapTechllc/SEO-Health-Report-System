"""
SEO Technical Audit Scripts

Core functionality for technical SEO analysis.
"""

from .crawl_site import (
    check_robots,
    check_sitemaps,
    analyze_crawlability,
    check_redirects,
    analyze_internal_links
)
from .analyze_speed import (
    get_pagespeed_insights,
    analyze_core_web_vitals,
    check_resource_optimization
)
from .check_security import (
    check_https,
    analyze_security_headers,
    check_mixed_content,
    analyze_security
)
from .validate_schema import (
    extract_structured_data,
    validate_schema,
    check_rich_results_eligibility,
    validate_structured_data
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
