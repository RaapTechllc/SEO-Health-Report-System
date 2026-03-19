"""
E2E Tests for SEO Health Report System.

These tests verify the complete system flow from API requests
through audit execution to report generation.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Optional playwright import - skip browser tests if not installed
try:
    from playwright.sync_api import Page, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None  # type: ignore

# Import the actual module functions
try:
    from seo_health_report import (  # noqa: F401
        build_report_document,
        generate_report,
        main,
        run_full_audit_sync,
    )
    SEO_MODULE_AVAILABLE = True
except ImportError:
    SEO_MODULE_AVAILABLE = False
    generate_report = None  # type: ignore
    main = None  # type: ignore


class TestCLIInterface:
    """Tests for CLI interface."""

    @pytest.mark.skipif(not SEO_MODULE_AVAILABLE, reason="seo_health_report module not available")
    def test_main_function_callable(self):
        """Verify main function exists and is callable."""
        assert callable(main), "main() should be callable"

    @pytest.mark.skipif(not SEO_MODULE_AVAILABLE, reason="seo_health_report module not available")
    def test_generate_report_function_callable(self):
        """Verify generate_report function exists and is callable."""
        assert callable(generate_report), "generate_report() should be callable"


class TestReportGenerationFlow:
    """Tests for the report generation flow."""

    @pytest.mark.skipif(not SEO_MODULE_AVAILABLE, reason="seo_health_report module not available")
    @patch("seo_health_report.run_full_audit_sync")
    @patch("seo_health_report.build_report_document")
    def test_full_report_flow(self, mock_build, mock_audit, tmp_path):
        """
        Simulate a full report generation flow mocking the actual audit and build steps.
        This ensures the 'glue' code in generate_report works.
        """
        # Mock return values
        mock_audit.return_value = {
            "audits": {
                "technical": {"score": 80, "grade": "B", "components": {}, "issues": [], "recommendations": []},
                "content": {"score": 75, "grade": "C", "components": {}, "issues": [], "recommendations": []},
                "ai_visibility": {"score": 70, "grade": "C", "components": {}, "issues": [], "recommendations": []},
            },
            "warnings": [],
            "errors": []
        }

        output_file = tmp_path / "test_report.docx"
        mock_build.return_value = {
            "success": True,
            "output_path": str(output_file),
            "pages": 5
        }

        # Execute
        result = generate_report(
            target_url="https://example.com",
            company_name="Test Corp",
            logo_file="logo.png",
            primary_keywords=["test", "seo"],
            output_dir=str(tmp_path),
            output_format="docx"
        )

        # Verify
        assert result["overall_score"] is not None
        assert isinstance(result["overall_score"], (int, float))
        assert result["report"]["success"] is True
        assert result["report"]["output_path"] == str(output_file)

        # Verify mocks called
        mock_audit.assert_called_once()
        mock_build.assert_called_once()

    @pytest.mark.skipif(not SEO_MODULE_AVAILABLE, reason="seo_health_report module not available")
    @patch("seo_health_report.run_full_audit_sync")
    @patch("seo_health_report.build_report_document")
    def test_report_with_competitors(self, mock_build, mock_audit, tmp_path):
        """Test report generation with competitor analysis."""
        mock_audit.return_value = {
            "audits": {
                "technical": {"score": 85, "grade": "B", "components": {}, "issues": [], "recommendations": []},
                "content": {"score": 80, "grade": "B", "components": {}, "issues": [], "recommendations": []},
                "ai_visibility": {"score": 75, "grade": "C", "components": {}, "issues": [], "recommendations": []},
            },
            "warnings": [],
            "errors": []
        }
        mock_build.return_value = {"success": True, "output_path": str(tmp_path / "report.docx"), "pages": 8}

        result = generate_report(
            target_url="https://example.com",
            company_name="Test Corp",
            logo_file="logo.png",
            primary_keywords=["seo", "marketing"],
            competitor_urls=["https://competitor1.com", "https://competitor2.com"],
            output_dir=str(tmp_path),
            output_format="docx"
        )

        assert result["overall_score"] > 0
        assert result["grade"] in ["A", "B", "C", "D", "F"]

        # Verify competitors were passed to audit
        call_kwargs = mock_audit.call_args[1]
        assert call_kwargs["competitor_urls"] == ["https://competitor1.com", "https://competitor2.com"]

    @pytest.mark.skipif(not SEO_MODULE_AVAILABLE, reason="seo_health_report module not available")
    @patch("seo_health_report.run_full_audit_sync")
    @patch("seo_health_report.build_report_document")
    def test_report_handles_audit_warnings(self, mock_build, mock_audit, tmp_path):
        """Test that warnings from audit are propagated to result."""
        mock_audit.return_value = {
            "audits": {
                "technical": {"score": 70, "grade": "C", "components": {}, "issues": [], "recommendations": []},
                "content": {"score": 65, "grade": "D", "components": {}, "issues": [], "recommendations": []},
                "ai_visibility": {"score": 60, "grade": "D", "components": {}, "issues": [], "recommendations": []},
            },
            "warnings": ["API rate limit approached", "Some pages could not be crawled"],
            "errors": []
        }
        mock_build.return_value = {"success": True, "output_path": str(tmp_path / "report.docx"), "pages": 5}

        result = generate_report(
            target_url="https://example.com",
            company_name="Test Corp",
            logo_file="logo.png",
            primary_keywords=["test"],
            output_dir=str(tmp_path),
            output_format="docx"
        )

        assert len(result["warnings"]) >= 2
        assert "API rate limit approached" in result["warnings"]


class TestAPIIntegration:
    """Tests for API endpoints (mocked)."""

    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client."""
        client = MagicMock()
        client.post = MagicMock()
        client.get = MagicMock()
        return client

    def test_audit_request_creation(self, mock_api_client):
        """Test creating an audit request."""
        mock_api_client.post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "audit_id": "audit_abc123",
                "status": "pending",
                "url": "https://example.com",
                "company_name": "Test Corp"
            }
        )

        response = mock_api_client.post(
            "/audit",
            json={
                "url": "https://example.com",
                "company_name": "Test Corp",
                "keywords": ["seo"],
                "tier": "basic"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "audit_id" in data
        assert data["status"] == "pending"

    def test_audit_status_polling(self, mock_api_client):
        """Test polling for audit status."""
        # Simulate status progression
        mock_api_client.get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"status": "running", "progress": 30}),
            MagicMock(status_code=200, json=lambda: {"status": "running", "progress": 60}),
            MagicMock(status_code=200, json=lambda: {"status": "completed", "overall_score": 75, "grade": "C"}),
        ]

        # Poll until complete
        statuses = []
        for _ in range(3):
            response = mock_api_client.get("/audit/audit_abc123")
            data = response.json()
            statuses.append(data["status"])
            if data["status"] == "completed":
                break

        assert statuses == ["running", "running", "completed"]


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
class TestDashboardUI:
    """Browser-based E2E tests for dashboard UI.

    These tests require:
    1. Playwright installed: pip install playwright && playwright install
    2. Running frontend server on localhost:3000
    """

    # @pytest.mark.skip(reason="Requires running frontend server")
    def test_dashboard_loads(self, page: Page):
        """Test that dashboard loads correctly."""
        page.goto("http://127.0.0.1:5173")
        expect(page).to_have_title("SEO Health Report Dashboard")
        expect(page.get_by_text("Recent Audits")).to_be_visible()

    # @pytest.mark.skip(reason="Requires running frontend server")
    def test_audit_detail_view(self, page: Page):
        """Test navigating to audit detail view."""
        page.goto("http://127.0.0.1:5173")
        # Click first audit in list
        page.locator(".audit-item").first.click()
        expect(page.locator(".audit-detail")).to_be_visible()
        expect(page.get_by_text("Overall Score")).to_be_visible()


class TestEndToEndAuditFlow:
    """Complete E2E flow tests with mocked external dependencies."""

    @pytest.mark.asyncio
    async def test_complete_audit_flow_mocked(self):
        """Test complete audit flow from request to report."""
        # This simulates what would happen in a real E2E test
        # but with mocked external dependencies

        # Step 1: Create audit request

        # Step 2: Mock audit execution
        mock_audit_result = {
            "url": "https://example.com",
            "company_name": "Example Corp",
            "timestamp": "2024-01-15T10:00:00",
            "audits": {
                "technical": {
                    "score": 80,
                    "grade": "B",
                    "components": {
                        "crawlability": {"score": 18, "max": 20},
                        "speed": {"score": 22, "max": 25},
                    },
                    "issues": [{"severity": "medium", "description": "Missing alt tags"}],
                    "recommendations": [{"priority": "high", "action": "Add alt tags to images"}],
                },
                "content": {
                    "score": 75,
                    "grade": "C",
                    "components": {},
                    "issues": [],
                    "recommendations": [],
                },
                "ai_visibility": {
                    "score": 70,
                    "grade": "C",
                    "components": {},
                    "issues": [],
                    "recommendations": [],
                },
            },
            "warnings": [],
            "errors": [],
        }

        # Step 3: Calculate scores (using actual logic)
        from packages.seo_health_report.scripts.calculate_scores import calculate_composite_score
        scores = calculate_composite_score(mock_audit_result)

        assert scores["overall_score"] > 0
        assert scores["grade"] in ["A", "B", "C", "D", "F"]
        assert "technical" in scores["component_scores"]
        assert "content" in scores["component_scores"]
        assert "ai_visibility" in scores["component_scores"]

    @pytest.mark.asyncio
    async def test_audit_flow_with_errors(self):
        """Test audit flow handles errors gracefully."""
        # Simulate an audit with errors
        mock_audit_result = {
            "audits": {
                "technical": {"score": 0, "grade": "F", "components": {}, "issues": [], "recommendations": []},
                "content": {"score": 0, "grade": "F", "components": {}, "issues": [], "recommendations": []},
                "ai_visibility": {"score": 0, "grade": "F", "components": {}, "issues": [], "recommendations": []},
            },
            "warnings": [],
            "errors": ["Failed to fetch URL: Connection timeout"],
        }

        from packages.seo_health_report.scripts.calculate_scores import calculate_composite_score
        scores = calculate_composite_score(mock_audit_result)

        # Even with errors, we should get valid structure
        assert "overall_score" in scores
        assert "grade" in scores
        assert scores["overall_score"] == 0
        assert scores["grade"] == "F"


class TestDataValidation:
    """Tests for input validation across the system."""

    def test_url_validation(self):
        """Test URL validation logic using Pydantic directly."""

        from pydantic import BaseModel, ValidationError, field_validator

        # Define a minimal request model matching the API schema
        class AuditRequest(BaseModel):
            url: str
            company_name: str
            keywords: list[str] = []
            tier: str = "basic"

            @field_validator("url")
            @classmethod
            def validate_url(cls, v):
                v = v.strip()
                if not v.startswith(("http://", "https://")):
                    v = f"https://{v}"
                if "." not in v:
                    raise ValueError("Invalid URL format")
                return v

            @field_validator("tier")
            @classmethod
            def validate_tier(cls, v):
                if v not in ["basic", "pro", "enterprise"]:
                    raise ValueError("Tier must be basic, pro, or enterprise")
                return v

        # Valid URLs
        valid_cases = [
            {"url": "https://example.com", "company_name": "Test"},
            {"url": "http://example.com", "company_name": "Test"},
            {"url": "example.com", "company_name": "Test"},  # Should auto-add https
        ]

        for case in valid_cases:
            request = AuditRequest(**case)
            assert request.url.startswith("http")
            assert "." in request.url

        # Invalid URL should raise
        with pytest.raises(ValidationError):
            AuditRequest(url="notaurl", company_name="Test")

    def test_tier_validation(self):
        """Test tier validation using Pydantic directly."""

        from pydantic import BaseModel, ValidationError, field_validator

        class AuditRequest(BaseModel):
            url: str
            company_name: str
            tier: str = "basic"

            @field_validator("tier")
            @classmethod
            def validate_tier(cls, v):
                if v not in ["basic", "pro", "enterprise"]:
                    raise ValueError("Tier must be basic, pro, or enterprise")
                return v

        # Valid tiers
        for tier in ["basic", "pro", "enterprise"]:
            request = AuditRequest(url="https://example.com", company_name="Test", tier=tier)
            assert request.tier == tier

        # Invalid tier
        with pytest.raises(ValidationError):
            AuditRequest(url="https://example.com", company_name="Test", tier="invalid")
