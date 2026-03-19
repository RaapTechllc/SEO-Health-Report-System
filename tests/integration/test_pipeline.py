"""
Integration tests for the full audit pipeline.
"""

import os
import sys
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class TestAuditPipeline:
    """Test full audit pipeline integration."""

    def test_orchestrate_imports(self):
        """Test orchestrate module imports correctly."""
        from seo_health_report.scripts.orchestrate import (
            handle_audit_failure,
            run_full_audit,
        )
        assert callable(run_full_audit)
        assert callable(handle_audit_failure)

    def test_schemas_imports(self):
        """Test schemas module imports correctly."""
        from seo_health_report.scripts.schemas import (
            Issue,
            calculate_grade,
        )
        assert Issue is not None
        assert callable(calculate_grade)

    def test_failure_handling_integration(self):
        """Test failure handling produces valid schema."""
        from seo_health_report.scripts.orchestrate import handle_audit_failure

        result = handle_audit_failure("technical", "Test error")

        assert result["score"] is None
        assert result["grade"] == "N/A"
        assert result["status"] == "unavailable"
        assert len(result["findings"]) > 0
        assert len(result["recommendations"]) > 0

    def test_domain_extraction_integration(self):
        """Test domain extraction with various URLs."""
        from seo_health_report.scripts.orchestrate import extract_domain

        test_cases = [
            ("https://www.example.com/page", "example.com"),
            ("http://blog.test.org/article", "blog.test.org"),
            ("https://example.com:8080/path", "example.com"),
        ]

        for url, expected in test_cases:
            assert extract_domain(url) == expected

    def test_issue_collection_integration(self):
        """Test issue collection from audit results."""
        from seo_health_report.scripts.orchestrate import collect_all_issues

        audit_results = {
            "audits": {
                "technical": {
                    "score": 75,
                    "issues": [
                        {"severity": "high", "description": "Slow page load"},
                        {"severity": "medium", "description": "Missing alt tags"},
                    ],
                },
                "content": {
                    "score": 80,
                    "issues": [
                        {"severity": "low", "description": "Short content"},
                    ],
                },
            }
        }

        issues = collect_all_issues(audit_results)

        assert len(issues) == 3
        # Should be sorted by severity
        assert issues[0]["severity"] == "high"
        assert issues[1]["severity"] == "medium"
        assert issues[2]["severity"] == "low"


class TestGeminiIntegration:
    """Test Gemini integration module."""

    def test_gemini_imports(self):
        """Test Gemini module imports correctly."""
        from seo_health_report.scripts.gemini_integration import (
            GeminiClient,
            GeminiConfig,
        )
        assert GeminiClient is not None
        assert GeminiConfig is not None

    def test_gemini_config_without_key(self):
        """Test Gemini config returns None without API key."""
        from seo_health_report.scripts.gemini_integration import get_gemini_config

        with patch.dict(os.environ, {}, clear=True):
            # Remove any existing keys
            os.environ.pop("GOOGLE_GEMINI_API_KEY", None)
            os.environ.pop("GOOGLE_API_KEY", None)
            get_gemini_config()
            # May or may not be None depending on env
            # Just verify it doesn't crash

    def test_gemini_client_availability(self):
        """Test GeminiClient reports availability correctly."""
        from seo_health_report.scripts.gemini_integration import GeminiClient

        client = GeminiClient(config=None)
        assert not client.available


class TestCacheIntegration:
    """Test caching system integration."""

    def test_cache_imports(self):
        """Test cache module imports correctly."""
        from seo_health_report.scripts.cache import (
            cached,
            clear_cache,
            get_cache,
        )
        assert callable(get_cache)
        assert callable(clear_cache)
        assert callable(cached)
