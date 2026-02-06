"""Pydantic models for the SEO Health SDK."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditStatus(str, Enum):
    """Status of an audit."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditTier(str, Enum):
    """Tier of an audit report."""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class TokenResponse(BaseModel):
    """Response from login/register endpoints."""

    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None


class AuditRequest(BaseModel):
    """Request to create a new audit."""

    url: str
    company_name: str
    tier: AuditTier = AuditTier.FREE
    webhook_url: Optional[str] = None
    options: Optional[dict[str, Any]] = None


class ScoreBreakdown(BaseModel):
    """Score breakdown for audit results."""

    technical: float = Field(ge=0, le=100)
    content: float = Field(ge=0, le=100)
    ai_visibility: float = Field(ge=0, le=100)
    overall: float = Field(ge=0, le=100)


class AuditResponse(BaseModel):
    """Response when creating an audit."""

    id: str
    url: str
    company_name: str
    status: AuditStatus
    tier: AuditTier
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class AuditResult(BaseModel):
    """Full audit result."""

    id: str
    url: str
    company_name: str
    status: AuditStatus
    tier: AuditTier
    created_at: datetime
    completed_at: Optional[datetime] = None
    scores: Optional[ScoreBreakdown] = None
    technical_audit: Optional[dict[str, Any]] = None
    content_audit: Optional[dict[str, Any]] = None
    ai_visibility_audit: Optional[dict[str, Any]] = None
    recommendations: Optional[list[dict[str, Any]]] = None
    report_url: Optional[str] = None
    pdf_url: Optional[str] = None


class WebhookEvent(str, Enum):
    """Webhook event types."""

    AUDIT_CREATED = "audit.created"
    AUDIT_COMPLETED = "audit.completed"
    AUDIT_FAILED = "audit.failed"


class Webhook(BaseModel):
    """Webhook configuration."""

    id: str
    url: str
    events: list[WebhookEvent]
    secret: Optional[str] = None
    active: bool = True
    created_at: datetime


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""

    id: str
    webhook_id: str
    event: WebhookEvent
    payload: dict[str, Any]
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    success: bool = False


class Branding(BaseModel):
    """Branding configuration."""

    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    company_name: Optional[str] = None
    footer_text: Optional[str] = None
    custom_css: Optional[str] = None


class BrandingUpdate(BaseModel):
    """Branding update request."""

    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    company_name: Optional[str] = None
    footer_text: Optional[str] = None
    custom_css: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated API response."""

    items: list[Any]
    total: int
    page: int
    per_page: int
    pages: int


__all__ = [
    "AuditStatus",
    "AuditTier",
    "TokenResponse",
    "AuditRequest",
    "ScoreBreakdown",
    "AuditResponse",
    "AuditResult",
    "WebhookEvent",
    "Webhook",
    "WebhookDelivery",
    "Branding",
    "BrandingUpdate",
    "PaginatedResponse",
]
