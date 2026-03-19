"""
Fixture sites for E2E and integration testing.

Each fixture represents a specific SEO scenario with known issues
and expected audit results for validation.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FixtureSite:
    """Definition of a test fixture site."""

    name: str
    url: str
    company_name: str
    trade_type: str
    description: str
    expected_issues: list[str]
    expected_score_range: tuple
    mock_responses: dict[str, Any] = field(default_factory=dict)
    expected_components: dict[str, tuple] = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Validate fixture configuration."""
        errors = []
        if not self.url.startswith(("http://", "https://")):
            errors.append(f"Invalid URL format: {self.url}")
        if len(self.expected_score_range) != 2:
            errors.append("expected_score_range must be a tuple of (min, max)")
        if self.expected_score_range[0] > self.expected_score_range[1]:
            errors.append("expected_score_range min must be <= max")
        return errors


FIXTURE_SITES: dict[str, FixtureSite] = {
    "healthy_plumber": FixtureSite(
        name="healthy_plumber",
        url="https://example-plumber.test",
        company_name="Example Plumbing Co",
        trade_type="Plumber",
        description="Well-optimized plumber site with good SEO - all basics done right",
        expected_issues=[],
        expected_score_range=(80, 100),
        keywords=["plumber", "plumbing services", "emergency plumber"],
        expected_components={
            "crawlability": (16, 20),
            "indexing": (12, 15),
            "speed": (20, 25),
            "mobile": (12, 15),
            "security": (8, 10),
            "structured_data": (10, 15),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /\nSitemap: https://example-plumber.test/sitemap.xml",
            },
            "/sitemap.xml": {
                "status": 200,
                "content": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://example-plumber.test/</loc></url>
    <url><loc>https://example-plumber.test/services</loc></url>
    <url><loc>https://example-plumber.test/contact</loc></url>
</urlset>""",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "healthy",
            },
        },
    ),

    "broken_sitemap": FixtureSite(
        name="broken_sitemap",
        url="https://broken-sitemap.test",
        company_name="Broken Sitemap HVAC",
        trade_type="HVAC",
        description="Site with missing/broken sitemap - common indexing issue",
        expected_issues=[
            "sitemap_not_found",
            "no_sitemap_in_robots",
        ],
        expected_score_range=(50, 70),
        keywords=["hvac", "air conditioning", "heating"],
        expected_components={
            "crawlability": (14, 18),
            "indexing": (2, 8),
            "speed": (18, 25),
            "mobile": (10, 15),
            "security": (8, 10),
            "structured_data": (6, 15),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /",
            },
            "/sitemap.xml": {
                "status": 404,
                "content": "Not Found",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "basic",
            },
        },
    ),

    "redirect_chains": FixtureSite(
        name="redirect_chains",
        url="https://redirect-chains.test",
        company_name="Redirect Chains Electric",
        trade_type="Electrician",
        description="Site with multiple redirect hops - hurts crawl efficiency",
        expected_issues=[
            "redirect_chain",
            "multiple_redirects",
        ],
        expected_score_range=(55, 75),
        keywords=["electrician", "electrical services", "wiring"],
        expected_components={
            "crawlability": (10, 16),
            "indexing": (10, 15),
            "speed": (15, 22),
            "mobile": (10, 15),
            "security": (6, 10),
            "structured_data": (8, 15),
        },
        mock_responses={
            "/": {
                "status": 301,
                "redirect_to": "https://redirect-chains.test/home",
            },
            "/home": {
                "status": 301,
                "redirect_to": "https://redirect-chains.test/home/",
            },
            "/home/": {
                "status": 302,
                "redirect_to": "https://redirect-chains.test/en/home/",
            },
            "/en/home/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "basic",
            },
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /\nSitemap: https://redirect-chains.test/sitemap.xml",
            },
            "/sitemap.xml": {
                "status": 200,
                "content": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://redirect-chains.test/en/home/</loc></url>
</urlset>""",
            },
        },
    ),

    "missing_schema": FixtureSite(
        name="missing_schema",
        url="https://missing-schema.test",
        company_name="No Schema Roofing",
        trade_type="Roofing",
        description="Site missing structured data - no rich results eligibility",
        expected_issues=[
            "no_structured_data",
            "no_organization_schema",
            "no_local_business_schema",
        ],
        expected_score_range=(50, 70),
        keywords=["roofing", "roof repair", "roofer"],
        expected_components={
            "crawlability": (16, 20),
            "indexing": (12, 15),
            "speed": (18, 25),
            "mobile": (12, 15),
            "security": (8, 10),
            "structured_data": (0, 5),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /\nSitemap: https://missing-schema.test/sitemap.xml",
            },
            "/sitemap.xml": {
                "status": 200,
                "content": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://missing-schema.test/</loc></url>
</urlset>""",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "no_schema",
            },
        },
    ),

    "crawl_blocked": FixtureSite(
        name="crawl_blocked",
        url="https://crawl-blocked.test",
        company_name="Blocked Crawl Landscaping",
        trade_type="Landscaping",
        description="Site blocking all crawlers - critical indexing failure",
        expected_issues=[
            "robots_disallow_all",
            "site_not_indexable",
        ],
        expected_score_range=(10, 30),
        keywords=["landscaping", "lawn care", "garden"],
        expected_components={
            "crawlability": (0, 5),
            "indexing": (0, 5),
            "speed": (0, 10),
            "mobile": (0, 10),
            "security": (6, 10),
            "structured_data": (0, 5),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nDisallow: /",
            },
            "/sitemap.xml": {
                "status": 403,
                "content": "Forbidden",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "blocked",
            },
        },
    ),

    "slow_performance": FixtureSite(
        name="slow_performance",
        url="https://slow-site.test",
        company_name="Slow Performance Painting",
        trade_type="Painting",
        description="Site with poor Core Web Vitals - fails speed audit",
        expected_issues=[
            "slow_lcp",
            "high_cls",
            "slow_fid",
            "poor_mobile_performance",
        ],
        expected_score_range=(40, 60),
        keywords=["painting", "house painter", "interior painting"],
        expected_components={
            "crawlability": (16, 20),
            "indexing": (12, 15),
            "speed": (5, 12),
            "mobile": (5, 10),
            "security": (8, 10),
            "structured_data": (8, 15),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /\nSitemap: https://slow-site.test/sitemap.xml",
            },
            "/sitemap.xml": {
                "status": 200,
                "content": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://slow-site.test/</loc></url>
</urlset>""",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "slow",
                "response_time_ms": 5000,
            },
            "_psi_mock": {
                "performance_score": 35,
                "lcp": 4500,
                "fid": 350,
                "cls": 0.35,
            },
        },
    ),

    "missing_meta": FixtureSite(
        name="missing_meta",
        url="https://missing-meta.test",
        company_name="No Meta Cleaning",
        trade_type="Cleaning",
        description="Site missing meta tags and canonical - basic SEO failures",
        expected_issues=[
            "missing_meta_description",
            "missing_canonical",
            "missing_viewport",
            "missing_title_optimization",
        ],
        expected_score_range=(45, 65),
        keywords=["cleaning", "house cleaning", "maid service"],
        expected_components={
            "crawlability": (12, 18),
            "indexing": (10, 15),
            "speed": (18, 25),
            "mobile": (5, 10),
            "security": (8, 10),
            "structured_data": (6, 15),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /\nSitemap: https://missing-meta.test/sitemap.xml",
            },
            "/sitemap.xml": {
                "status": 200,
                "content": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://missing-meta.test/</loc></url>
</urlset>""",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "missing_meta",
            },
        },
    ),

    "security_issues": FixtureSite(
        name="security_issues",
        url="http://insecure-site.test",
        company_name="Insecure Security Services",
        trade_type="Security",
        description="Site with security issues - no HTTPS, missing headers",
        expected_issues=[
            "no_https",
            "missing_security_headers",
            "mixed_content",
        ],
        expected_score_range=(35, 55),
        keywords=["security", "locks", "alarm systems"],
        expected_components={
            "crawlability": (14, 20),
            "indexing": (10, 15),
            "speed": (18, 25),
            "mobile": (10, 15),
            "security": (0, 4),
            "structured_data": (8, 15),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "insecure",
                "headers": {},
            },
        },
    ),

    "noindex_pages": FixtureSite(
        name="noindex_pages",
        url="https://noindex-pages.test",
        company_name="Noindex Flooring",
        trade_type="Flooring",
        description="Site with accidental noindex on important pages",
        expected_issues=[
            "noindex_on_important_pages",
            "meta_robots_noindex",
        ],
        expected_score_range=(40, 60),
        keywords=["flooring", "hardwood floors", "carpet"],
        expected_components={
            "crawlability": (8, 14),
            "indexing": (4, 10),
            "speed": (18, 25),
            "mobile": (12, 15),
            "security": (8, 10),
            "structured_data": (8, 15),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /\nSitemap: https://noindex-pages.test/sitemap.xml",
            },
            "/sitemap.xml": {
                "status": 200,
                "content": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://noindex-pages.test/</loc></url>
    <url><loc>https://noindex-pages.test/services</loc></url>
</urlset>""",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "noindex",
            },
        },
    ),

    "broken_internal_links": FixtureSite(
        name="broken_internal_links",
        url="https://broken-links.test",
        company_name="Broken Links Plumbing",
        trade_type="Plumber",
        description="Site with 404 internal links and poor link structure",
        expected_issues=[
            "broken_internal_links",
            "orphan_pages",
            "poor_internal_linking",
        ],
        expected_score_range=(50, 70),
        keywords=["plumber", "drain cleaning", "water heater"],
        expected_components={
            "crawlability": (10, 16),
            "indexing": (10, 15),
            "speed": (18, 25),
            "mobile": (12, 15),
            "security": (8, 10),
            "structured_data": (8, 15),
        },
        mock_responses={
            "/robots.txt": {
                "status": 200,
                "content": "User-agent: *\nAllow: /\nSitemap: https://broken-links.test/sitemap.xml",
            },
            "/sitemap.xml": {
                "status": 200,
                "content": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://broken-links.test/</loc></url>
    <url><loc>https://broken-links.test/services</loc></url>
    <url><loc>https://broken-links.test/about</loc></url>
</urlset>""",
            },
            "/": {
                "status": 200,
                "content_type": "text/html",
                "html_template": "broken_links",
            },
            "/services": {
                "status": 404,
                "content": "Not Found",
            },
            "/about": {
                "status": 404,
                "content": "Not Found",
            },
        },
    ),
}


def get_fixture(name: str) -> Optional[FixtureSite]:
    """Get a fixture site by name."""
    return FIXTURE_SITES.get(name)


def get_all_fixtures() -> dict[str, FixtureSite]:
    """Get all fixture sites."""
    return FIXTURE_SITES.copy()


def get_fixtures_by_issue(issue_type: str) -> list[FixtureSite]:
    """Get all fixtures that have a specific expected issue."""
    return [
        fixture for fixture in FIXTURE_SITES.values()
        if issue_type in fixture.expected_issues
    ]


def validate_all_fixtures() -> dict[str, list[str]]:
    """Validate all fixture configurations."""
    results = {}
    for name, fixture in FIXTURE_SITES.items():
        errors = fixture.validate()
        if errors:
            results[name] = errors
    return results


__all__ = [
    "FixtureSite",
    "FIXTURE_SITES",
    "get_fixture",
    "get_all_fixtures",
    "get_fixtures_by_issue",
    "validate_all_fixtures",
]
