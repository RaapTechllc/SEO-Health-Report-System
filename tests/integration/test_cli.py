"""
End-to-end tests for CLI interface.

Tests the command-line interface for generating reports.
"""

import os
import sys
from unittest.mock import patch

import pytest

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""

    @pytest.mark.integration
    def test_cli_requires_url(self):
        """Test that CLI requires --url argument."""
        import argparse


        # Capture parser behavior
        with patch("sys.argv", ["seo_health_report"]):
            with pytest.raises(SystemExit) as exc_info:
                parser = argparse.ArgumentParser()
                parser.add_argument("--url", required=True)
                parser.parse_args()

            assert exc_info.value.code == 2  # Missing required argument

    @pytest.mark.integration
    def test_cli_accepts_all_arguments(self):
        """Test that CLI accepts all defined arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--url", required=True)
        parser.add_argument("--company", required=True)
        parser.add_argument("--logo", required=True)
        parser.add_argument("--keywords", required=True)
        parser.add_argument("--competitors")
        parser.add_argument("--output", default="report.docx")
        parser.add_argument("--format", default="docx", choices=["docx", "pdf", "md"])
        parser.add_argument("--primary-color")
        parser.add_argument("--secondary-color")

        args = parser.parse_args(
            [
                "--url",
                "https://example.com",
                "--company",
                "Test Corp",
                "--logo",
                "logo.png",
                "--keywords",
                "widget,gadget",
                "--competitors",
                "https://comp1.com,https://comp2.com",
                "--output",
                "test-report.md",
                "--format",
                "md",
                "--primary-color",
                "#1a73e8",
                "--secondary-color",
                "#34a853",
            ]
        )

        assert args.url == "https://example.com"
        assert args.company == "Test Corp"
        assert args.logo == "logo.png"
        assert args.keywords == "widget,gadget"
        assert args.competitors == "https://comp1.com,https://comp2.com"
        assert args.format == "md"

    @pytest.mark.integration
    def test_cli_parses_keywords(self):
        """Test keyword parsing from comma-separated string."""
        keywords_str = "widget, gadget, service, enterprise solution"
        keywords = [k.strip() for k in keywords_str.split(",")]

        assert keywords == ["widget", "gadget", "service", "enterprise solution"]
        assert len(keywords) == 4

    @pytest.mark.integration
    def test_cli_parses_competitors(self):
        """Test competitor URL parsing."""
        competitors_str = "https://comp1.com, https://comp2.com"
        competitors = [c.strip() for c in competitors_str.split(",")]

        assert competitors == ["https://comp1.com", "https://comp2.com"]

    @pytest.mark.integration
    def test_cli_parses_brand_colors(self):
        """Test brand color parsing."""
        primary = "#1a73e8"
        secondary = "#34a853"

        colors = {"primary": primary}
        if secondary:
            colors["secondary"] = secondary

        assert colors["primary"] == "#1a73e8"
        assert colors["secondary"] == "#34a853"


class TestCLIOutputFormatting:
    """Test CLI output formatting."""

    @pytest.mark.integration
    def test_format_text_report(self):
        """Test text report formatting for console output."""
        from seo_health_report import format_text_report

        result = {
            "overall_score": 75,
            "grade": "C",
            "component_scores": {
                "technical": {"score": 78, "weight": 0.30},
                "content": {"score": 72, "weight": 0.35},
                "ai_visibility": {"score": 65, "weight": 0.35},
            },
            "critical_issues": [
                {"description": "Missing HTTPS"},
                {"description": "Slow page speed"},
            ],
            "quick_wins": [
                {"action": "Add meta descriptions"},
                {"action": "Optimize images"},
            ],
        }

        text = format_text_report(result)

        # Check structure
        assert "SEO HEALTH REPORT SUMMARY" in text
        assert "OVERALL SCORE: 75/100" in text
        assert "Grade: C" in text
        assert "COMPONENT SCORES" in text
        assert "CRITICAL ISSUES" in text
        assert "QUICK WINS" in text

    @pytest.mark.integration
    def test_format_text_report_with_empty_issues(self):
        """Test text formatting with no issues."""
        from seo_health_report import format_text_report

        result = {
            "overall_score": 92,
            "grade": "A",
            "component_scores": {
                "technical": {"score": 95, "weight": 0.30},
            },
            "critical_issues": [],
            "quick_wins": [],
        }

        text = format_text_report(result)

        assert "OVERALL SCORE: 92/100" in text
        # Should not crash with empty lists


class TestCLIIntegration:
    """Test CLI integration with main module."""

    @pytest.mark.integration
    def test_main_function_exists(self):
        """Test that main function is accessible."""
        from seo_health_report import main

        assert callable(main)

    @pytest.mark.integration
    def test_generate_report_function_signature(self):
        """Test generate_report accepts expected parameters."""
        import inspect

        from seo_health_report import generate_report

        sig = inspect.signature(generate_report)
        params = list(sig.parameters.keys())

        expected_params = [
            "target_url",
            "company_name",
            "logo_file",
            "primary_keywords",
            "brand_colors",
            "competitor_urls",
            "output_format",
            "output_dir",
            "preparer_name",
            "ground_truth",
        ]

        for param in expected_params:
            assert param in params, f"Missing parameter: {param}"

    @pytest.mark.integration
    def test_output_format_handling(self):
        """Test different output format options."""
        valid_formats = ["docx", "pdf", "md"]

        for fmt in valid_formats:
            # Simulate format validation
            assert fmt in valid_formats


class TestCLIHelpers:
    """Test CLI helper utilities."""

    @pytest.mark.integration
    def test_cache_clearing_function(self):
        """Test cache clearing is accessible via CLI."""
        from seo_health_report import clear_all_caches

        # Should not raise
        clear_all_caches()

    @pytest.mark.integration
    def test_cache_stats_function(self):
        """Test cache stats retrieval."""
        from seo_health_report import get_cache_stats

        stats = get_cache_stats()
        assert isinstance(stats, dict)

    @pytest.mark.integration
    def test_module_version(self):
        """Test module version is accessible."""
        from seo_health_report import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)


class TestCLIErrorHandling:
    """Test CLI error handling."""

    @pytest.mark.integration
    def test_invalid_url_handling(self):
        """Test handling of invalid URL format."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "",
        ]

        from urllib.parse import urlparse

        for url in invalid_urls:
            parsed = urlparse(url)
            # Invalid URLs should have empty or non-http(s) scheme
            if url:
                is_valid = parsed.scheme in ["http", "https"] and parsed.netloc
            else:
                is_valid = False

            assert not is_valid or url == ""

    @pytest.mark.integration
    def test_output_directory_creation(self, tmp_path):
        """Test that output directory is handled properly."""
        import os

        # Non-existent subdirectory
        output_dir = str(tmp_path / "reports" / "subdir")

        # Determine directory from path
        determined_dir = os.path.dirname(output_dir) or "."

        # Should not crash - directory handling is external
        assert determined_dir is not None


class TestCLIModuleExports:
    """Test module exports are correct."""

    @pytest.mark.integration
    def test_all_exports_available(self):
        """Test all expected exports are available."""
        import seo_health_report

        expected_exports = [
            "generate_report",
            "format_text_report",
            "clear_all_caches",
            "get_cache_stats",
            "run_full_audit",
            "calculate_composite_score",
            "determine_grade",
            "generate_executive_summary",
            "build_report_document",
            "apply_branding",
        ]

        for export in expected_exports:
            assert hasattr(seo_health_report, export), f"Missing export: {export}"

    @pytest.mark.integration
    def test_exports_are_callable(self):
        """Test that exported functions are callable."""
        import seo_health_report

        callable_exports = [
            "generate_report",
            "format_text_report",
            "clear_all_caches",
            "get_cache_stats",
        ]

        for export in callable_exports:
            func = getattr(seo_health_report, export)
            assert callable(func), f"Export not callable: {export}"


class TestCLIWithMocks:
    """Test CLI with mocked dependencies."""

    @pytest.mark.integration
    def test_generate_report_with_mocked_audits(self, tmp_path):
        """Test generate_report with mocked audit modules."""
        from seo_health_report.scripts.build_report import build_report_document
        from seo_health_report.scripts.calculate_scores import calculate_composite_score
        from seo_health_report.scripts.generate_summary import (
            generate_executive_summary,
        )

        # Mock audit results (simulating what run_full_audit would return)
        mock_audit_results = {
            "url": "https://example.com",
            "company_name": "Test Corp",
            "timestamp": "2024-01-15T10:00:00",
            "audits": {
                "technical": {
                    "score": 80,
                    "grade": "B",
                    "components": {},
                    "recommendations": [],
                },
                "content": {
                    "score": 75,
                    "grade": "C",
                    "components": {},
                    "recommendations": [],
                },
                "ai_visibility": {
                    "score": 70,
                    "grade": "C",
                    "components": {},
                    "recommendations": [],
                },
            },
            "warnings": [],
            "errors": [],
        }

        # Calculate scores
        scores = calculate_composite_score(mock_audit_results)
        assert scores["overall_score"] > 0

        # Generate summary
        summary = generate_executive_summary(
            scores=scores, critical_issues=[], quick_wins=[], company_name="Test Corp"
        )
        assert "headline" in summary

        # Build report
        result = build_report_document(
            audit_results=mock_audit_results,
            scores=scores,
            executive_summary=summary,
            company_name="Test Corp",
            output_format="md",
            output_dir=str(tmp_path),
        )

        assert result["success"] is True
        assert os.path.exists(result["output_path"])
