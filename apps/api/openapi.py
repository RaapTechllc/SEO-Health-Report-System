"""
OpenAPI Schema Enhancement for SEO Health Report API

Provides comprehensive OpenAPI documentation with:
- Detailed API description
- Security scheme documentation
- Response examples
- Error response models
"""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field

# --- API Description ---

API_DESCRIPTION = """
# SEO Health Report API

Comprehensive SEO audit platform with AI visibility analysis, technical SEO checks,
and content authority assessment.

## Overview

The SEO Health Report API enables you to:
- **Run SEO Audits**: Analyze websites for technical SEO, content quality, and AI visibility
- **Track Competitors**: Monitor competitor SEO performance over time
- **Generate Reports**: Create detailed PDF and HTML reports with actionable insights
- **Webhook Integration**: Receive real-time notifications when audits complete

## Authentication

All authenticated endpoints require a Bearer JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

To obtain a token:
1. Register at `POST /auth/register`
2. Or login at `POST /auth/login`

## Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| General API | 100 requests/minute |
| Audit Creation | 10 audits/hour |
| Report Generation | 20/hour |

Rate limit status is returned in response headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Audit Tiers

| Tier | Features |
|------|----------|
| **basic** | Technical SEO, basic content analysis |
| **pro** | + AI visibility audit, competitor comparison |
| **enterprise** | + Historical trends, white-label reports, API webhooks |

## Webhook Events

Subscribe to these events via the `/webhooks` endpoints:
- `audit.completed` - Audit finished successfully
- `audit.failed` - Audit encountered an error
- `competitor.alert` - Competitor score changed significantly

## Support

- Documentation: https://docs.seohealthreport.com
- Email: api-support@raaptech.com
"""


# --- Tags Metadata ---

TAGS_METADATA = [
    {
        "name": "authentication",
        "description": "User registration, login, and token management",
    },
    {
        "name": "audits",
        "description": "SEO audit creation, status tracking, and report retrieval",
    },
    {
        "name": "competitors",
        "description": "Competitor monitoring and tracking",
    },
    {
        "name": "payments",
        "description": "Stripe checkout and payment processing",
    },
    {
        "name": "webhooks",
        "description": "Webhook subscription management for event notifications",
    },
    {
        "name": "branding",
        "description": "White-label branding configuration for enterprise tenants",
    },
    {
        "name": "dashboard",
        "description": "Dashboard and analytics endpoints",
    },
    {
        "name": "system",
        "description": "Health checks, rate limits, and system status",
    },
]


# --- Error Response Models ---

class ErrorDetail(BaseModel):
    """Standard error detail structure."""
    detail: str = Field(..., description="Human-readable error message")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found"
            }
        }


class ValidationErrorDetail(BaseModel):
    """Validation error with field details."""
    detail: list = Field(..., description="List of validation errors")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "url"],
                        "msg": "Invalid URL format",
                        "type": "value_error"
                    }
                ]
            }
        }


# --- Common Response Examples ---

ERROR_RESPONSES = {
    400: {
        "description": "Bad Request - Invalid input or validation error",
        "content": {
            "application/json": {
                "examples": {
                    "validation_error": {
                        "summary": "Validation Error",
                        "value": {"detail": "Invalid URL format"}
                    },
                    "invalid_tier": {
                        "summary": "Invalid Tier",
                        "value": {"detail": "Tier must be basic, pro, or enterprise"}
                    }
                }
            }
        }
    },
    401: {
        "description": "Unauthorized - Missing or invalid authentication token",
        "content": {
            "application/json": {
                "examples": {
                    "missing_token": {
                        "summary": "Missing Token",
                        "value": {"detail": "Not authenticated"}
                    },
                    "invalid_token": {
                        "summary": "Invalid Token",
                        "value": {"detail": "Could not validate credentials"}
                    },
                    "expired_token": {
                        "summary": "Expired Token",
                        "value": {"detail": "Token has expired"}
                    }
                }
            }
        }
    },
    404: {
        "description": "Not Found - Resource does not exist",
        "content": {
            "application/json": {
                "examples": {
                    "audit_not_found": {
                        "summary": "Audit Not Found",
                        "value": {"detail": "Audit not found"}
                    },
                    "report_not_found": {
                        "summary": "Report Not Found",
                        "value": {"detail": "Report file not found"}
                    }
                }
            }
        }
    },
    422: {
        "description": "Validation Error - Request body validation failed",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "url"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    },
    429: {
        "description": "Too Many Requests - Rate limit exceeded",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Rate limit exceeded. Try again in 60 seconds."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error - Unexpected server error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An unexpected error occurred. Please try again later."
                }
            }
        }
    }
}


# --- Request/Response Examples ---

AUDIT_REQUEST_EXAMPLE = {
    "url": "https://example.com",
    "company_name": "Example Corp",
    "keywords": ["seo tools", "website audit", "search optimization"],
    "competitors": ["https://competitor1.com", "https://competitor2.com"],
    "tier": "pro"
}

AUDIT_RESPONSE_EXAMPLE = {
    "audit_id": "audit_abc123def456",
    "status": "queued",
    "url": "https://example.com",
    "company_name": "Example Corp"
}

AUDIT_STATUS_EXAMPLE = {
    "audit_id": "audit_abc123def456",
    "status": "completed",
    "url": "https://example.com",
    "company_name": "Example Corp",
    "tier": "pro",
    "overall_score": 78.5,
    "grade": "B+",
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:32:45Z"
}

AUDIT_FULL_EXAMPLE = {
    **AUDIT_STATUS_EXAMPLE,
    "result": {
        "technical_score": 82,
        "content_score": 75,
        "ai_visibility_score": 79,
        "issues": [
            {"severity": "high", "category": "performance", "message": "Page load time exceeds 3 seconds"},
            {"severity": "medium", "category": "meta", "message": "Missing meta description on 5 pages"}
        ]
    },
    "report_html_url": "/audits/audit_abc123def456/report/html",
    "report_pdf_url": "/audits/audit_abc123def456/report/pdf"
}

TOKEN_RESPONSE_EXAMPLE = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": "user_xyz789",
    "email": "user@example.com"
}

COMPETITOR_EXAMPLE = {
    "competitor_id": "comp_abc123",
    "url": "https://competitor.com",
    "company_name": "Competitor Inc",
    "monitoring_frequency": 3600,
    "alert_threshold": 10,
    "last_score": 72.5,
    "last_audit_at": "2024-01-15T08:00:00Z"
}

PRICING_EXAMPLE = {
    "tiers": {
        "basic": {
            "name": "Basic",
            "description": "Essential SEO analysis",
            "price": 29.00,
            "currency": "USD"
        },
        "pro": {
            "name": "Pro",
            "description": "Advanced SEO with AI visibility",
            "price": 79.00,
            "currency": "USD"
        },
        "enterprise": {
            "name": "Enterprise",
            "description": "Full suite with white-label reports",
            "price": 199.00,
            "currency": "USD"
        }
    }
}

WEBHOOK_EXAMPLE = {
    "webhook_id": "wh_abc123",
    "url": "https://yourapp.com/webhooks/seo",
    "events": ["audit.completed", "audit.failed"],
    "secret": "whsec_...",
    "active": True,
    "created_at": "2024-01-10T12:00:00Z"
}

BRANDING_EXAMPLE = {
    "tenant_id": "tenant_xyz",
    "company_name": "Acme SEO Services",
    "logo_url": "https://cdn.example.com/logo.png",
    "primary_color": "#2563eb",
    "secondary_color": "#1e40af",
    "accent_color": "#f59e0b",
    "custom_css": ".report-header { background: linear-gradient(...) }"
}


def create_custom_openapi(app: FastAPI) -> dict[str, Any]:
    """
    Create custom OpenAPI schema with enhanced documentation.

    Args:
        app: FastAPI application instance

    Returns:
        OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=API_DESCRIPTION,
        routes=app.routes,
        tags=TAGS_METADATA,
    )

    # Ensure components exists
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login or /auth/register"
        }
    }

    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "https://api.seohealthreport.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.seohealthreport.com",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development"
        }
    ]

    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "RaapTech API Support",
        "url": "https://raaptech.com/support",
        "email": "api-support@raaptech.com"
    }
    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://seohealthreport.com/terms"
    }

    # Add external docs link
    openapi_schema["externalDocs"] = {
        "description": "Full API Documentation",
        "url": "https://docs.seohealthreport.com"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_custom_openapi_function(app: FastAPI):
    """
    Returns a function that generates the custom OpenAPI schema.
    Use this to set app.openapi = get_custom_openapi_function(app)
    """
    def custom_openapi():
        return create_custom_openapi(app)
    return custom_openapi
