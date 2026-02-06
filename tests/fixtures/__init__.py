"""
Test fixtures for SEO Health Report E2E and integration testing.

This module provides fixture sites with known SEO issues and expected
results for validating audit accuracy.
"""

from .mock_responses import (
    MockResponse,
    MockResponseBuilder,
    build_html_page,
    build_robots_txt,
    build_sitemap_xml,
    get_mock_responses,
)
from .sites import (
    FIXTURE_SITES,
    FixtureSite,
    get_all_fixtures,
    get_fixture,
    get_fixtures_by_issue,
)

__all__ = [
    # Site fixtures
    "FixtureSite",
    "FIXTURE_SITES",
    "get_fixture",
    "get_all_fixtures",
    "get_fixtures_by_issue",
    # Mock response builders
    "MockResponse",
    "MockResponseBuilder",
    "get_mock_responses",
    "build_robots_txt",
    "build_sitemap_xml",
    "build_html_page",
]
