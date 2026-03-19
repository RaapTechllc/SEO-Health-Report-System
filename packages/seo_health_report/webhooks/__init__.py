"""
Webhook system for SEO Health Report.

Provides webhook subscription management, secure delivery with HMAC signing,
exponential backoff retries, and SSRF protection.

Usage:
    from packages.seo_health_report.webhooks import WebhookService, WebhookEvent

    service = WebhookService(db_session)

    # Fire an event
    await service.fire_event(
        tenant_id="tenant_123",
        event=WebhookEvent.AUDIT_COMPLETED,
        payload={"audit_id": "audit_456", "score": 85}
    )
"""

from .security import sign_payload, validate_webhook_url, verify_signature
from .service import WebhookEvent, WebhookService

__all__ = [
    "WebhookService",
    "WebhookEvent",
    "validate_webhook_url",
    "sign_payload",
    "verify_signature",
]
