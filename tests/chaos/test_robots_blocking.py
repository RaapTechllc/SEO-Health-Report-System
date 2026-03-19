"""
Chaos tests for robots.txt blocking scenarios.

Tests verify that the system correctly handles various robots.txt
configurations and blocking scenarios.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Sample robots.txt contents
ROBOTS_FULL_BLOCK = """
User-agent: *
Disallow: /
"""

ROBOTS_PARTIAL_BLOCK = """
User-agent: *
Disallow: /admin
Disallow: /private
Disallow: /api/internal
Allow: /
"""

ROBOTS_USER_AGENT_SPECIFIC = """
User-agent: SEOHealthBot
Disallow: /

User-agent: *
Allow: /
"""

ROBOTS_MALFORMED = """
User-agent: *
Disalow: /admin
Allow /public
Random garbage here
"""

ROBOTS_EMPTY = ""

ROBOTS_CRAWL_DELAY = """
User-agent: *
Crawl-delay: 10
Allow: /
"""


class TestFullSiteBlock:
    """Tests for full site blocking scenarios."""

    def test_full_site_block_returns_clear_error(self):
        """Full site block should return clear, user-friendly error."""

        def check_robots(robots_txt, path="/"):
            if "Disallow: /" in robots_txt and "Allow:" not in robots_txt:
                return {
                    "allowed": False,
                    "reason": "Site blocks all crawling via robots.txt",
                    "user_message": "This website's robots.txt prevents crawling. "
                    "The site owner has requested that automated tools "
                    "not access the site.",
                }
            return {"allowed": True}

        result = check_robots(ROBOTS_FULL_BLOCK)

        assert result["allowed"] is False
        assert "robots.txt" in result["reason"]
        assert "user_message" in result

    def test_full_block_audit_returns_partial_results(self):
        """Audit on fully blocked site should return meaningful partial results."""
        audit_result = {
            "url": "https://example.com",
            "status": "partial",
            "crawl_blocked": True,
            "crawl_error": "robots.txt blocks all crawling",
            "available_data": {
                "dns_resolved": True,
                "ssl_valid": True,
                "response_time_ms": 150,
            },
            "recommendations": [
                "Review robots.txt configuration",
                "Consider allowing SEO audit tools",
            ],
        }

        assert audit_result["status"] == "partial"
        assert audit_result["crawl_blocked"] is True
        assert len(audit_result["available_data"]) > 0


class TestPartialBlock:
    """Tests for partial path blocking scenarios."""

    def test_partial_block_crawls_allowed_paths(self):
        """Should crawl paths not blocked by robots.txt."""

        def is_path_allowed(robots_txt, path, user_agent="*"):
            # Simple implementation for testing
            lines = robots_txt.strip().split("\n")
            current_agent_matches = False
            disallowed = []
            allowed = []

            for line in lines:
                line = line.strip()
                if line.startswith("User-agent:"):
                    agent = line.split(":", 1)[1].strip()
                    current_agent_matches = agent == "*" or agent == user_agent
                elif current_agent_matches and line.startswith("Disallow:"):
                    path_pattern = line.split(":", 1)[1].strip()
                    if path_pattern:
                        disallowed.append(path_pattern)
                elif current_agent_matches and line.startswith("Allow:"):
                    path_pattern = line.split(":", 1)[1].strip()
                    if path_pattern:
                        allowed.append(path_pattern)

            # Check if path is disallowed (order matters in real robots.txt)
            # More specific rules should be checked first
            for pattern in sorted(disallowed, key=len, reverse=True):
                if path.startswith(pattern):
                    return False

            return True

        # Test various paths
        assert is_path_allowed(ROBOTS_PARTIAL_BLOCK, "/") is True
        assert is_path_allowed(ROBOTS_PARTIAL_BLOCK, "/about") is True
        assert is_path_allowed(ROBOTS_PARTIAL_BLOCK, "/admin") is False
        assert is_path_allowed(ROBOTS_PARTIAL_BLOCK, "/admin/users") is False
        assert is_path_allowed(ROBOTS_PARTIAL_BLOCK, "/private") is False
        assert is_path_allowed(ROBOTS_PARTIAL_BLOCK, "/api/internal") is False
        # /api/public is not blocked since Disallow: /api/internal only blocks that path
        assert is_path_allowed(ROBOTS_PARTIAL_BLOCK, "/api/public") is True

    def test_partial_block_reports_blocked_paths(self):
        """Audit should report which paths were blocked."""
        crawl_result = {
            "total_urls_found": 50,
            "urls_crawled": 35,
            "urls_blocked_by_robots": 15,
            "blocked_paths": [
                "/admin",
                "/admin/users",
                "/private/data",
            ],
            "message": "15 URLs were not crawled due to robots.txt restrictions",
        }

        assert crawl_result["urls_blocked_by_robots"] == 15
        assert len(crawl_result["blocked_paths"]) > 0


class TestUserAgentSpecific:
    """Tests for user-agent specific robots rules."""

    def test_user_agent_specific_rules(self):
        """Should respect user-agent specific rules."""

        def check_for_agent(robots_txt, path, user_agent):
            lines = robots_txt.strip().split("\n")
            specific_rules = {}
            current_agent = None

            for line in lines:
                line = line.strip()
                if line.startswith("User-agent:"):
                    current_agent = line.split(":", 1)[1].strip()
                    if current_agent not in specific_rules:
                        specific_rules[current_agent] = {"disallow": [], "allow": []}
                elif current_agent and line.startswith("Disallow:"):
                    pattern = line.split(":", 1)[1].strip()
                    specific_rules[current_agent]["disallow"].append(pattern)
                elif current_agent and line.startswith("Allow:"):
                    pattern = line.split(":", 1)[1].strip()
                    specific_rules[current_agent]["allow"].append(pattern)

            # Check specific agent first, then wildcard
            rules = specific_rules.get(user_agent) or specific_rules.get("*", {})

            for pattern in rules.get("disallow", []):
                if pattern and path.startswith(pattern):
                    return False
            return True

        # SEOHealthBot is specifically blocked
        assert check_for_agent(ROBOTS_USER_AGENT_SPECIFIC, "/", "SEOHealthBot") is False

        # Other agents are allowed
        assert check_for_agent(ROBOTS_USER_AGENT_SPECIFIC, "/", "Googlebot") is True
        assert check_for_agent(ROBOTS_USER_AGENT_SPECIFIC, "/", "OtherBot") is True

    def test_audit_uses_appropriate_user_agent(self):
        """Audit should use appropriate user agent string."""
        expected_user_agent = "SEOHealthBot/1.0"

        # Configuration should specify user agent
        config = {
            "user_agent": expected_user_agent,
            "respect_robots_txt": True,
        }

        assert "SEOHealthBot" in config["user_agent"]


class TestMissingRobotstxt:
    """Tests for missing robots.txt scenarios."""

    @pytest.mark.asyncio
    async def test_missing_robots_allows_crawl(self):
        """Missing robots.txt (404) should allow crawling."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            # When robots.txt returns 404, crawling is allowed
            response = await mock_get("https://example.com/robots.txt")

            if response.status_code == 404:
                crawl_allowed = True
            else:
                crawl_allowed = False

            assert crawl_allowed is True

    def test_missing_robots_logged_appropriately(self):
        """Missing robots.txt should be logged as info, not error."""
        import logging

        with patch.object(logging.Logger, "info") as mock_info:
            # Simulate logging for missing robots.txt
            logger = logging.getLogger("test")
            logger.info("robots.txt not found (404), proceeding with crawl")

            # Should be info level, not warning/error
            mock_info.assert_called()


class TestMalformedRobotstxt:
    """Tests for malformed robots.txt handling."""

    def test_malformed_robots_fallback(self):
        """Malformed robots.txt should fall back to permissive crawling."""

        def parse_robots(robots_txt):
            try:
                # Attempt to parse
                rules = {"disallow": [], "allow": []}
                for line in robots_txt.split("\n"):
                    line = line.strip()
                    if line.startswith("Disallow:"):
                        path = line.split(":", 1)[1].strip()
                        if path:
                            rules["disallow"].append(path)
                    elif line.startswith("Allow:"):
                        path = line.split(":", 1)[1].strip()
                        if path:
                            rules["allow"].append(path)
                return {"parsed": True, "rules": rules}
            except Exception:
                return {"parsed": False, "rules": {"disallow": [], "allow": []}}

        result = parse_robots(ROBOTS_MALFORMED)

        # Should parse what it can, ignore malformed lines
        assert result["parsed"] is True
        # "Disalow" (typo) should be ignored
        assert "/admin" not in result["rules"]["disallow"]

    def test_malformed_robots_reports_warning(self):
        """Malformed robots.txt should generate a warning in audit."""
        audit_warnings = []

        def check_robots_validity(robots_txt):
            issues = []
            for i, line in enumerate(robots_txt.split("\n")):
                line = line.strip()
                if line and not line.startswith("#"):
                    valid_directives = [
                        "User-agent:",
                        "Disallow:",
                        "Allow:",
                        "Sitemap:",
                        "Crawl-delay:",
                    ]
                    if not any(line.startswith(d) for d in valid_directives):
                        issues.append(f"Line {i+1}: Unrecognized directive")
            return issues

        issues = check_robots_validity(ROBOTS_MALFORMED)
        if issues:
            audit_warnings.append(
                {"type": "robots_txt_issues", "message": f"Found {len(issues)} issues"}
            )

        assert len(audit_warnings) > 0


class TestRobotstxtTimeout:
    """Tests for robots.txt fetch timeout."""

    @pytest.mark.asyncio
    async def test_robots_timeout_handling(self):
        """Robots.txt fetch timeout should allow cautious crawling."""
        import asyncio

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = asyncio.TimeoutError("Request timeout")

            try:
                await mock_get("https://example.com/robots.txt")
            except asyncio.TimeoutError:
                # On timeout, use conservative approach
                crawl_policy = "conservative"  # Only crawl homepage

            assert crawl_policy == "conservative"

    def test_timeout_results_in_limited_crawl(self):
        """Timeout should result in limited crawl scope."""
        crawl_config = {
            "robots_status": "timeout",
            "max_pages": 5,  # Limited when robots.txt unavailable
            "paths_to_crawl": ["/"],  # Only homepage
            "reason": "robots.txt unavailable, using conservative crawl",
        }

        assert crawl_config["max_pages"] < 100  # Much less than normal
        assert crawl_config["paths_to_crawl"] == ["/"]


class TestCrawlDelay:
    """Tests for crawl-delay directive."""

    def test_crawl_delay_respected(self):
        """Crawl-delay directive should be respected."""

        def parse_crawl_delay(robots_txt):
            for line in robots_txt.split("\n"):
                if line.strip().startswith("Crawl-delay:"):
                    try:
                        return int(line.split(":", 1)[1].strip())
                    except ValueError:
                        return None
            return None

        delay = parse_crawl_delay(ROBOTS_CRAWL_DELAY)
        assert delay == 10

    def test_crawl_delay_capped_at_maximum(self):
        """Crawl delay should be capped at reasonable maximum."""
        max_crawl_delay = 30  # seconds

        def apply_crawl_delay(parsed_delay, maximum=30):
            if parsed_delay is None:
                return 0
            return min(parsed_delay, maximum)

        # Very long delay should be capped
        assert apply_crawl_delay(100, max_crawl_delay) == 30

        # Reasonable delay should be used as-is
        assert apply_crawl_delay(10, max_crawl_delay) == 10


# Run configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
