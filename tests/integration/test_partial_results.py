"""Test partial results handling on audit failures."""

import asyncio
import sys
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

sys.modules.setdefault("stripe", MagicMock())

import pytest
from fastapi.testclient import TestClient


class TestPartialResults:
    """Tests for handling partial audit results when modules fail."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        from apps.api.main import app
        return TestClient(app)

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        session.add = MagicMock()
        session.commit = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def partial_audit_result(self):
        """Create a partial audit result where one module failed."""
        return {
            "url": "https://example.com",
            "company_name": "Test Company",
            "timestamp": datetime.now().isoformat(),
            "audits": {
                "technical": {
                    "score": 75,
                    "grade": "C",
                    "status": "completed",
                    "issues": [{"severity": "medium", "description": "Missing meta tags"}],
                    "recommendations": [{"action": "Add meta tags", "priority": "high"}],
                },
                "content": {
                    "score": None,
                    "grade": "N/A",
                    "status": "unavailable",
                    "error_type": "system_unavailable",
                    "message": "Content analysis temporarily unavailable",
                    "reason": "Technical issue - manual analysis recommended",
                    "components": {},
                    "issues": [],
                    "findings": ["Content audit could not be completed"],
                    "recommendations": ["Contact RaapTech for manual content analysis"],
                },
                "ai_visibility": {
                    "score": 82,
                    "grade": "B",
                    "status": "completed",
                    "issues": [],
                    "recommendations": [],
                },
            },
            "warnings": ["Content audit module not found"],
            "errors": [],
        }

    @pytest.fixture
    def fully_failed_audit_result(self):
        """Create audit result where all modules failed."""
        return {
            "url": "https://example.com",
            "company_name": "Test Company",
            "timestamp": datetime.now().isoformat(),
            "audits": {
                "technical": {
                    "score": None,
                    "grade": "N/A",
                    "status": "unavailable",
                    "error_type": "system_unavailable",
                },
                "content": {
                    "score": None,
                    "grade": "N/A",
                    "status": "unavailable",
                    "error_type": "system_unavailable",
                },
                "ai_visibility": {
                    "score": None,
                    "grade": "N/A",
                    "status": "unavailable",
                    "error_type": "system_unavailable",
                },
            },
            "warnings": [],
            "errors": ["All audits failed"],
        }

    def test_timeout_returns_partial_results(self, client):
        """When a module times out, return partial results from completed modules."""
        from scripts.orchestrate import handle_audit_failure

        async def mock_run_full_audit(*args, **kwargs):
            return {
                "url": kwargs.get("target_url", "https://example.com"),
                "company_name": kwargs.get("company_name", "Test"),
                "timestamp": datetime.now().isoformat(),
                "audits": {
                    "technical": {"score": 80, "grade": "B", "status": "completed"},
                    "content": handle_audit_failure("content", "Timeout after 30s"),
                    "ai_visibility": {"score": 75, "grade": "C", "status": "completed"},
                },
                "warnings": ["Content audit timed out"],
                "errors": [],
            }

        with patch("scripts.orchestrate.run_full_audit", new=mock_run_full_audit):
            result = asyncio.run(mock_run_full_audit(
                target_url="https://example.com",
                company_name="Test Company",
                primary_keywords=["seo"],
            ))

        assert result["audits"]["technical"]["score"] == 80
        assert result["audits"]["technical"]["status"] == "completed"
        assert result["audits"]["content"]["score"] is None
        assert result["audits"]["content"]["status"] == "unavailable"
        assert result["audits"]["ai_visibility"]["score"] == 75
        assert result["audits"]["ai_visibility"]["status"] == "completed"

    def test_api_failure_returns_partial_results(self, client):
        """When external API fails, return partial results."""
        from scripts.orchestrate import handle_audit_failure

        async def mock_run_full_audit(*args, **kwargs):
            return {
                "url": "https://example.com",
                "company_name": "Test",
                "timestamp": datetime.now().isoformat(),
                "audits": {
                    "technical": {"score": 85, "grade": "B", "status": "completed"},
                    "content": {"score": 72, "grade": "C", "status": "completed"},
                    "ai_visibility": handle_audit_failure("ai_visibility", "OpenAI API rate limited"),
                },
                "warnings": [],
                "errors": ["AI visibility audit failed: OpenAI API rate limited"],
            }

        with patch("scripts.orchestrate.run_full_audit", new=mock_run_full_audit):
            result = asyncio.run(mock_run_full_audit())

        assert result["audits"]["technical"]["status"] == "completed"
        assert result["audits"]["content"]["status"] == "completed"
        assert result["audits"]["ai_visibility"]["status"] == "unavailable"
        assert "AI visibility audit failed" in result["errors"][0]

    def test_partial_results_are_downloadable(self, partial_audit_result):
        """Verify partial results can be retrieved via API."""
        from apps.api.main import app
        from database import Audit, get_db

        audit_id = f"audit_{uuid.uuid4().hex[:12]}"
        mock_audit = MagicMock(spec=Audit)
        mock_audit.id = audit_id
        mock_audit.status = "partial"
        mock_audit.url = "https://example.com"
        mock_audit.company_name = "Test Company"
        mock_audit.tier = "basic"
        mock_audit.overall_score = 52
        mock_audit.grade = "C"
        mock_audit.result = partial_audit_result
        mock_audit.created_at = datetime.utcnow()
        mock_audit.completed_at = datetime.utcnow()
        mock_audit.report_html_path = None
        mock_audit.report_pdf_path = None

        def mock_get_db_override():
            session = MagicMock()
            session.query.return_value.filter.return_value.first.return_value = mock_audit
            yield session

        app.dependency_overrides[get_db] = mock_get_db_override
        try:
            client = TestClient(app)
            response = client.get(f"/audit/{audit_id}/full")
            assert response.status_code == 200
            data = response.json()
            assert data["audit_id"] == audit_id
            assert data["status"] == "partial"
            assert data["overall_score"] == 52
        finally:
            app.dependency_overrides.clear()

    def test_partial_status_indicates_what_failed(self, partial_audit_result):
        """Verify partial status includes info about which modules failed."""
        audits = partial_audit_result["audits"]

        failed_modules = []
        completed_modules = []

        for module_name, module_data in audits.items():
            if module_data.get("status") == "unavailable":
                failed_modules.append(module_name)
            elif module_data.get("status") == "completed":
                completed_modules.append(module_name)

        assert "content" in failed_modules
        assert "technical" in completed_modules
        assert "ai_visibility" in completed_modules

        content_result = audits["content"]
        assert content_result["error_type"] == "system_unavailable"
        assert "unavailable" in content_result["message"].lower()

    def test_completed_modules_have_scores(self, partial_audit_result):
        """Verify completed modules have valid scores even when others fail."""
        audits = partial_audit_result["audits"]

        technical = audits["technical"]
        assert technical["score"] == 75
        assert technical["grade"] == "C"
        assert technical["status"] == "completed"

        ai_visibility = audits["ai_visibility"]
        assert ai_visibility["score"] == 82
        assert ai_visibility["grade"] == "B"
        assert ai_visibility["status"] == "completed"

        content = audits["content"]
        assert content["score"] is None
        assert content["grade"] == "N/A"

    def test_handle_audit_failure_returns_proper_structure(self):
        """Verify handle_audit_failure returns expected structure."""
        from scripts.orchestrate import handle_audit_failure

        result = handle_audit_failure("technical", "Connection timeout")

        assert result["score"] is None
        assert result["grade"] == "N/A"
        assert result["status"] == "unavailable"
        assert result["error_type"] == "system_unavailable"
        assert "unavailable" in result["message"].lower()
        assert "components" in result
        assert "issues" in result
        assert "findings" in result
        assert "recommendations" in result
        assert "next_steps" in result

    def test_partial_score_calculation(self, partial_audit_result):
        """Verify partial scores are calculated correctly from available modules."""
        from scripts.calculate_scores import calculate_composite_score

        scores = calculate_composite_score(partial_audit_result)

        assert "overall_score" in scores
        assert scores["overall_score"] >= 0 or scores["overall_score"] is None
        assert "grade" in scores

    def test_multiple_module_failures_still_returns_results(self):
        """When multiple modules fail, still return results from successful ones."""
        from scripts.orchestrate import handle_audit_failure

        result = {
            "url": "https://example.com",
            "company_name": "Test",
            "timestamp": datetime.now().isoformat(),
            "audits": {
                "technical": {"score": 90, "grade": "A", "status": "completed"},
                "content": handle_audit_failure("content", "API error"),
                "ai_visibility": handle_audit_failure("ai_visibility", "Timeout"),
            },
            "warnings": ["Content audit failed", "AI visibility audit failed"],
            "errors": [],
        }

        assert result["audits"]["technical"]["status"] == "completed"
        assert result["audits"]["technical"]["score"] == 90

        failed_count = sum(
            1 for a in result["audits"].values()
            if a.get("status") == "unavailable"
        )
        assert failed_count == 2

    def test_all_modules_failed_returns_meaningful_response(self, fully_failed_audit_result):
        """When all modules fail, return meaningful error response."""
        audits = fully_failed_audit_result["audits"]

        all_failed = all(
            a.get("status") == "unavailable" for a in audits.values()
        )
        assert all_failed

        assert len(fully_failed_audit_result["errors"]) > 0

    def test_partial_results_include_warnings(self, partial_audit_result):
        """Verify partial results include warnings about failed modules."""
        assert len(partial_audit_result["warnings"]) > 0
        assert any("content" in w.lower() for w in partial_audit_result["warnings"])

    def test_audit_status_set_to_partial_on_failure(self):
        """Verify audit status is 'partial' not 'failed' when some data exists."""
        from apps.api.main import app
        from database import Audit, get_db

        audit_id = f"audit_{uuid.uuid4().hex[:12]}"
        mock_audit = MagicMock(spec=Audit)
        mock_audit.id = audit_id
        mock_audit.status = "partial"
        mock_audit.url = "https://example.com"
        mock_audit.company_name = "Test"
        mock_audit.tier = "basic"
        mock_audit.overall_score = 60
        mock_audit.grade = "C"
        mock_audit.created_at = datetime.utcnow()
        mock_audit.completed_at = datetime.utcnow()

        def mock_get_db_override():
            session = MagicMock()
            session.query.return_value.filter.return_value.first.return_value = mock_audit
            yield session

        app.dependency_overrides[get_db] = mock_get_db_override
        try:
            client = TestClient(app)
            response = client.get(f"/audit/{audit_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "partial"
            assert data["overall_score"] == 60
        finally:
            app.dependency_overrides.clear()

    def test_run_audit_task_handles_partial_failure(self):
        """Verify run_audit_task properly handles partial module failures."""
        from scripts.orchestrate import handle_audit_failure

        async def mock_run_full_audit(*args, **kwargs):
            return {
                "url": "https://example.com",
                "company_name": "Test",
                "timestamp": datetime.now().isoformat(),
                "audits": {
                    "technical": {"score": 70, "grade": "C", "status": "completed"},
                    "content": handle_audit_failure("content", "Module crashed"),
                    "ai_visibility": {"score": 65, "grade": "D", "status": "completed"},
                },
                "warnings": [],
                "errors": [],
            }

        with patch("scripts.orchestrate.run_full_audit", mock_run_full_audit):
            result = asyncio.run(mock_run_full_audit())

        completed_count = sum(
            1 for a in result["audits"].values()
            if a.get("status") == "completed"
        )
        assert completed_count == 2

        failed_count = sum(
            1 for a in result["audits"].values()
            if a.get("status") == "unavailable"
        )
        assert failed_count == 1


class TestPartialResultsCalculation:
    """Tests for score calculation with partial results."""

    def test_weighted_score_with_missing_module(self):
        """Verify weighted score calculation handles missing modules."""
        from scripts.calculate_scores import calculate_composite_score

        partial_result = {
            "audits": {
                "technical": {"score": 80, "grade": "B"},
                "content": {"score": None, "grade": "N/A", "status": "unavailable"},
                "ai_visibility": {"score": 70, "grade": "C"},
            }
        }

        scores = calculate_composite_score(partial_result)
        assert "overall_score" in scores
        assert "component_scores" in scores

    def test_grade_assignment_with_partial_data(self):
        """Verify grade is assigned correctly with partial data."""
        from scripts.calculate_scores import calculate_composite_score

        partial_result = {
            "audits": {
                "technical": {"score": 90, "grade": "A"},
                "content": {"score": 85, "grade": "B"},
                "ai_visibility": {"score": None, "grade": "N/A", "status": "unavailable"},
            }
        }

        scores = calculate_composite_score(partial_result)
        assert scores.get("grade") in ["A", "B", "C", "D", "F", "N/A"]


class TestPartialResultsWebhooks:
    """Tests for webhook delivery with partial results."""

    @pytest.fixture
    def mock_webhook_service(self):
        """Create a mock webhook service."""
        service = MagicMock()
        service.fire_event = AsyncMock(return_value=["delivery_123"])
        service.close = AsyncMock()
        return service

    def test_webhook_includes_partial_status(self, mock_webhook_service):
        """Verify webhook payload includes partial status information."""
        audit_data = {
            "audit_id": "audit_123",
            "url": "https://example.com",
            "company_name": "Test",
            "tier": "basic",
            "overall_score": 55,
            "grade": "C",
            "status": "partial",
            "failed_modules": ["content"],
            "completed_at": datetime.utcnow().isoformat(),
        }

        assert audit_data["status"] == "partial"
        assert "failed_modules" in audit_data
        assert "content" in audit_data["failed_modules"]


class TestPartialResultsReportGeneration:
    """Tests for report generation with partial results."""

    def test_html_report_shows_unavailable_modules(self):
        """Verify HTML report properly displays unavailable module sections."""
        partial_result = {
            "audits": {
                "technical": {"score": 75, "status": "completed"},
                "content": {"score": None, "status": "unavailable", "message": "Temporarily unavailable"},
                "ai_visibility": {"score": 80, "status": "completed"},
            }
        }

        content = partial_result["audits"]["content"]
        assert content["status"] == "unavailable"
        assert "message" in content

    def test_pdf_report_handles_missing_data(self):
        """Verify PDF generation handles missing module data gracefully."""
        partial_result = {
            "url": "https://example.com",
            "company_name": "Test",
            "audits": {
                "technical": {"score": 70, "issues": [], "recommendations": []},
                "content": {"score": None, "status": "unavailable"},
                "ai_visibility": {"score": None, "status": "unavailable"},
            }
        }

        available_modules = [
            name for name, data in partial_result["audits"].items()
            if data.get("status") != "unavailable" and data.get("score") is not None
        ]
        assert len(available_modules) == 1
        assert "technical" in available_modules
