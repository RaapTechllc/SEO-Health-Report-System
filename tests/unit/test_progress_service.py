"""Tests for progress tracking service."""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from packages.seo_health_report.progress.service import (
    AuditProgress,
    ModuleProgress,
    _parse_module_events,
    estimate_completion_time,
    get_audit_progress,
)


class TestEstimateCompletionTime:
    def test_basic_tier(self):
        result = estimate_completion_time("basic", 10)
        assert result == 140  # 120 base + 10 * 2

    def test_pro_tier(self):
        result = estimate_completion_time("pro", 10)
        assert result == 350  # 300 base + 10 * 5

    def test_enterprise_tier(self):
        result = estimate_completion_time("enterprise", 10)
        assert result == 1000  # 900 base + 10 * 10

    def test_unknown_tier_defaults_to_basic(self):
        result = estimate_completion_time("unknown", 10)
        assert result == 140

    def test_zero_pages(self):
        result = estimate_completion_time("basic", 0)
        assert result == 120


class TestModuleProgress:
    def test_to_dict_with_dates(self):
        now = datetime(2025, 1, 18, 10, 0, 0)
        mp = ModuleProgress(
            module_name="technical",
            status="completed",
            progress_pct=100,
            started_at=now,
            completed_at=now + timedelta(minutes=2),
        )
        result = mp.to_dict()
        assert result["module_name"] == "technical"
        assert result["status"] == "completed"
        assert result["started_at"] == "2025-01-18T10:00:00"
        assert result["completed_at"] == "2025-01-18T10:02:00"

    def test_to_dict_without_dates(self):
        mp = ModuleProgress(module_name="ai", status="pending", progress_pct=0)
        result = mp.to_dict()
        assert result["started_at"] is None
        assert result["completed_at"] is None


class TestParseModuleEvents:
    def test_empty_events(self):
        modules = _parse_module_events([])
        assert len(modules) == 3
        assert all(m.status == "pending" for m in modules.values())

    def test_step_started_event(self):
        events = [
            ("step_started", "Starting technical audit", None, datetime.utcnow(), None),
        ]
        modules = _parse_module_events(events)
        assert modules["technical"].status == "running"
        assert modules["technical"].started_at is not None

    def test_step_done_event(self):
        events = [
            ("step_started", "Starting technical audit", None, datetime.utcnow(), None),
            ("step_done", "Technical audit complete", None, datetime.utcnow(), None),
        ]
        modules = _parse_module_events(events)
        assert modules["technical"].status == "completed"
        assert modules["technical"].progress_pct == 100

    def test_error_event(self):
        events = [
            ("error", "Content audit failed: timeout", None, datetime.utcnow(), None),
        ]
        modules = _parse_module_events(events)
        assert modules["content"].status == "failed"
        assert "timeout" in modules["content"].error_message

    def test_progress_update(self):
        events = [
            ("step_started", "Starting ai analysis", None, datetime.utcnow(), None),
            ("metric", "AI analysis progress", 50, datetime.utcnow(), None),
        ]
        modules = _parse_module_events(events)
        assert modules["ai"].progress_pct == 50


class TestGetAuditProgress:
    def test_audit_not_found(self):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = None
        result = get_audit_progress(db, "nonexistent")
        assert result is None

    def test_completed_audit(self):
        db = MagicMock()
        started = datetime(2025, 1, 18, 10, 0, 0)
        completed = datetime(2025, 1, 18, 10, 5, 0)

        db.execute.return_value.fetchone.return_value = (
            "completed", "pro", started, completed
        )
        db.execute.return_value.fetchall.return_value = []

        result = get_audit_progress(db, "aud_123")
        assert result.overall_status == "completed"
        assert result.overall_progress_pct == 100
        assert all(m.status == "completed" for m in result.modules)

    def test_running_audit_calculates_elapsed(self):
        db = MagicMock()
        started = datetime.utcnow() - timedelta(seconds=60)

        audit_result = MagicMock()
        audit_result.fetchone.return_value = ("running", "basic", started, None)

        events_result = MagicMock()
        events_result.fetchall.return_value = [
            ("step_done", "Technical audit done", 100, datetime.utcnow(), None),
        ]

        db.execute.side_effect = [audit_result, events_result]

        result = get_audit_progress(db, "aud_123")
        assert result.overall_status == "running"
        assert result.elapsed_seconds >= 59
        assert result.estimated_completion is not None

    def test_to_dict_serialization(self):
        progress = AuditProgress(
            audit_id="aud_123",
            overall_status="running",
            overall_progress_pct=50,
            modules=[
                ModuleProgress("technical", "completed", 100),
                ModuleProgress("content", "running", 50),
                ModuleProgress("ai", "pending", 0),
            ],
            started_at=datetime(2025, 1, 18, 10, 0, 0),
            estimated_completion=datetime(2025, 1, 18, 10, 5, 0),
            elapsed_seconds=120,
        )
        result = progress.to_dict()
        assert result["audit_id"] == "aud_123"
        assert result["started_at"] == "2025-01-18T10:00:00"
        assert len(result["modules"]) == 3
