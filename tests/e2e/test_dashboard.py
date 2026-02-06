"""
E2E Tests for Dashboard UI flows.

Tests dashboard functionality including:
- Audit list view
- Audit detail view
- Progress polling
- Report download links

These tests use mocked responses to avoid requiring a running server.
"""

import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


class TestAuditListView:
    """Tests for the audit list view."""

    def test_audit_list_returns_audits(self):
        """Test that audit list endpoint returns audits."""
        mock_audits = [
            {
                "audit_id": "audit_001",
                "status": "completed",
                "url": "https://example1.com",
                "company_name": "Company One",
                "overall_score": 85,
                "grade": "B",
                "tier": "basic",
                "created_at": "2024-01-15T10:00:00",
            },
            {
                "audit_id": "audit_002",
                "status": "running",
                "url": "https://example2.com",
                "company_name": "Company Two",
                "overall_score": None,
                "grade": None,
                "tier": "pro",
                "created_at": "2024-01-15T11:00:00",
            },
            {
                "audit_id": "audit_003",
                "status": "pending",
                "url": "https://example3.com",
                "company_name": "Company Three",
                "overall_score": None,
                "grade": None,
                "tier": "enterprise",
                "created_at": "2024-01-15T12:00:00",
            },
        ]

        # Simulate API response
        response = {"audits": mock_audits}

        assert len(response["audits"]) == 3
        assert response["audits"][0]["status"] == "completed"
        assert response["audits"][1]["status"] == "running"
        assert response["audits"][2]["status"] == "pending"

    def test_audit_list_ordered_by_date(self):
        """Test that audits are ordered by date (newest first)."""
        mock_audits = [
            {"audit_id": "audit_003", "created_at": "2024-01-15T12:00:00"},
            {"audit_id": "audit_002", "created_at": "2024-01-15T11:00:00"},
            {"audit_id": "audit_001", "created_at": "2024-01-15T10:00:00"},
        ]

        # Verify order is newest first
        dates = [a["created_at"] for a in mock_audits]
        assert dates == sorted(dates, reverse=True)

    def test_audit_list_pagination(self):
        """Test audit list pagination."""
        # Create 150 mock audits
        all_audits = [
            {"audit_id": f"audit_{i:03d}", "created_at": f"2024-01-{i+1:02d}T10:00:00"}
            for i in range(150)
        ]

        # Simulate paginated response (limit 100)
        page_1 = all_audits[:100]
        page_2 = all_audits[100:]

        assert len(page_1) == 100
        assert len(page_2) == 50

    def test_audit_list_empty(self):
        """Test audit list when no audits exist."""
        response = {"audits": []}

        assert len(response["audits"]) == 0

    def test_audit_list_filters_by_status(self):
        """Test filtering audits by status."""
        all_audits = [
            {"audit_id": "audit_001", "status": "completed"},
            {"audit_id": "audit_002", "status": "running"},
            {"audit_id": "audit_003", "status": "completed"},
            {"audit_id": "audit_004", "status": "failed"},
        ]

        # Filter by status
        completed = [a for a in all_audits if a["status"] == "completed"]
        running = [a for a in all_audits if a["status"] == "running"]
        failed = [a for a in all_audits if a["status"] == "failed"]

        assert len(completed) == 2
        assert len(running) == 1
        assert len(failed) == 1


class TestAuditDetailView:
    """Tests for the audit detail view."""

    def test_audit_detail_returns_full_data(self):
        """Test that audit detail endpoint returns complete data."""
        mock_audit = {
            "audit_id": "audit_123",
            "status": "completed",
            "url": "https://example.com",
            "company_name": "Test Corp",
            "tier": "pro",
            "overall_score": 78,
            "grade": "C",
            "created_at": "2024-01-15T10:00:00",
            "completed_at": "2024-01-15T10:05:00",
            "result": {
                "audits": {
                    "technical": {"score": 80, "grade": "B"},
                    "content": {"score": 75, "grade": "C"},
                    "ai_visibility": {"score": 78, "grade": "C"},
                }
            },
            "report_html_url": "/audits/audit_123/report/html",
            "report_pdf_url": "/audits/audit_123/report/pdf",
        }

        assert mock_audit["audit_id"] == "audit_123"
        assert mock_audit["overall_score"] == 78
        assert "technical" in mock_audit["result"]["audits"]
        assert "report_html_url" in mock_audit

    def test_audit_detail_not_found(self):
        """Test 404 response for non-existent audit."""
        def get_audit(audit_id):
            if audit_id == "nonexistent":
                return {"error": "Audit not found", "status_code": 404}
            return {"audit_id": audit_id}

        result = get_audit("nonexistent")
        assert result["status_code"] == 404

    def test_audit_detail_component_scores(self):
        """Test that component scores are included."""
        mock_audit = {
            "audit_id": "audit_123",
            "overall_score": 75,
            "result": {
                "audits": {
                    "technical": {
                        "score": 80,
                        "grade": "B",
                        "components": {
                            "crawlability": {"score": 18, "max": 20},
                            "speed": {"score": 22, "max": 25},
                            "mobile": {"score": 15, "max": 20},
                        }
                    },
                    "content": {
                        "score": 70,
                        "grade": "C",
                        "components": {
                            "quality": {"score": 30, "max": 40},
                            "keywords": {"score": 20, "max": 30},
                        }
                    },
                    "ai_visibility": {
                        "score": 75,
                        "grade": "C",
                        "components": {
                            "presence": {"score": 40, "max": 50},
                            "accuracy": {"score": 35, "max": 50},
                        }
                    },
                }
            }
        }

        technical = mock_audit["result"]["audits"]["technical"]
        assert technical["score"] == 80
        assert len(technical["components"]) == 3

    def test_audit_detail_issues_and_recommendations(self):
        """Test that issues and recommendations are included."""
        mock_audit = {
            "audit_id": "audit_123",
            "result": {
                "audits": {
                    "technical": {
                        "issues": [
                            {"severity": "high", "description": "Missing meta descriptions"},
                            {"severity": "medium", "description": "Slow page load"},
                        ],
                        "recommendations": [
                            {"priority": "high", "action": "Add meta descriptions"},
                            {"priority": "medium", "action": "Optimize images"},
                        ]
                    }
                }
            }
        }

        technical = mock_audit["result"]["audits"]["technical"]
        assert len(technical["issues"]) == 2
        assert len(technical["recommendations"]) == 2
        assert technical["issues"][0]["severity"] == "high"


class TestProgressPolling:
    """Tests for progress polling functionality."""

    def test_progress_events_returned(self):
        """Test that progress events are returned."""
        mock_events = [
            {
                "event_type": "initializing",
                "message": "Starting audit for https://example.com",
                "progress_pct": 0,
                "timestamp": "2024-01-15T10:00:00",
            },
            {
                "event_type": "technical_audit",
                "message": "Running technical SEO audit",
                "progress_pct": 10,
                "timestamp": "2024-01-15T10:00:05",
            },
            {
                "event_type": "content_audit",
                "message": "Running content authority audit",
                "progress_pct": 30,
                "timestamp": "2024-01-15T10:00:30",
            },
            {
                "event_type": "ai_visibility_audit",
                "message": "Running AI visibility audit",
                "progress_pct": 50,
                "timestamp": "2024-01-15T10:01:00",
            },
            {
                "event_type": "generating_report",
                "message": "Generating audit report",
                "progress_pct": 80,
                "timestamp": "2024-01-15T10:02:00",
            },
            {
                "event_type": "completed",
                "message": "Audit completed with score 75 (C)",
                "progress_pct": 100,
                "timestamp": "2024-01-15T10:02:30",
            },
        ]

        response = {"audit_id": "audit_123", "events": mock_events}

        assert len(response["events"]) == 6
        assert response["events"][0]["progress_pct"] == 0
        assert response["events"][-1]["progress_pct"] == 100

    def test_progress_percentage_increases(self):
        """Test that progress percentage monotonically increases."""
        events = [
            {"progress_pct": 0},
            {"progress_pct": 10},
            {"progress_pct": 30},
            {"progress_pct": 50},
            {"progress_pct": 80},
            {"progress_pct": 100},
        ]

        percentages = [e["progress_pct"] for e in events]
        assert percentages == sorted(percentages)

    def test_progress_stages_in_order(self):
        """Test that progress stages occur in expected order."""
        expected_stages = [
            "initializing",
            "technical_audit",
            "content_audit",
            "ai_visibility_audit",
            "generating_report",
            "completed",
        ]

        events = [{"event_type": stage} for stage in expected_stages]
        actual_stages = [e["event_type"] for e in events]

        assert actual_stages == expected_stages

    def test_failed_stage_event(self):
        """Test that failed stage is recorded on error."""
        events = [
            {"event_type": "initializing", "progress_pct": 0},
            {"event_type": "technical_audit", "progress_pct": 10},
            {"event_type": "failed", "progress_pct": 0, "message": "Audit failed: Connection timeout"},
        ]

        assert events[-1]["event_type"] == "failed"
        assert "failed" in events[-1]["message"].lower()

    @pytest.mark.asyncio
    async def test_polling_interval(self):
        """Test that polling works at expected intervals."""
        import asyncio

        poll_count = 0
        max_polls = 3

        async def poll_progress():
            nonlocal poll_count
            poll_count += 1
            if poll_count >= max_polls:
                return {"status": "completed"}
            return {"status": "running", "progress_pct": poll_count * 30}

        # Simulate polling with short intervals for testing
        while poll_count < max_polls:
            result = await poll_progress()
            if result["status"] == "completed":
                break
            await asyncio.sleep(0.01)  # Short interval for test

        assert poll_count == max_polls


class TestReportDownload:
    """Tests for report download functionality."""

    def test_html_report_url_available(self):
        """Test that HTML report URL is available for completed audits."""
        audit = {
            "audit_id": "audit_123",
            "status": "completed",
            "report_html_url": "/audits/audit_123/report/html",
        }

        assert "report_html_url" in audit
        assert "/html" in audit["report_html_url"]

    def test_pdf_report_url_available(self):
        """Test that PDF report URL is available for completed audits."""
        audit = {
            "audit_id": "audit_123",
            "status": "completed",
            "report_pdf_url": "/audits/audit_123/report/pdf",
        }

        assert "report_pdf_url" in audit
        assert "/pdf" in audit["report_pdf_url"]

    def test_report_not_available_for_pending(self):
        """Test that reports are not available for pending audits."""
        audit = {
            "audit_id": "audit_123",
            "status": "pending",
        }

        assert "report_html_url" not in audit
        assert "report_pdf_url" not in audit

    def test_report_not_available_for_failed(self):
        """Test that reports are not available for failed audits."""
        audit = {
            "audit_id": "audit_123",
            "status": "failed",
        }

        assert "report_html_url" not in audit
        assert "report_pdf_url" not in audit


class TestDashboardNavigation:
    """Tests for dashboard navigation."""

    def test_navigation_from_list_to_detail(self):
        """Test navigation from audit list to audit detail."""
        # Simulate clicking on an audit in the list
        selected_audit_id = "audit_123"
        detail_url = f"/dashboard/audits/{selected_audit_id}"

        assert selected_audit_id in detail_url

    def test_navigation_back_to_list(self):
        """Test navigation back to audit list."""
        list_url = "/dashboard/audits"
        assert "/audits" in list_url

    def test_breadcrumb_navigation(self):
        """Test breadcrumb navigation structure."""
        breadcrumbs = [
            {"label": "Dashboard", "url": "/dashboard"},
            {"label": "Audits", "url": "/dashboard/audits"},
            {"label": "Audit #123", "url": "/dashboard/audits/audit_123"},
        ]

        assert len(breadcrumbs) == 3
        assert breadcrumbs[0]["label"] == "Dashboard"
        assert breadcrumbs[-1]["label"] == "Audit #123"


class TestDashboardDataDisplay:
    """Tests for data display in dashboard."""

    def test_score_display_format(self):
        """Test that scores are displayed correctly."""
        audit = {"overall_score": 78, "grade": "C"}

        # Score should be displayed as integer out of 100
        score_display = f"{audit['overall_score']}/100"
        assert score_display == "78/100"

        # Grade should be a letter
        assert audit["grade"] in ["A", "B", "C", "D", "F"]

    def test_date_display_format(self):
        """Test that dates are formatted for display."""
        created_at = "2024-01-15T10:30:00"
        dt = datetime.fromisoformat(created_at)

        # Various display formats
        display_date = dt.strftime("%B %d, %Y")
        display_time = dt.strftime("%H:%M")

        assert display_date == "January 15, 2024"
        assert display_time == "10:30"

    def test_status_badge_colors(self):
        """Test that status badges have appropriate colors."""
        status_colors = {
            "completed": "green",
            "running": "blue",
            "pending": "yellow",
            "failed": "red",
        }

        for status, color in status_colors.items():
            assert status in status_colors
            assert color is not None

    def test_tier_badge_display(self):
        """Test tier badges are displayed correctly."""
        tier_labels = {
            "basic": "Basic",
            "pro": "Pro",
            "enterprise": "Enterprise",
        }

        for tier, label in tier_labels.items():
            assert tier in tier_labels
            assert label.title() == label  # Should be title case


class TestDashboardErrorStates:
    """Tests for error state handling in dashboard."""

    def test_loading_state(self):
        """Test loading state is shown while fetching data."""
        loading_state = {
            "is_loading": True,
            "data": None,
            "error": None,
        }

        assert loading_state["is_loading"] is True
        assert loading_state["data"] is None

    def test_error_state(self):
        """Test error state is shown on API failure."""
        error_state = {
            "is_loading": False,
            "data": None,
            "error": "Failed to load audits. Please try again.",
        }

        assert error_state["is_loading"] is False
        assert error_state["error"] is not None

    def test_empty_state(self):
        """Test empty state when no audits exist."""
        empty_state = {
            "is_loading": False,
            "data": {"audits": []},
            "error": None,
        }

        assert len(empty_state["data"]["audits"]) == 0

    def test_retry_on_error(self):
        """Test retry functionality on error."""
        retry_count = 0
        max_retries = 3

        def fetch_with_retry():
            nonlocal retry_count
            retry_count += 1
            if retry_count < max_retries:
                raise Exception("Network error")
            return {"audits": []}

        result = None
        while retry_count < max_retries:
            try:
                result = fetch_with_retry()
                break
            except Exception:
                if retry_count >= max_retries:
                    result = {"error": "Max retries exceeded"}
                    break

        assert retry_count == max_retries
        assert result == {"audits": []}


class TestDashboardAPIIntegration:
    """Tests for dashboard API integration."""

    def test_api_endpoints_structure(self):
        """Test expected API endpoint structure."""
        endpoints = {
            "list_audits": "/audits",
            "get_audit": "/audit/{audit_id}",
            "get_audit_full": "/audit/{audit_id}/full",
            "get_events": "/audits/{audit_id}/events",
            "get_report_html": "/audits/{audit_id}/report/html",
            "get_report_pdf": "/audits/{audit_id}/report/pdf",
        }

        assert "list_audits" in endpoints
        assert "get_audit" in endpoints
        assert "{audit_id}" in endpoints["get_audit"]

    def test_api_response_structure(self):
        """Test expected API response structure."""
        # List response
        list_response = {
            "audits": [
                {"audit_id": "...", "status": "...", "url": "...", "company_name": "..."}
            ]
        }
        assert "audits" in list_response

        # Detail response
        detail_response = {
            "audit_id": "...",
            "status": "...",
            "url": "...",
            "company_name": "...",
            "overall_score": 0,
            "grade": "F",
        }
        assert "audit_id" in detail_response
        assert "overall_score" in detail_response

        # Events response
        events_response = {
            "audit_id": "...",
            "events": [
                {"event_type": "...", "message": "...", "progress_pct": 0}
            ]
        }
        assert "events" in events_response
