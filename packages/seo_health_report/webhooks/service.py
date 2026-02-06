"""
Webhook service for delivering events to registered endpoints.

Features:
- HMAC-SHA256 payload signing
- Exponential backoff retries (5 attempts: 1m, 5m, 15m, 1h, 4h)
- SSRF protection
- Delivery tracking and metrics
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from .security import SSRFError, generate_secret, sign_payload, validate_webhook_url

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Supported webhook event types."""
    AUDIT_COMPLETED = "audit.completed"
    AUDIT_FAILED = "audit.failed"
    AUDIT_STARTED = "audit.started"


RETRY_DELAYS = [60, 300, 900, 3600, 14400]  # 1m, 5m, 15m, 1h, 4h
MAX_RETRIES = len(RETRY_DELAYS)
DELIVERY_TIMEOUT = 10.0


class WebhookService:
    """
    Service for managing webhooks and delivering events.

    Usage:
        service = WebhookService(db_session)

        # Create a webhook
        webhook = await service.create_webhook(
            tenant_id="tenant_123",
            url="https://example.com/webhook",
            events=["audit.completed", "audit.failed"]
        )

        # Fire an event
        await service.fire_event(
            tenant_id="tenant_123",
            event=WebhookEvent.AUDIT_COMPLETED,
            payload={"audit_id": "abc", "score": 85}
        )
    """

    def __init__(self, db: Session):
        self.db = db
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(DELIVERY_TIMEOUT),
                follow_redirects=False,
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def create_webhook(
        self,
        tenant_id: str,
        url: str,
        events: list[str],
    ) -> dict[str, Any]:
        """
        Create a new webhook subscription.

        Args:
            tenant_id: Tenant ID
            url: Webhook delivery URL
            events: List of event types to subscribe to

        Returns:
            Created webhook data (secret only returned on creation)

        Raises:
            SSRFError: If URL fails security validation
            ValueError: If events list is invalid
        """
        from database import Webhook

        # Validate URL for SSRF
        is_valid, error = validate_webhook_url(url)
        if not is_valid:
            raise SSRFError(error)

        # Validate events
        valid_events = {e.value for e in WebhookEvent}
        for event in events:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}. Valid types: {valid_events}")

        # Generate secret
        secret = generate_secret()

        # Create webhook
        webhook = Webhook(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            url=url,
            secret=secret,
            events=events,
            is_active=True,
        )

        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)

        logger.info(f"Created webhook {webhook.id} for tenant {tenant_id}")

        return {
            "id": webhook.id,
            "url": webhook.url,
            "events": webhook.events,
            "is_active": webhook.is_active,
            "secret": secret,  # Only returned on creation
            "created_at": webhook.created_at.isoformat() if webhook.created_at else None,
        }

    def get_webhook(self, webhook_id: str, tenant_id: str) -> Optional[dict[str, Any]]:
        """Get webhook by ID (scoped to tenant)."""
        from database import Webhook

        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id,
        ).first()

        if not webhook:
            return None

        return {
            "id": webhook.id,
            "url": webhook.url,
            "events": webhook.events,
            "is_active": webhook.is_active,
            "created_at": webhook.created_at.isoformat() if webhook.created_at else None,
            "updated_at": webhook.updated_at.isoformat() if webhook.updated_at else None,
        }

    def list_webhooks(self, tenant_id: str) -> list[dict[str, Any]]:
        """List all webhooks for a tenant."""
        from database import Webhook

        webhooks = self.db.query(Webhook).filter(
            Webhook.tenant_id == tenant_id,
        ).order_by(Webhook.created_at.desc()).all()

        return [
            {
                "id": w.id,
                "url": w.url,
                "events": w.events,
                "is_active": w.is_active,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in webhooks
        ]

    def delete_webhook(self, webhook_id: str, tenant_id: str) -> bool:
        """Delete a webhook (scoped to tenant)."""
        from database import Webhook

        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id,
        ).first()

        if not webhook:
            return False

        self.db.delete(webhook)
        self.db.commit()

        logger.info(f"Deleted webhook {webhook_id}")
        return True

    def get_deliveries(
        self,
        webhook_id: str,
        tenant_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get delivery history for a webhook."""
        from database import Webhook, WebhookDelivery

        # Verify webhook belongs to tenant
        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id,
        ).first()

        if not webhook:
            return []

        deliveries = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id,
        ).order_by(WebhookDelivery.created_at.desc()).limit(limit).all()

        return [
            {
                "id": d.id,
                "event_type": d.event_type,
                "status": d.status,
                "attempts": d.attempts,
                "response_code": d.response_code,
                "error_message": d.error_message,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            }
            for d in deliveries
        ]

    async def fire_event(
        self,
        tenant_id: str,
        event: WebhookEvent,
        payload: dict[str, Any],
    ) -> list[str]:
        """
        Fire an event to all subscribed webhooks.

        Args:
            tenant_id: Tenant ID
            event: Event type
            payload: Event payload

        Returns:
            List of delivery IDs created
        """
        from database import Webhook

        webhooks = self.db.query(Webhook).filter(
            Webhook.tenant_id == tenant_id,
            Webhook.is_active,
        ).all()

        delivery_ids = []

        for webhook in webhooks:
            if event.value in webhook.events:
                delivery_id = await self._create_and_deliver(webhook, event.value, payload)
                if delivery_id:
                    delivery_ids.append(delivery_id)

        return delivery_ids

    async def _create_and_deliver(
        self,
        webhook: Any,
        event_type: str,
        payload: dict[str, Any],
    ) -> Optional[str]:
        """Create delivery record and attempt delivery."""
        from database import WebhookDelivery
        from packages.seo_health_report.metrics import metrics

        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
            status="pending",
            attempts=0,
        )

        self.db.add(delivery)
        self.db.commit()

        # Attempt delivery
        success = await self._deliver(delivery, webhook)

        if success:
            metrics.inc_counter("webhook_deliveries_total", labels={"status": "success"})
        else:
            metrics.inc_counter("webhook_deliveries_total", labels={"status": "pending_retry"})

        return delivery.id

    async def _deliver(self, delivery: Any, webhook: Any) -> bool:
        """
        Attempt to deliver a webhook.

        Args:
            delivery: WebhookDelivery record
            webhook: Webhook record

        Returns:
            True if delivered successfully
        """
        from packages.seo_health_report.metrics import metrics

        delivery.attempts += 1

        # Build payload with event envelope
        full_payload = {
            "event": delivery.event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "delivery_id": delivery.id,
            "data": delivery.payload,
        }

        payload_json = json.dumps(full_payload)
        signature = sign_payload(payload_json, webhook.secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery": delivery.id,
            "User-Agent": "SEO-Health-Report-Webhook/1.0",
        }

        try:
            client = await self._get_client()
            response = await client.post(
                webhook.url,
                content=payload_json,
                headers=headers,
            )

            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000] if response.text else None

            if response.status_code < 400:
                delivery.status = "delivered"
                delivery.delivered_at = datetime.utcnow()
                delivery.error_message = None
                self.db.commit()

                logger.info(f"Webhook delivered: {delivery.id} to {webhook.url}")
                return True
            else:
                delivery.error_message = f"HTTP {response.status_code}"

        except httpx.TimeoutException:
            delivery.error_message = "Request timeout"
        except httpx.RequestError as e:
            delivery.error_message = str(e)[:500]
        except Exception as e:
            delivery.error_message = f"Unexpected error: {str(e)[:500]}"
            logger.exception(f"Webhook delivery failed: {delivery.id}")

        # Schedule retry if under max attempts
        if delivery.attempts < MAX_RETRIES:
            delay = RETRY_DELAYS[delivery.attempts - 1]
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
            delivery.status = "pending"
            logger.info(f"Webhook {delivery.id} scheduled for retry in {delay}s")
        else:
            delivery.status = "failed"
            metrics.inc_counter("webhook_deliveries_total", labels={"status": "failed"})
            logger.warning(f"Webhook {delivery.id} failed after {MAX_RETRIES} attempts")

        self.db.commit()
        return False

    async def process_pending_retries(self) -> int:
        """
        Process webhooks that are due for retry.

        Returns:
            Number of deliveries processed
        """
        from database import Webhook, WebhookDelivery

        pending = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.status == "pending",
            WebhookDelivery.next_retry_at <= datetime.utcnow(),
        ).limit(100).all()

        count = 0
        for delivery in pending:
            webhook = self.db.query(Webhook).filter(
                Webhook.id == delivery.webhook_id,
            ).first()

            if webhook and webhook.is_active:
                await self._deliver(delivery, webhook)
                count += 1

        return count

    async def send_test_event(self, webhook_id: str, tenant_id: str) -> dict[str, Any]:
        """Send a test event to verify webhook configuration."""
        from database import Webhook

        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id,
        ).first()

        if not webhook:
            raise ValueError("Webhook not found")

        test_payload = {
            "message": "This is a test webhook event",
            "webhook_id": webhook_id,
        }

        delivery_id = await self._create_and_deliver(
            webhook,
            "test",
            test_payload,
        )

        from database import WebhookDelivery
        delivery = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.id == delivery_id,
        ).first()

        return {
            "delivery_id": delivery_id,
            "status": delivery.status if delivery else "unknown",
            "response_code": delivery.response_code if delivery else None,
            "error_message": delivery.error_message if delivery else None,
        }
