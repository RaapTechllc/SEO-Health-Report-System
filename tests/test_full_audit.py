"""
Sprint 3 - Task 3.7.1: Full Audit Integration Test Suite.

Tests the complete audit flow including:
- Audit execution via handle_full_audit()
- Progress event tracking
- Result storage and formatting
- Error handling and webhook delivery
"""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from apps.worker.handlers.full_audit import handle_full_audit, write_progress_event
from packages.schemas.models import ProgressStage


@pytest.fixture
def mock_db():
    """Mock database session for testing."""
    db = MagicMock()
    db.execute = MagicMock()
    db.commit = MagicMock()
    return db


@pytest.fixture
def sample_payload():
    """Sample audit payload for testing."""
    return {
        "url": "https://example.com",
        "company_name": "Test Corp",
        "tier": "basic",
        "keywords": ["seo", "marketing"],
        "competitors": [],
        "tenant_id": "default",
    }


@pytest.fixture
def sample_payload_with_callback():
    """Sample payload with callback URL."""
    return {
        "url": "https://example.com",
        "company_name": "Test Corp",
        "tier": "pro",
        "keywords": ["seo", "marketing"],
        "competitors": ["https://competitor.com"],
        "tenant_id": "test-tenant",
        "callback_url": "https://webhook.example.com/callback",
    }


@pytest.fixture
def mock_raw_audit_result():
    """Mock raw result from run_full_audit."""
    return {
        "url": "https://example.com",
        "company_name": "Test Corp",
        "timestamp": "2024-01-15T10:00:00",
        "audits": {
            "technical": {
                "score": 80,
                "grade": "B",
                "components": {
                    "crawlability": {"score": 18, "max": 20},
                    "speed": {"score": 22, "max": 25},
                },
                "issues": [],
                "recommendations": [],
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


@pytest.fixture
def mock_composite_scores():
    """Mock composite score calculation result."""
    return {
        "overall_score": 75,
        "grade": "C",
        "component_scores": {
            "technical": {"score": 80, "weight": 0.30, "weighted_score": 24},
            "content": {"score": 75, "weight": 0.35, "weighted_score": 26.25},
            "ai_visibility": {"score": 70, "weight": 0.35, "weighted_score": 24.5},
        },
        "weights_used": {"technical": 0.30, "content": 0.35, "ai_visibility": 0.35},
    }


class TestWriteProgressEvent:
    """Tests for the write_progress_event function."""

    @pytest.mark.asyncio
    async def test_writes_event_to_database(self, mock_db):
        """Test that progress events are written to the database."""
        await write_progress_event(
            db=mock_db,
            audit_id="audit-123",
            job_id="job-456",
            stage=ProgressStage.INITIALIZING,
            progress_pct=0,
            message="Starting audit",
        )

        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

        call_args = mock_db.execute.call_args
        params = call_args[0][1]

        assert params["audit_id"] == "audit-123"
        assert params["job_id"] == "job-456"
        assert params["event_type"] == "initializing"
        assert params["progress_pct"] == 0
        assert params["message"] == "Starting audit"

    @pytest.mark.asyncio
    async def test_redacts_sensitive_data_in_message(self, mock_db):
        """Test that sensitive data is redacted from progress messages."""
        sensitive_message = "Processing with api_key=secret123"

        await write_progress_event(
            db=mock_db,
            audit_id="audit-123",
            job_id="job-456",
            stage=ProgressStage.TECHNICAL_AUDIT,
            progress_pct=10,
            message=sensitive_message,
        )

        call_args = mock_db.execute.call_args
        params = call_args[0][1]

        assert "secret123" not in params["message"]
        assert "[REDACTED]" in params["message"]


class TestAuditExecutionFlow:
    """Tests for the audit execution flow via handle_full_audit."""

    @pytest.mark.asyncio
    async def test_successful_audit_flow(
        self, mock_db, sample_payload, mock_raw_audit_result, mock_composite_scores
    ):
        """Test handle_full_audit() with mocked orchestrate.run_full_audit."""
        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ) as mock_run_audit, patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/default/audit-123.html",
        ):
            result = await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload,
                db=mock_db,
            )

            mock_run_audit.assert_called_once_with(
                target_url="https://example.com",
                company_name="Test Corp",
                primary_keywords=["seo", "marketing"],
                competitor_urls=[],
                rate_limiter=ANY,
            )

            assert "raw" in result
            assert "summary" in result
            assert result["raw"] == mock_raw_audit_result

    @pytest.mark.asyncio
    async def test_progress_events_written_in_order(
        self, mock_db, sample_payload, mock_raw_audit_result, mock_composite_scores
    ):
        """Verify progress events are written in correct order with correct stages."""
        progress_calls = []

        original_execute = mock_db.execute
        def capture_execute(*args, **kwargs):
            if args and "audit_progress_events" in str(args[0]):
                params = args[0] if len(args) == 1 else args[1]
                if isinstance(params, dict):
                    progress_calls.append(params.get("event_type"))
            return original_execute(*args, **kwargs)

        mock_db.execute = MagicMock(side_effect=capture_execute)

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/default/audit-123.html",
        ):
            await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload,
                db=mock_db,
            )

        expected_stages = [
            "initializing",
            "technical_audit",
            "content_audit",
            "ai_visibility_audit",
            "generating_report",
            "completed",
        ]

        assert len(progress_calls) == len(expected_stages)
        assert progress_calls == expected_stages

    @pytest.mark.asyncio
    async def test_audit_record_updated_with_scores(
        self, mock_db, sample_payload, mock_raw_audit_result, mock_composite_scores
    ):
        """Verify audit record is updated with scores and status."""
        update_calls = []

        def capture_execute(*args, **kwargs):
            sql_text = str(args[0]) if args else ""
            if "UPDATE audits SET" in sql_text:
                params = args[1] if len(args) > 1 else kwargs.get("params", {})
                update_calls.append(params)
            return MagicMock()

        mock_db.execute = MagicMock(side_effect=capture_execute)

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/default/audit-123.html",
        ):
            await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload,
                db=mock_db,
            )

        assert len(update_calls) >= 1
        final_update = update_calls[0]
        assert final_update["audit_id"] == "audit-123"
        assert final_update["score"] == 75
        assert final_update["grade"] == "C"


class TestProgressEventsWrittenCorrectly:
    """Tests for correct progress event tracking."""

    @pytest.mark.asyncio
    async def test_progress_pct_increases_monotonically(
        self, mock_db, sample_payload, mock_raw_audit_result, mock_composite_scores
    ):
        """Verify progress_pct increases monotonically through stages."""
        progress_values = []

        def capture_execute(*args, **kwargs):
            if args and len(args) > 1:
                params = args[1]
                if isinstance(params, dict) and "progress_pct" in params:
                    progress_values.append(params["progress_pct"])
            return MagicMock()

        mock_db.execute = MagicMock(side_effect=capture_execute)

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/default/audit-123.html",
        ):
            await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload,
                db=mock_db,
            )

        for i in range(1, len(progress_values)):
            assert progress_values[i] >= progress_values[i - 1], (
                f"Progress should increase: {progress_values[i-1]} -> {progress_values[i]}"
            )

        assert progress_values[-1] == 100

    @pytest.mark.asyncio
    async def test_messages_are_redacted(self, mock_db):
        """Verify sensitive data in messages is redacted."""
        sensitive_msg = "Error with token=abc123secret and api_key=xyz789"

        await write_progress_event(
            db=mock_db,
            audit_id="audit-123",
            job_id="job-456",
            stage=ProgressStage.FAILED,
            progress_pct=0,
            message=sensitive_msg,
        )

        call_args = mock_db.execute.call_args
        params = call_args[0][1]

        assert "abc123secret" not in params["message"]
        assert "xyz789" not in params["message"]


class TestResultStoredInCorrectFormat:
    """Tests for correct result storage format."""

    @pytest.mark.asyncio
    async def test_result_json_has_raw_and_summary(
        self, mock_db, sample_payload, mock_raw_audit_result, mock_composite_scores
    ):
        """Verify result_json has 'raw' and 'summary' keys."""
        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/default/audit-123.html",
        ):
            result = await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload,
                db=mock_db,
            )

        assert "raw" in result
        assert "summary" in result
        assert result["raw"] == mock_raw_audit_result

    @pytest.mark.asyncio
    async def test_summary_matches_audit_result_schema(
        self, mock_db, sample_payload, mock_raw_audit_result, mock_composite_scores
    ):
        """Verify summary matches AuditResult schema."""
        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/default/audit-123.html",
        ):
            result = await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload,
                db=mock_db,
            )

        summary = result["summary"]

        assert summary["audit_id"] == "audit-123"
        assert summary["url"] == "https://example.com"
        assert summary["company_name"] == "Test Corp"
        assert summary["tier"] == "basic"
        assert summary["status"] == "completed"
        assert summary["overall_score"] == 75
        assert summary["grade"] == "C"
        assert "technical_score" in summary
        assert "content_score" in summary
        assert "ai_visibility_score" in summary
        assert "report_path" in summary

    @pytest.mark.asyncio
    async def test_html_report_path_stored(
        self, mock_db, sample_payload, mock_raw_audit_result, mock_composite_scores
    ):
        """Verify HTML report path is generated and stored."""
        expected_path = "reports/default/audit-123.html"

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value=expected_path,
        ) as mock_gen_report:
            result = await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload,
                db=mock_db,
            )

        mock_gen_report.assert_called_once()
        assert result["summary"]["report_path"] == expected_path


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_failure_updates_audit_to_failed_status(self, mock_db, sample_payload):
        """Test that failure scenario updates audit to failed status."""
        update_calls = []

        def capture_execute(*args, **kwargs):
            sql_text = str(args[0]) if args else ""
            if "UPDATE audits SET status" in sql_text:
                params = args[1] if len(args) > 1 else kwargs.get("params", {})
                update_calls.append(params)
            return MagicMock()

        mock_db.execute = MagicMock(side_effect=capture_execute)

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            side_effect=Exception("Audit processing failed"),
        ):
            with pytest.raises(Exception, match="Audit processing failed"):
                await handle_full_audit(
                    audit_id="audit-123",
                    job_id="job-456",
                    payload=sample_payload,
                    db=mock_db,
                )

        failed_updates = [u for u in update_calls if u.get("status") == "failed"]
        assert len(failed_updates) >= 1

    @pytest.mark.asyncio
    async def test_webhook_delivered_on_failure(
        self, mock_db, sample_payload_with_callback
    ):
        """Test that webhook is delivered on failure."""
        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            side_effect=Exception("Audit failed unexpectedly"),
        ), patch(
            "apps.worker.handlers.full_audit.build_audit_webhook_payload",
            return_value={"event": "audit.failed", "audit_id": "audit-123"},
        ) as mock_build_payload, patch(
            "apps.worker.handlers.full_audit.deliver_webhook",
            new_callable=AsyncMock,
        ) as mock_deliver:
            with pytest.raises(Exception):
                await handle_full_audit(
                    audit_id="audit-123",
                    job_id="job-456",
                    payload=sample_payload_with_callback,
                    db=mock_db,
                )

        mock_build_payload.assert_called_once()
        call_kwargs = mock_build_payload.call_args
        assert call_kwargs[1]["status"] == "failed"

        mock_deliver.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_messages_are_redacted(self, mock_db, sample_payload):
        """Verify error messages are redacted before storage."""
        progress_messages = []

        def capture_execute(*args, **kwargs):
            if args and len(args) > 1:
                params = args[1]
                if isinstance(params, dict) and "message" in params:
                    progress_messages.append(params["message"])
            return MagicMock()

        mock_db.execute = MagicMock(side_effect=capture_execute)

        sensitive_error = "Connection failed: api_key=secret123 token=xyz789"

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            side_effect=Exception(sensitive_error),
        ):
            with pytest.raises(Exception):
                await handle_full_audit(
                    audit_id="audit-123",
                    job_id="job-456",
                    payload=sample_payload,
                    db=mock_db,
                )

        failed_messages = [m for m in progress_messages if "failed" in m.lower()]
        for msg in failed_messages:
            assert "secret123" not in msg
            assert "xyz789" not in msg

    @pytest.mark.asyncio
    async def test_failed_stage_progress_event_written(self, mock_db, sample_payload):
        """Test that FAILED stage progress event is written on error."""
        progress_stages = []

        def capture_execute(*args, **kwargs):
            if args and len(args) > 1:
                params = args[1]
                if isinstance(params, dict) and "event_type" in params:
                    progress_stages.append(params["event_type"])
            return MagicMock()

        mock_db.execute = MagicMock(side_effect=capture_execute)

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            side_effect=Exception("Test failure"),
        ):
            with pytest.raises(Exception):
                await handle_full_audit(
                    audit_id="audit-123",
                    job_id="job-456",
                    payload=sample_payload,
                    db=mock_db,
                )

        assert "failed" in progress_stages


class TestWebhookDelivery:
    """Tests for webhook delivery on successful completion."""

    @pytest.mark.asyncio
    async def test_webhook_delivered_on_success(
        self, mock_db, sample_payload_with_callback, mock_raw_audit_result, mock_composite_scores
    ):
        """Test webhook is delivered on successful audit completion."""
        mock_webhook_result = MagicMock()
        mock_webhook_result.success = True

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/test-tenant/audit-123.html",
        ), patch(
            "apps.worker.handlers.full_audit.build_audit_webhook_payload",
            return_value={"event": "audit.completed", "audit_id": "audit-123"},
        ) as mock_build, patch(
            "apps.worker.handlers.full_audit.deliver_webhook",
            new_callable=AsyncMock,
            return_value=mock_webhook_result,
        ) as mock_deliver:
            await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload_with_callback,
                db=mock_db,
            )

        mock_build.assert_called_once()
        build_kwargs = mock_build.call_args[1]
        assert build_kwargs["status"] == "completed"
        assert build_kwargs["overall_score"] == 75
        assert build_kwargs["grade"] == "C"

        mock_deliver.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_delivered_at_updated_on_success(
        self, mock_db, sample_payload_with_callback, mock_raw_audit_result, mock_composite_scores
    ):
        """Test that callback_delivered_at is updated when webhook succeeds."""
        update_sqls = []

        def capture_execute(*args, **kwargs):
            sql_text = str(args[0]) if args else ""
            update_sqls.append(sql_text)
            return MagicMock()

        mock_db.execute = MagicMock(side_effect=capture_execute)

        mock_webhook_result = MagicMock()
        mock_webhook_result.success = True

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/test-tenant/audit-123.html",
        ), patch(
            "apps.worker.handlers.full_audit.deliver_webhook",
            new_callable=AsyncMock,
            return_value=mock_webhook_result,
        ):
            await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=sample_payload_with_callback,
                db=mock_db,
            )

        callback_updates = [s for s in update_sqls if "callback_delivered_at" in s]
        assert len(callback_updates) >= 1


class TestTierHandling:
    """Tests for different audit tiers."""

    @pytest.mark.asyncio
    async def test_basic_tier_handled(
        self, mock_db, mock_raw_audit_result, mock_composite_scores
    ):
        """Test basic tier audit execution."""
        payload = {
            "url": "https://example.com",
            "company_name": "Basic Corp",
            "tier": "basic",
            "keywords": [],
            "competitors": [],
            "tenant_id": "default",
        }

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/default/audit-123.html",
        ):
            result = await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=payload,
                db=mock_db,
            )

        assert result["summary"]["tier"] == "basic"

    @pytest.mark.asyncio
    async def test_enterprise_tier_handled(
        self, mock_db, mock_raw_audit_result, mock_composite_scores
    ):
        """Test enterprise tier audit execution."""
        payload = {
            "url": "https://enterprise.com",
            "company_name": "Enterprise Corp",
            "tier": "enterprise",
            "keywords": ["enterprise", "solutions"],
            "competitors": ["https://competitor1.com", "https://competitor2.com"],
            "tenant_id": "enterprise-tenant",
        }

        with patch(
            "apps.worker.handlers.full_audit.run_full_audit",
            new_callable=AsyncMock,
            return_value=mock_raw_audit_result,
        ), patch(
            "apps.worker.handlers.full_audit.calculate_composite_score",
            return_value=mock_composite_scores,
        ), patch(
            "apps.worker.handlers.full_audit.generate_html_report_simple",
            new_callable=AsyncMock,
            return_value="reports/enterprise-tenant/audit-123.html",
        ):
            result = await handle_full_audit(
                audit_id="audit-123",
                job_id="job-456",
                payload=payload,
                db=mock_db,
            )

        assert result["summary"]["tier"] == "enterprise"
