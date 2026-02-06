"""Tests for audit completion webhook integration.

These tests focus on the webhook firing logic in isolation.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock heavy dependencies before importing main
sys.modules.setdefault("stripe", MagicMock())


class TestFireAuditWebhookFunction:
    """Tests for fire_audit_webhook helper function logic."""

    @pytest.mark.asyncio
    async def test_completed_webhook_payload_structure(self):
        """Test the payload structure for completed audit webhooks."""
        from packages.seo_health_report.webhooks import WebhookEvent, WebhookService

        MagicMock()
        mock_service = MagicMock(spec=WebhookService)
        mock_service.fire_event = AsyncMock(return_value=["del_123"])
        mock_service.close = AsyncMock()

        # Simulate fire_audit_webhook logic
        audit_data = {
            "url": "https://example.com",
            "company_name": "Example Inc",
            "tier": "pro",
            "overall_score": 85,
            "grade": "B+",
            "completed_at": "2024-01-15T10:30:00",
        }

        payload = {
            "audit_id": "audit_123",
            "url": audit_data.get("url"),
            "company_name": audit_data.get("company_name"),
            "tier": audit_data.get("tier"),
            "overall_score": audit_data.get("overall_score"),
            "grade": audit_data.get("grade"),
            "completed_at": audit_data.get("completed_at"),
        }

        await mock_service.fire_event(
            tenant_id="tenant_456",
            event=WebhookEvent.AUDIT_COMPLETED,
            payload=payload,
        )

        mock_service.fire_event.assert_called_once()
        call_kwargs = mock_service.fire_event.call_args.kwargs
        assert call_kwargs["tenant_id"] == "tenant_456"
        assert call_kwargs["event"] == WebhookEvent.AUDIT_COMPLETED
        assert call_kwargs["payload"]["audit_id"] == "audit_123"
        assert call_kwargs["payload"]["overall_score"] == 85
        assert call_kwargs["payload"]["grade"] == "B+"

    @pytest.mark.asyncio
    async def test_failed_webhook_includes_error(self):
        """Test the payload for failed audit webhooks includes error."""
        from packages.seo_health_report.webhooks import WebhookEvent, WebhookService

        mock_service = MagicMock(spec=WebhookService)
        mock_service.fire_event = AsyncMock(return_value=["del_456"])
        mock_service.close = AsyncMock()

        audit_data = {
            "url": "https://example.com",
            "company_name": "Example Inc",
            "tier": "basic",
            "error": "Connection timeout",
        }

        payload = {
            "audit_id": "audit_789",
            "url": audit_data.get("url"),
            "company_name": audit_data.get("company_name"),
            "tier": audit_data.get("tier"),
            "error": audit_data.get("error"),
        }

        await mock_service.fire_event(
            tenant_id="tenant_456",
            event=WebhookEvent.AUDIT_FAILED,
            payload=payload,
        )

        call_kwargs = mock_service.fire_event.call_args.kwargs
        assert call_kwargs["event"] == WebhookEvent.AUDIT_FAILED
        assert call_kwargs["payload"]["error"] == "Connection timeout"


class TestWebhookServiceIntegration:
    """Tests for WebhookService fire_event integration."""

    @pytest.mark.asyncio
    async def test_fire_event_with_audit_payload(self):
        """Test WebhookService.fire_event with audit completion payload."""
        from packages.seo_health_report.webhooks.service import WebhookEvent, WebhookService

        mock_db = MagicMock()
        mock_webhook = MagicMock()
        mock_webhook.id = "wh_123"
        mock_webhook.tenant_id = "tenant_1"
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.secret = "test_secret"
        mock_webhook.events = ["audit.completed", "audit.failed"]
        mock_webhook.is_active = True

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_webhook]

        service = WebhookService(mock_db)

        with patch.object(service, "_create_and_deliver", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = "del_abc"

            payload = {
                "audit_id": "audit_123",
                "url": "https://example.com",
                "overall_score": 90,
                "grade": "A",
            }

            delivery_ids = await service.fire_event(
                tenant_id="tenant_1",
                event=WebhookEvent.AUDIT_COMPLETED,
                payload=payload,
            )

        assert delivery_ids == ["del_abc"]
        mock_deliver.assert_called_once_with(mock_webhook, "audit.completed", payload)

    @pytest.mark.asyncio
    async def test_fire_event_filters_by_subscribed_events(self):
        """Test that fire_event only delivers to webhooks subscribed to the event."""
        from packages.seo_health_report.webhooks.service import WebhookEvent, WebhookService

        mock_db = MagicMock()

        # Webhook only subscribed to audit.completed
        mock_webhook_completed = MagicMock()
        mock_webhook_completed.id = "wh_1"
        mock_webhook_completed.events = ["audit.completed"]
        mock_webhook_completed.is_active = True

        # Webhook only subscribed to audit.failed
        mock_webhook_failed = MagicMock()
        mock_webhook_failed.id = "wh_2"
        mock_webhook_failed.events = ["audit.failed"]
        mock_webhook_failed.is_active = True

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_webhook_completed, mock_webhook_failed]

        service = WebhookService(mock_db)

        with patch.object(service, "_create_and_deliver", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = "del_xyz"

            # Fire AUDIT_COMPLETED - should only deliver to wh_1
            await service.fire_event(
                tenant_id="tenant_1",
                event=WebhookEvent.AUDIT_COMPLETED,
                payload={"audit_id": "123"},
            )

        # Only the webhook subscribed to audit.completed should receive delivery
        assert mock_deliver.call_count == 1
        mock_deliver.assert_called_with(mock_webhook_completed, "audit.completed", {"audit_id": "123"})

    @pytest.mark.asyncio
    async def test_fire_event_skips_inactive_webhooks(self):
        """Test that fire_event skips inactive webhooks."""
        from packages.seo_health_report.webhooks.service import WebhookEvent, WebhookService

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        # Query already filters is_active == True, so return empty
        mock_query.all.return_value = []

        service = WebhookService(mock_db)

        with patch.object(service, "_create_and_deliver", new_callable=AsyncMock) as mock_deliver:
            delivery_ids = await service.fire_event(
                tenant_id="tenant_1",
                event=WebhookEvent.AUDIT_COMPLETED,
                payload={"audit_id": "123"},
            )

        assert delivery_ids == []
        mock_deliver.assert_not_called()


class TestAuditWebhookPayloads:
    """Tests for webhook payload content requirements."""

    def test_completed_payload_required_fields(self):
        """Test that completed audit payload has all required fields."""
        required_fields = ["audit_id", "url", "company_name", "tier", "overall_score", "grade", "completed_at"]

        audit_data = {
            "url": "https://example.com",
            "company_name": "Example Inc",
            "tier": "enterprise",
            "overall_score": 92,
            "grade": "A",
            "completed_at": "2024-01-15T12:00:00Z",
        }

        payload = {
            "audit_id": "audit_xyz",
            "url": audit_data.get("url"),
            "company_name": audit_data.get("company_name"),
            "tier": audit_data.get("tier"),
            "overall_score": audit_data.get("overall_score"),
            "grade": audit_data.get("grade"),
            "completed_at": audit_data.get("completed_at"),
        }

        for field in required_fields:
            assert field in payload, f"Missing required field: {field}"

    def test_failed_payload_includes_error(self):
        """Test that failed audit payload includes error message."""
        audit_data = {
            "url": "https://example.com",
            "company_name": "Example Inc",
            "tier": "basic",
            "error": "DNS resolution failed",
        }

        payload = {
            "audit_id": "audit_fail",
            "url": audit_data.get("url"),
            "company_name": audit_data.get("company_name"),
            "tier": audit_data.get("tier"),
            "error": audit_data.get("error"),
        }

        assert "error" in payload
        assert payload["error"] == "DNS resolution failed"

    def test_payload_scores_are_numeric(self):
        """Test that score values are numeric."""
        payload = {
            "audit_id": "audit_123",
            "overall_score": 85,
            "grade": "B+",
        }

        assert isinstance(payload["overall_score"], (int, float))


class TestWebhookEventTypes:
    """Tests for webhook event type handling."""

    def test_audit_completed_event_value(self):
        """Test AUDIT_COMPLETED event value."""
        from packages.seo_health_report.webhooks import WebhookEvent
        assert WebhookEvent.AUDIT_COMPLETED.value == "audit.completed"

    def test_audit_failed_event_value(self):
        """Test AUDIT_FAILED event value."""
        from packages.seo_health_report.webhooks import WebhookEvent
        assert WebhookEvent.AUDIT_FAILED.value == "audit.failed"

    def test_audit_started_event_value(self):
        """Test AUDIT_STARTED event value."""
        from packages.seo_health_report.webhooks import WebhookEvent
        assert WebhookEvent.AUDIT_STARTED.value == "audit.started"

    def test_event_in_subscription_check(self):
        """Test event subscription filtering logic."""
        from packages.seo_health_report.webhooks import WebhookEvent

        subscribed_events = ["audit.completed", "audit.failed"]

        assert WebhookEvent.AUDIT_COMPLETED.value in subscribed_events
        assert WebhookEvent.AUDIT_FAILED.value in subscribed_events
        assert WebhookEvent.AUDIT_STARTED.value not in subscribed_events


class TestWebhookDeliveryFlow:
    """Tests for the complete webhook delivery flow."""

    @pytest.mark.asyncio
    async def test_delivery_creates_record_and_attempts(self):
        """Test that delivery creates a record and attempts HTTP request."""
        from packages.seo_health_report.webhooks.service import WebhookService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        mock_webhook = MagicMock()
        mock_webhook.id = "wh_123"
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.secret = "test_secret"

        service = WebhookService(mock_db)

        with patch.object(service, "_deliver", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = True

            with patch("packages.seo_health_report.webhooks.service.uuid") as mock_uuid:
                mock_uuid.uuid4.return_value.hex = "abc123"

                with patch("database.WebhookDelivery") as mock_delivery_class:
                    mock_delivery = MagicMock()
                    mock_delivery.id = "del_abc123"
                    mock_delivery_class.return_value = mock_delivery

                    await service._create_and_deliver(
                        webhook=mock_webhook,
                        event_type="audit.completed",
                        payload={"audit_id": "123"},
                    )

        # Record should be created
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

        # Delivery should be attempted
        mock_deliver.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_delivery_increments_counter(self):
        """Test that successful delivery increments metrics counter."""
        from packages.seo_health_report.webhooks.service import WebhookService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        mock_webhook = MagicMock()
        mock_webhook.id = "wh_123"

        service = WebhookService(mock_db)

        with patch.object(service, "_deliver", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = True

            with patch("packages.seo_health_report.webhooks.service.uuid") as mock_uuid:
                mock_uuid.uuid4.return_value.hex = "abc123"

                with patch("database.WebhookDelivery") as mock_delivery_class:
                    mock_delivery = MagicMock()
                    mock_delivery_class.return_value = mock_delivery

                    with patch("packages.seo_health_report.metrics.metrics") as mock_metrics:
                        await service._create_and_deliver(
                            webhook=mock_webhook,
                            event_type="audit.completed",
                            payload={"audit_id": "123"},
                        )

                        mock_metrics.inc_counter.assert_called_with(
                            "webhook_deliveries_total",
                            labels={"status": "success"}
                        )
