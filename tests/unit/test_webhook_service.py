"""Tests for webhook service."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from packages.seo_health_report.webhooks.security import SSRFError
from packages.seo_health_report.webhooks.service import (
    MAX_RETRIES,
    RETRY_DELAYS,
    WebhookEvent,
    WebhookService,
)


class TestWebhookEvent:
    """Tests for webhook event types."""

    def test_event_values(self):
        assert WebhookEvent.AUDIT_COMPLETED.value == "audit.completed"
        assert WebhookEvent.AUDIT_FAILED.value == "audit.failed"
        assert WebhookEvent.AUDIT_STARTED.value == "audit.started"

    def test_event_as_string(self):
        assert WebhookEvent.AUDIT_COMPLETED.value == "audit.completed"


class TestRetryConfiguration:
    """Tests for retry timing configuration."""

    def test_retry_delays(self):
        assert RETRY_DELAYS == [60, 300, 900, 3600, 14400]

    def test_max_retries(self):
        assert MAX_RETRIES == 5


class MockWebhook:
    """Mock webhook for testing."""
    def __init__(self, id="wh_123", tenant_id="tenant_1", url="https://example.com/webhook",
                 secret="test_secret", events=None, is_active=True):
        self.id = id
        self.tenant_id = tenant_id
        self.url = url
        self.secret = secret
        self.events = events or ["audit.completed"]
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class MockDelivery:
    """Mock delivery for testing."""
    def __init__(self, id="del_123", webhook_id="wh_123", event_type="audit.completed",
                 payload=None, status="pending", attempts=0):
        self.id = id
        self.webhook_id = webhook_id
        self.event_type = event_type
        self.payload = payload or {"audit_id": "abc"}
        self.status = status
        self.attempts = attempts
        self.next_retry_at = None
        self.response_code = None
        self.response_body = None
        self.error_message = None
        self.created_at = datetime.utcnow()
        self.delivered_at = None


class TestWebhookServiceCreate:
    """Tests for webhook creation."""

    def test_create_webhook_success(self):
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = WebhookService(mock_db)

        with patch("packages.seo_health_report.webhooks.service.validate_webhook_url") as mock_validate:
            mock_validate.return_value = (True, None)

            with patch("database.Webhook") as mock_webhook_class:
                mock_webhook = MockWebhook()
                mock_webhook_class.return_value = mock_webhook

                result = service.create_webhook(
                    tenant_id="tenant_1",
                    url="https://example.com/webhook",
                    events=["audit.completed"],
                )

        assert "id" in result
        assert result["url"] == "https://example.com/webhook"
        assert "secret" in result  # Secret returned on creation
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_webhook_ssrf_blocked(self):
        mock_db = MagicMock()
        service = WebhookService(mock_db)

        with patch("packages.seo_health_report.webhooks.service.validate_webhook_url") as mock_validate:
            mock_validate.return_value = (False, "Private IP blocked")

            with pytest.raises(SSRFError):
                service.create_webhook(
                    tenant_id="tenant_1",
                    url="http://127.0.0.1/webhook",
                    events=["audit.completed"],
                )

    def test_create_webhook_invalid_event(self):
        mock_db = MagicMock()
        service = WebhookService(mock_db)

        with patch("packages.seo_health_report.webhooks.service.validate_webhook_url") as mock_validate:
            mock_validate.return_value = (True, None)

            with pytest.raises(ValueError) as exc_info:
                service.create_webhook(
                    tenant_id="tenant_1",
                    url="https://example.com/webhook",
                    events=["invalid.event"],
                )

            assert "Invalid event type" in str(exc_info.value)


class TestWebhookServiceList:
    """Tests for listing webhooks."""

    def test_list_webhooks(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [MockWebhook(), MockWebhook(id="wh_456")]

        service = WebhookService(mock_db)
        result = service.list_webhooks("tenant_1")

        assert len(result) == 2
        assert result[0]["id"] == "wh_123"
        assert result[1]["id"] == "wh_456"

    def test_list_webhooks_empty(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        service = WebhookService(mock_db)
        result = service.list_webhooks("tenant_1")

        assert result == []


class TestWebhookServiceGet:
    """Tests for getting a single webhook."""

    def test_get_webhook_found(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MockWebhook()

        service = WebhookService(mock_db)
        result = service.get_webhook("wh_123", "tenant_1")

        assert result["id"] == "wh_123"
        assert "secret" not in result  # Secret not returned on get

    def test_get_webhook_not_found(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        service = WebhookService(mock_db)
        result = service.get_webhook("wh_999", "tenant_1")

        assert result is None


class TestWebhookServiceDelete:
    """Tests for deleting webhooks."""

    def test_delete_webhook_success(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MockWebhook()

        service = WebhookService(mock_db)
        result = service.delete_webhook("wh_123", "tenant_1")

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_webhook_not_found(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        service = WebhookService(mock_db)
        result = service.delete_webhook("wh_999", "tenant_1")

        assert result is False


class TestWebhookDelivery:
    """Tests for webhook delivery."""

    @pytest.mark.asyncio
    async def test_deliver_success(self):
        mock_db = MagicMock()
        service = WebhookService(mock_db)

        webhook = MockWebhook()
        delivery = MockDelivery()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service._deliver(delivery, webhook)

        assert result is True
        assert delivery.status == "delivered"
        assert delivery.response_code == 200
        assert delivery.delivered_at is not None

    @pytest.mark.asyncio
    async def test_deliver_failure_schedules_retry(self):
        mock_db = MagicMock()
        service = WebhookService(mock_db)

        webhook = MockWebhook()
        delivery = MockDelivery(attempts=0)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service._deliver(delivery, webhook)

        assert result is False
        assert delivery.status == "pending"
        assert delivery.next_retry_at is not None
        assert delivery.attempts == 1

    @pytest.mark.asyncio
    async def test_deliver_timeout_schedules_retry(self):
        mock_db = MagicMock()
        service = WebhookService(mock_db)

        webhook = MockWebhook()
        delivery = MockDelivery(attempts=0)

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_get_client.return_value = mock_client

            result = await service._deliver(delivery, webhook)

        assert result is False
        assert delivery.error_message == "Request timeout"
        assert delivery.status == "pending"

    @pytest.mark.asyncio
    async def test_deliver_max_retries_marks_failed(self):
        mock_db = MagicMock()
        service = WebhookService(mock_db)

        webhook = MockWebhook()
        delivery = MockDelivery(attempts=MAX_RETRIES - 1)  # One more attempt will hit max

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error"

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await service._deliver(delivery, webhook)

        assert result is False
        assert delivery.status == "failed"
        assert delivery.attempts == MAX_RETRIES


class TestWebhookServiceGetDeliveries:
    """Tests for getting delivery history."""

    def test_get_deliveries(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.first.return_value = MockWebhook()
        mock_query.all.return_value = [MockDelivery(), MockDelivery(id="del_456")]

        service = WebhookService(mock_db)
        result = service.get_deliveries("wh_123", "tenant_1")

        assert len(result) == 2


class TestWebhookPayloadFormat:
    """Tests for webhook payload structure."""

    @pytest.mark.asyncio
    async def test_payload_envelope(self):
        mock_db = MagicMock()
        service = WebhookService(mock_db)

        webhook = MockWebhook()
        delivery = MockDelivery(payload={"audit_id": "abc", "score": 85})

        captured_payload = None

        async def capture_post(url, content, headers):
            nonlocal captured_payload
            captured_payload = json.loads(content)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            return mock_response

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = capture_post
            mock_get_client.return_value = mock_client

            await service._deliver(delivery, webhook)

        assert "event" in captured_payload
        assert "timestamp" in captured_payload
        assert "delivery_id" in captured_payload
        assert "data" in captured_payload
        assert captured_payload["data"]["audit_id"] == "abc"

    @pytest.mark.asyncio
    async def test_headers_include_signature(self):
        mock_db = MagicMock()
        service = WebhookService(mock_db)

        webhook = MockWebhook(secret="test_secret_123")
        delivery = MockDelivery()

        captured_headers = None

        async def capture_post(url, content, headers):
            nonlocal captured_headers
            captured_headers = headers
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            return mock_response

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = capture_post
            mock_get_client.return_value = mock_client

            await service._deliver(delivery, webhook)

        assert "X-Webhook-Signature" in captured_headers
        assert captured_headers["X-Webhook-Signature"].startswith("sha256=")
        assert "X-Webhook-Event" in captured_headers
        assert "X-Webhook-Delivery" in captured_headers
