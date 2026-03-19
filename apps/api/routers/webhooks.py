"""
Webhook management API endpoints.

Provides CRUD operations for webhook subscriptions.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from auth import require_auth
from database import User, get_db
from packages.seo_health_report.webhooks import WebhookEvent, WebhookService
from packages.seo_health_report.webhooks.security import SSRFError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class CreateWebhookRequest(BaseModel):
    url: str
    events: list[str]

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v):
        if not v:
            raise ValueError("At least one event type is required")
        valid_events = {e.value for e in WebhookEvent}
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event: {event}. Valid: {list(valid_events)}")
        return v


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str] = None


class WebhookCreatedResponse(WebhookResponse):
    secret: str


class DeliveryResponse(BaseModel):
    id: str
    event_type: str
    status: str
    attempts: int
    response_code: Optional[int]
    error_message: Optional[str]
    created_at: Optional[str]
    delivered_at: Optional[str]


class TestWebhookResponse(BaseModel):
    delivery_id: str
    status: str
    response_code: Optional[int]
    error_message: Optional[str]


@router.post("", response_model=WebhookCreatedResponse, status_code=201)
async def create_webhook(
    request: CreateWebhookRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Register a new webhook.

    The secret is only returned once on creation. Store it securely for
    signature verification.
    """
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = WebhookService(db)

    try:
        webhook = service.create_webhook(
            tenant_id=user.tenant_id,
            url=request.url,
            events=request.events,
        )
        return webhook
    except SSRFError as e:
        logger.warning("SSRF attempt blocked for webhook URL: %s", e)
        raise HTTPException(status_code=400, detail="Invalid webhook URL")
    except ValueError as e:
        logger.warning("Invalid webhook creation request: %s", e)
        raise HTTPException(status_code=400, detail="Invalid webhook configuration")


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """List all webhooks for the current tenant."""
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = WebhookService(db)
    return service.list_webhooks(user.tenant_id)


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get webhook details."""
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = WebhookService(db)
    webhook = service.get_webhook(webhook_id, user.tenant_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return webhook


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Delete a webhook."""
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = WebhookService(db)
    deleted = service.delete_webhook(webhook_id, user.tenant_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.get("/{webhook_id}/deliveries", response_model=list[DeliveryResponse])
async def get_deliveries(
    webhook_id: str,
    limit: int = 50,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get delivery history for a webhook."""
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = WebhookService(db)
    deliveries = service.get_deliveries(webhook_id, user.tenant_id, limit)

    if deliveries == []:
        # Check if webhook exists
        webhook = service.get_webhook(webhook_id, user.tenant_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

    return deliveries


@router.post("/{webhook_id}/test", response_model=TestWebhookResponse)
async def test_webhook(
    webhook_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Send a test event to verify webhook configuration."""
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = WebhookService(db)

    try:
        result = await service.send_test_event(webhook_id, user.tenant_id)
        return result
    except ValueError as e:
        logger.warning("Webhook test event failed: %s", e)
        raise HTTPException(status_code=404, detail="Webhook not found")
    finally:
        await service.close()
