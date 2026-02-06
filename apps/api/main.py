#!/usr/bin/env python3
"""
SEO Health Report API Server

Production-ready API with database persistence, authentication, and payments.
"""

import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "seo-health-report"))
sys.path.insert(0, str(project_root.parent.parent))  # Add root for packages

# Import configuration and validate at startup
from packages.config import get_settings, validate_startup

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate configuration at startup
# This will exit with a clear error message if configuration is invalid
try:
    validation_result = validate_startup(
        require_database=True,
        require_auth=True,
        exit_on_error=False,  # Don't exit, we'll handle gracefully for dev
    )
    logger.info(f"Configuration validated for environment: {validation_result['environment']}")
except Exception as e:
    logger.warning(f"Configuration validation warning: {e}")
    # Continue anyway for development, but log the warning

# Get settings singleton
settings = get_settings()

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from apps.api.middleware.rate_limit import RateLimitHeadersMiddleware
from apps.api.openapi import (
    TAGS_METADATA,
    get_custom_openapi_function,
)
from database import get_db, init_db
from rate_limiter import get_rate_limit_status

# Import dashboard router
try:
    from apps.dashboard.routes import router as dashboard_router
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    logger.warning("Dashboard module not available")

# Import webhooks router
try:
    from apps.api.routers.webhooks import router as webhooks_router
    WEBHOOKS_AVAILABLE = True
except ImportError:
    WEBHOOKS_AVAILABLE = False
    logger.warning("Webhooks module not available")

# Import branding router
try:
    from apps.api.routers.branding import router as branding_router
    BRANDING_AVAILABLE = True
except ImportError:
    BRANDING_AVAILABLE = False
    logger.warning("Branding module not available")

# Import competitors router
try:
    from apps.api.routers.competitors import router as competitors_router
    COMPETITORS_AVAILABLE = True
except ImportError:
    COMPETITORS_AVAILABLE = False
    logger.warning("Competitors module not available")

# Import auth router
try:
    from apps.api.routers.auth_routes import router as auth_router
    AUTH_ROUTER_AVAILABLE = True
except ImportError:
    AUTH_ROUTER_AVAILABLE = False
    logger.warning("Auth router module not available")

# Import payments router
try:
    from apps.api.routers.payments import router as payments_router
    PAYMENTS_AVAILABLE = True
except ImportError:
    PAYMENTS_AVAILABLE = False
    logger.warning("Payments router module not available")

# Import admin router
try:
    from apps.admin.routes import router as admin_router
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False
    logger.warning("Admin module not available")

# Import audits router
try:
    from apps.api.routers.audits import router as audits_router
    AUDITS_AVAILABLE = True
except ImportError:
    AUDITS_AVAILABLE = False
    logger.warning("Audits module not available")

# Initialize database on startup
init_db()

app = FastAPI(
    title="SEO Health Report API",
    description="Run comprehensive SEO audits with AI visibility analysis",
    version="2.0.0",
    openapi_tags=TAGS_METADATA,
)

# Set custom OpenAPI schema
app.openapi = get_custom_openapi_function(app)


# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitHeadersMiddleware, default_tier="default", enabled=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:3000",
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount dashboard router if available
if DASHBOARD_AVAILABLE:
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
    dashboard_static_dir = Path(__file__).parent.parent / "dashboard" / "static"
    if dashboard_static_dir.exists():
        app.mount("/dashboard/static", StaticFiles(directory=str(dashboard_static_dir)), name="dashboard_static")
        logger.info("Dashboard static files mounted at /dashboard/static")
    shared_css_dir = Path(__file__).parent.parent / "shared-styles" / "dist"
    if shared_css_dir.exists():
        app.mount("/static/css", StaticFiles(directory=str(shared_css_dir)), name="shared_css")
        logger.info("Shared CSS mounted at /static/css")
    logger.info("Dashboard mounted at /dashboard")

# Mount webhooks router if available
if WEBHOOKS_AVAILABLE:
    app.include_router(webhooks_router)
    logger.info("Webhooks API mounted at /webhooks")

# Mount branding router if available
if BRANDING_AVAILABLE:
    app.include_router(branding_router)
    logger.info("Branding API mounted at /tenant/branding")

# Mount competitors router if available
if COMPETITORS_AVAILABLE:
    app.include_router(competitors_router)
    logger.info("Competitors API mounted at /competitors")

# Mount auth router if available
if AUTH_ROUTER_AVAILABLE:
    app.include_router(auth_router)
    logger.info("Auth API mounted at /auth")

# Mount admin router if available
if ADMIN_AVAILABLE:
    app.include_router(admin_router, prefix="/admin", tags=["admin"])
    logger.info("Admin dashboard mounted at /admin")

# Mount audits router if available
if AUDITS_AVAILABLE:
    app.include_router(audits_router)
    logger.info("Audits API mounted")

# Mount payments router if available
if PAYMENTS_AVAILABLE:
    app.include_router(payments_router)
    logger.info("Payments API mounted")


# --- Health ---

@app.get(
    "/",
    tags=["system"],
    summary="API root",
    description="Get API info and version."
)
async def root():
    return {"message": "SEO Health Report API", "version": "2.0.0"}


@app.get(
    "/health",
    tags=["system"],
    summary="Health check",
    description="Check API and database health status.",
    responses={
        200: {
            "description": "Health status",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Healthy",
                            "value": {"status": "healthy", "database": "connected"}
                        },
                        "degraded": {
                            "summary": "Degraded",
                            "value": {"status": "degraded", "database": "disconnected"}
                        }
                    }
                }
            }
        }
    }
)
async def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "disconnected"}


@app.get(
    "/rate-limit",
    tags=["system"],
    summary="Rate limit status",
    description="Get current rate limit status for your client IP.",
    responses={
        200: {
            "description": "Rate limit status",
            "content": {
                "application/json": {
                    "example": {
                        "limit": 100,
                        "remaining": 95,
                        "reset": 1705320000
                    }
                }
            }
        }
    }
)
async def rate_limit_status(request: Request):
    """Get current rate limit status for client."""
    return get_rate_limit_status(request)



# --- URL Validation ---

@app.post(
    "/validate-url",
    tags=["system"],
    summary="Validate URL",
    description="Validate and auto-correct a URL format before submitting an audit.",
    responses={
        200: {
            "description": "Validation result",
            "content": {
                "application/json": {
                    "example": {
                        "validation": {
                            "original": "example.com",
                            "corrected": "https://www.example.com",
                            "isValid": True,
                            "corrections": ["Added HTTPS protocol", "Added www subdomain"]
                        }
                    }
                }
            }
        }
    }
)
async def validate_url(request: dict):
    """Validate and correct URL format."""
    url = request.get("url", "").strip()
    corrections = []

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
        corrections.append("Added HTTPS protocol")

    if url.count(".") == 1 and "www." not in url:
        url = url.replace("://", "://www.")
        corrections.append("Added www subdomain")

    is_valid = url.startswith(("http://", "https://")) and "." in url

    return {"validation": {"original": request.get("url", ""), "corrected": url, "isValid": is_valid, "corrections": corrections}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
