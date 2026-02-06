"""
SEO Health SDK - Python client for the SEO Health Report API.

Usage:
    from packages.seo_health_sdk import SEOHealthClient, AsyncSEOHealthClient

    # Synchronous usage
    client = SEOHealthClient("https://api.seohealth.com", api_key="your-key")
    audit = client.create_audit("https://example.com", "Example Corp")

    # Async usage
    async with AsyncSEOHealthClient("https://api.seohealth.com", api_key="your-key") as client:
        audit = await client.create_audit("https://example.com", "Example Corp")
"""

from .auth import RefreshableTokenAuth, TokenAuth
from .client import AsyncSEOHealthClient, SEOHealthClient
from .exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    SEOHealthError,
    ValidationError,
)
from .models import (
    AuditRequest,
    AuditResponse,
    AuditResult,
    AuditStatus,
    AuditTier,
    Branding,
    BrandingUpdate,
    PaginatedResponse,
    ScoreBreakdown,
    TokenResponse,
    Webhook,
    WebhookDelivery,
    WebhookEvent,
)

__version__ = "0.1.0"

__all__ = [
    # Clients
    "SEOHealthClient",
    "AsyncSEOHealthClient",
    # Auth
    "TokenAuth",
    "RefreshableTokenAuth",
    # Models
    "AuditStatus",
    "AuditTier",
    "TokenResponse",
    "AuditRequest",
    "AuditResponse",
    "AuditResult",
    "ScoreBreakdown",
    "WebhookEvent",
    "Webhook",
    "WebhookDelivery",
    "Branding",
    "BrandingUpdate",
    "PaginatedResponse",
    # Exceptions
    "SEOHealthError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "APIError",
]
