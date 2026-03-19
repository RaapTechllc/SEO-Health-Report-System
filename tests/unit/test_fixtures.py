"""
Unit tests for test fixture library.

Validates that all fixture sites are properly configured and
mock responses are correctly built.
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.fixtures import (
    FIXTURE_SITES,
    FixtureSite,
    get_all_fixtures,
    get_fixture,
    get_fixtures_by_issue,
)
from tests.fixtures.mock_responses import (
    MockResponse,
    MockResponseBuilder,
    build_html_page,
    build_robots_txt,
    build_sitemap_xml,
    get_mock_responses,
)
from tests.fixtures.sites import validate_all_fixtures


class TestFixtureSiteDefinitions:
    """Tests for fixture site definitions."""

    def test_all_fixtures_have_required_fields(self):
        """All fixtures must have required fields populated."""
        for name, fixture in FIXTURE_SITES.items():
            assert fixture.name, f"{name}: name is required"
            assert fixture.url, f"{name}: url is required"
            assert fixture.company_name, f"{name}: company_name is required"
            assert fixture.trade_type, f"{name}: trade_type is required"
            assert fixture.description, f"{name}: description is required"
            assert isinstance(fixture.expected_issues, list), f"{name}: expected_issues must be a list"
            assert len(fixture.expected_score_range) == 2, f"{name}: expected_score_range must be (min, max)"

    def test_all_fixtures_have_valid_urls(self):
        """All fixture URLs must be properly formatted."""
        for name, fixture in FIXTURE_SITES.items():
            assert fixture.url.startswith(("http://", "https://")), \
                f"{name}: URL must start with http:// or https://"
            assert ".test" in fixture.url or "example" in fixture.url, \
                f"{name}: URL should use .test TLD or example domain"

    def test_all_fixtures_have_valid_score_ranges(self):
        """Score ranges must be valid (min <= max, within 0-100)."""
        for name, fixture in FIXTURE_SITES.items():
            min_score, max_score = fixture.expected_score_range
            assert 0 <= min_score <= 100, f"{name}: min score must be 0-100"
            assert 0 <= max_score <= 100, f"{name}: max score must be 0-100"
            assert min_score <= max_score, f"{name}: min must be <= max"

    def test_validate_all_fixtures_passes(self):
        """All fixtures should pass validation."""
        errors = validate_all_fixtures()
        assert not errors, f"Fixture validation failed: {errors}"

    def test_fixture_count(self):
        """We should have at least 5 fixture sites."""
        assert len(FIXTURE_SITES) >= 5, "Need at least 5 fixture sites for coverage"

    def test_fixtures_cover_different_scenarios(self):
        """Fixtures should cover different SEO issue scenarios."""
        all_issues = set()
        for fixture in FIXTURE_SITES.values():
            all_issues.update(fixture.expected_issues)

        assert len(all_issues) > 0, "Fixtures should cover various issues"

        expected_coverage = {
            "sitemap": ["sitemap"],
            "redirect": ["redirect"],
            "schema": ["schema", "structured_data"],
            "security": ["security", "https"],
            "crawl": ["disallow", "blocked", "indexable", "crawl"],
        }
        issues_str = " ".join(all_issues).lower()
        for category, keywords in expected_coverage.items():
            found = any(kw in issues_str for kw in keywords)
            assert found, f"No fixture covers '{category}' issues (looking for: {keywords})"


class TestGetFixtureFunctions:
    """Tests for fixture retrieval functions."""

    def test_get_fixture_returns_existing(self):
        """get_fixture returns fixture when it exists."""
        fixture = get_fixture("healthy_plumber")
        assert fixture is not None
        assert fixture.name == "healthy_plumber"

    def test_get_fixture_returns_none_for_missing(self):
        """get_fixture returns None for non-existent fixture."""
        fixture = get_fixture("nonexistent_fixture")
        assert fixture is None

    def test_get_all_fixtures_returns_copy(self):
        """get_all_fixtures returns a copy of all fixtures."""
        fixtures = get_all_fixtures()
        assert len(fixtures) == len(FIXTURE_SITES)

        fixtures["new_key"] = None
        assert "new_key" not in FIXTURE_SITES

    def test_get_fixtures_by_issue(self):
        """get_fixtures_by_issue returns fixtures with matching issue."""
        fixtures = get_fixtures_by_issue("sitemap_not_found")
        assert len(fixtures) >= 1
        for fixture in fixtures:
            assert "sitemap_not_found" in fixture.expected_issues


class TestMockResponseBuilder:
    """Tests for MockResponseBuilder."""

    def test_add_robots_txt(self):
        """Builder creates valid robots.txt responses."""
        builder = MockResponseBuilder()
        builder.add_robots_txt(
            "https://example.test",
            allow_all=True,
            sitemap_urls=["https://example.test/sitemap.xml"],
        )

        responses = builder.build()
        assert "https://example.test/robots.txt" in responses

        response = responses["https://example.test/robots.txt"]
        assert response.status_code == 200
        assert "User-agent" in response.content
        assert "Sitemap" in response.content

    def test_add_sitemap(self):
        """Builder creates valid sitemap responses."""
        builder = MockResponseBuilder()
        builder.add_sitemap(
            "https://example.test/sitemap.xml",
            page_urls=[
                "https://example.test/",
                "https://example.test/about",
            ],
        )

        responses = builder.build()
        response = responses["https://example.test/sitemap.xml"]

        assert response.status_code == 200
        assert "<?xml" in response.content
        assert "<urlset" in response.content
        assert "https://example.test/" in response.content
        assert "https://example.test/about" in response.content

    def test_add_html_page(self):
        """Builder creates valid HTML page responses."""
        builder = MockResponseBuilder()
        builder.add_html_page(
            "https://example.test/",
            title="Test Page",
            description="Test description",
            canonical="https://example.test/",
            has_viewport=True,
        )

        responses = builder.build()
        response = responses["https://example.test/"]

        assert response.status_code == 200
        assert "<title>Test Page</title>" in response.content
        assert 'name="description"' in response.content
        assert 'rel="canonical"' in response.content
        assert 'name="viewport"' in response.content

    def test_add_redirect(self):
        """Builder creates redirect responses."""
        builder = MockResponseBuilder()
        builder.add_redirect(
            "https://example.test/old",
            "https://example.test/new",
            status_code=301,
        )

        responses = builder.build()
        response = responses["https://example.test/old"]

        assert response.status_code == 301
        assert response.redirect_to == "https://example.test/new"
        assert response.headers["Location"] == "https://example.test/new"

    def test_add_error(self):
        """Builder creates error responses."""
        builder = MockResponseBuilder()
        builder.add_error("https://example.test/missing", 404, "Not Found")

        responses = builder.build()
        response = responses["https://example.test/missing"]

        assert response.status_code == 404
        assert response.content == "Not Found"

    def test_builder_chaining(self):
        """Builder supports method chaining."""
        responses = (
            MockResponseBuilder()
            .add_robots_txt("https://example.test")
            .add_sitemap("https://example.test/sitemap.xml", ["https://example.test/"])
            .add_html_page("https://example.test/", title="Home")
            .build()
        )

        assert len(responses) == 3


class TestBuildFunctions:
    """Tests for individual build functions."""

    def test_build_robots_txt_allow_all(self):
        """build_robots_txt creates allow-all robots.txt."""
        content = build_robots_txt(allow_all=True)
        assert "User-agent: *" in content
        assert "Allow: /" in content

    def test_build_robots_txt_disallow(self):
        """build_robots_txt creates disallow rules."""
        content = build_robots_txt(
            allow_all=False,
            disallow_paths=["/admin", "/private"],
        )
        assert "Disallow: /admin" in content
        assert "Disallow: /private" in content

    def test_build_robots_txt_with_sitemap(self):
        """build_robots_txt includes sitemap."""
        content = build_robots_txt(
            sitemap_urls=["https://example.test/sitemap.xml"],
        )
        assert "Sitemap: https://example.test/sitemap.xml" in content

    def test_build_robots_txt_with_crawl_delay(self):
        """build_robots_txt includes crawl delay."""
        content = build_robots_txt(crawl_delay=10)
        assert "Crawl-delay: 10" in content

    def test_build_sitemap_xml_basic(self):
        """build_sitemap_xml creates valid sitemap."""
        content = build_sitemap_xml(
            urls=["https://example.test/", "https://example.test/about"],
            include_lastmod=False,
        )
        assert '<?xml version="1.0"' in content
        assert "<urlset" in content
        assert "<loc>https://example.test/</loc>" in content
        assert "<loc>https://example.test/about</loc>" in content
        assert "</urlset>" in content

    def test_build_sitemap_xml_with_lastmod(self):
        """build_sitemap_xml includes lastmod dates."""
        content = build_sitemap_xml(
            urls=["https://example.test/"],
            include_lastmod=True,
        )
        assert "<lastmod>" in content

    def test_build_html_page_basic(self):
        """build_html_page creates basic HTML."""
        content = build_html_page(title="Test")
        assert "<!DOCTYPE html>" in content
        assert "<title>Test</title>" in content
        assert "<h1>Test</h1>" in content

    def test_build_html_page_with_meta(self):
        """build_html_page includes meta tags."""
        content = build_html_page(
            title="Test",
            description="Test description",
            has_viewport=True,
        )
        assert 'content="Test description"' in content
        assert 'name="viewport"' in content

    def test_build_html_page_with_canonical(self):
        """build_html_page includes canonical."""
        content = build_html_page(
            title="Test",
            canonical="https://example.test/page",
        )
        assert 'rel="canonical"' in content
        assert 'href="https://example.test/page"' in content

    def test_build_html_page_with_noindex(self):
        """build_html_page includes noindex."""
        content = build_html_page(title="Test", noindex=True)
        assert 'name="robots"' in content
        assert "noindex" in content

    def test_build_html_page_with_schema(self):
        """build_html_page includes JSON-LD schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Test Org",
        }
        content = build_html_page(title="Test", schema=schema)
        assert 'type="application/ld+json"' in content
        assert "@context" in content
        assert "Organization" in content

    def test_build_html_page_with_internal_links(self):
        """build_html_page includes internal links."""
        content = build_html_page(
            title="Test",
            internal_links=["https://example.test/about", "https://example.test/contact"],
        )
        assert 'href="https://example.test/about"' in content
        assert 'href="https://example.test/contact"' in content


class TestGetMockResponses:
    """Tests for get_mock_responses function."""

    def test_get_mock_responses_healthy_plumber(self):
        """get_mock_responses returns responses for healthy_plumber."""
        responses = get_mock_responses("healthy_plumber")

        assert len(responses) > 0

        robots_key = [k for k in responses.keys() if "robots.txt" in k]
        assert len(robots_key) == 1
        assert responses[robots_key[0]].status_code == 200

    def test_get_mock_responses_nonexistent(self):
        """get_mock_responses returns empty dict for nonexistent fixture."""
        responses = get_mock_responses("nonexistent")
        assert responses == {}

    def test_mock_responses_match_fixture_config(self):
        """Mock responses match the fixture configuration."""
        fixture = get_fixture("broken_sitemap")
        responses = get_mock_responses("broken_sitemap")

        sitemap_url = f"{fixture.url}/sitemap.xml"
        assert sitemap_url in responses
        assert responses[sitemap_url].status_code == 404


class TestExpectedResultsFiles:
    """Tests for expected results JSON files."""

    @pytest.fixture
    def results_dir(self):
        """Get the expected results directory path."""
        return Path(__file__).parent.parent / "fixtures" / "expected_results"

    def test_expected_results_dir_exists(self, results_dir):
        """Expected results directory should exist."""
        assert results_dir.exists(), f"Expected results dir not found: {results_dir}"

    def test_expected_results_files_are_valid_json(self, results_dir):
        """All JSON files in expected_results should be valid."""
        json_files = list(results_dir.glob("*.json"))
        assert len(json_files) > 0, "No JSON files found in expected_results"

        for json_file in json_files:
            with open(json_file) as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict), f"{json_file.name}: must be a dict"
                except json.JSONDecodeError as e:
                    pytest.fail(f"{json_file.name}: Invalid JSON - {e}")

    def test_expected_results_have_required_fields(self, results_dir):
        """Expected results files must have required fields."""
        required_fields = [
            "fixture_name",
            "url",
            "expected_score_range",
            "expected_issues",
        ]

        for json_file in results_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)

            for field in required_fields:
                assert field in data, f"{json_file.name}: missing required field '{field}'"

    def test_expected_results_match_fixtures(self, results_dir):
        """Expected results should correspond to existing fixtures."""
        for json_file in results_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)

            fixture_name = data.get("fixture_name")
            assert fixture_name in FIXTURE_SITES, \
                f"{json_file.name}: fixture_name '{fixture_name}' not found in FIXTURE_SITES"

            fixture = FIXTURE_SITES[fixture_name]
            assert data["url"] == fixture.url, \
                f"{json_file.name}: URL mismatch with fixture"


class TestMockResponseDataclass:
    """Tests for MockResponse dataclass."""

    def test_mock_response_defaults(self):
        """MockResponse has sensible defaults."""
        response = MockResponse()
        assert response.status_code == 200
        assert response.content == ""
        assert response.content_type == "text/html"
        assert response.headers == {}
        assert response.response_time_ms == 100
        assert response.redirect_to is None

    def test_mock_response_to_dict(self):
        """MockResponse.to_dict() returns dict representation."""
        response = MockResponse(
            status_code=301,
            content="Moved",
            redirect_to="https://example.test/new",
        )
        data = response.to_dict()

        assert data["status_code"] == 301
        assert data["content"] == "Moved"
        assert data["redirect_to"] == "https://example.test/new"


class TestFixtureSiteValidation:
    """Tests for FixtureSite.validate() method."""

    def test_validate_valid_fixture(self):
        """validate() returns empty list for valid fixture."""
        fixture = FixtureSite(
            name="test",
            url="https://test.example",
            company_name="Test Co",
            trade_type="Test",
            description="Test fixture",
            expected_issues=[],
            expected_score_range=(50, 100),
        )
        errors = fixture.validate()
        assert errors == []

    def test_validate_invalid_url(self):
        """validate() catches invalid URL format."""
        fixture = FixtureSite(
            name="test",
            url="invalid-url",
            company_name="Test Co",
            trade_type="Test",
            description="Test fixture",
            expected_issues=[],
            expected_score_range=(50, 100),
        )
        errors = fixture.validate()
        assert any("URL" in e for e in errors)

    def test_validate_invalid_score_range(self):
        """validate() catches invalid score range."""
        fixture = FixtureSite(
            name="test",
            url="https://test.example",
            company_name="Test Co",
            trade_type="Test",
            description="Test fixture",
            expected_issues=[],
            expected_score_range=(100, 50),
        )
        errors = fixture.validate()
        assert any("score_range" in e for e in errors)
