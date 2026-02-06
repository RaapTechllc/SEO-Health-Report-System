"""Audit management routes."""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.openapi import (
    AUDIT_FULL_EXAMPLE,
    AUDIT_REQUEST_EXAMPLE,
    AUDIT_RESPONSE_EXAMPLE,
    AUDIT_STATUS_EXAMPLE,
    ERROR_RESPONSES,
)
from auth import get_current_user, require_auth
from database import Audit, User, get_db
from packages.seo_health_report.metrics import metrics
from packages.seo_health_report.progress import get_audit_progress
from packages.seo_health_report.scripts.calculate_scores import calculate_composite_score
from packages.seo_health_report.scripts.idempotency import compute_idempotency_key
from packages.seo_health_report.scripts.orchestrate import run_full_audit
from rate_limiter import check_rate_limit

if TYPE_CHECKING:
    from packages.seo_health_report.webhooks import WebhookEvent

logger = logging.getLogger(__name__)

# Import webhook service for audit completion events
try:
    from packages.seo_health_report.webhooks import WebhookEvent, WebhookService
    WEBHOOKS_SERVICE_AVAILABLE = True
except ImportError:
    WEBHOOKS_SERVICE_AVAILABLE = False
    logger.warning("Webhook service not available")

router = APIRouter(tags=["audits"])

# Project root for report storage
project_root = Path(__file__).parent.parent

# Tier mapping from legacy to new tier system
TIER_MAPPING = {
    # New tier names (preferred)
    "low": "low",
    "medium": "medium",
    "high": "high",
    # Legacy tier names (backwards compatible)
    "basic": "low",
    "pro": "medium",
    "enterprise": "high",
    # Friendly aliases from frontend
    "budget": "low",
    "balanced": "medium",
    "premium": "high",
}

VALID_TIERS = list(TIER_MAPPING.keys())


# --- Models ---

class AuditRequest(BaseModel):
    """Request model for starting a new SEO audit."""
    url: str
    company_name: str
    keywords: list[str] = []
    competitors: list[str] = []
    tier: str = "low"  # Default to LOW tier (Budget Watchdog)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        if "." not in v:
            raise ValueError("Invalid URL format")
        return v

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v):
        v_lower = v.lower().strip()
        if v_lower not in VALID_TIERS:
            raise ValueError(f"Tier must be one of: {', '.join(VALID_TIERS)}")
        return TIER_MAPPING[v_lower]

    class Config:
        json_schema_extra = {"example": AUDIT_REQUEST_EXAMPLE}


class AuditResponse(BaseModel):
    """Response model for audit creation."""
    audit_id: str
    status: str
    url: str
    company_name: str

    class Config:
        json_schema_extra = {"example": AUDIT_RESPONSE_EXAMPLE}


# --- Helper Functions ---

async def fire_audit_webhook(
    db: Session,
    audit_id: str,
    tenant_id: Optional[str],
    event: "WebhookEvent",
    audit_data: dict,
) -> None:
    """
    Fire a webhook event for audit completion/failure.

    Args:
        db: Database session
        audit_id: Audit ID
        tenant_id: Tenant ID (if multi-tenant)
        event: WebhookEvent.AUDIT_COMPLETED or AUDIT_FAILED
        audit_data: Audit result data to include in payload
    """
    if not WEBHOOKS_SERVICE_AVAILABLE:
        return

    if not tenant_id:
        logger.debug(f"No tenant_id for audit {audit_id}, skipping webhook")
        return

    try:
        service = WebhookService(db)
        payload = {
            "audit_id": audit_id,
            "url": audit_data.get("url"),
            "company_name": audit_data.get("company_name"),
            "tier": audit_data.get("tier"),
            "overall_score": audit_data.get("overall_score"),
            "grade": audit_data.get("grade"),
            "completed_at": audit_data.get("completed_at"),
        }

        if event == WebhookEvent.AUDIT_FAILED:
            payload["error"] = audit_data.get("error")

        delivery_ids = await service.fire_event(
            tenant_id=tenant_id,
            event=event,
            payload=payload,
        )

        if delivery_ids:
            logger.info(f"Fired {event.value} webhook for audit {audit_id}: {len(delivery_ids)} deliveries")

        await service.close()
    except Exception as e:
        logger.error(f"Failed to fire webhook for audit {audit_id}: {e}")


def enqueue_audit_job(
    db: Session,
    audit_id: str,
    tenant_id: str,
    url: str,
    options: dict,
    job_type: str = "hello_audit"
) -> str:
    """Create job record for async processing."""
    job_id = str(uuid.uuid4())
    idempotency_key = compute_idempotency_key(tenant_id or "default", url, options)

    existing = db.execute(
        text("SELECT audit_id FROM audit_jobs WHERE idempotency_key = :key"),
        {"key": idempotency_key}
    ).fetchone()

    if existing:
        return existing[0]

    db.execute(
        text('''
            INSERT INTO audit_jobs
            (job_id, tenant_id, audit_id, status, idempotency_key, payload_json, queued_at)
            VALUES (:job_id, :tenant_id, :audit_id, 'queued', :idempotency_key, :payload, CURRENT_TIMESTAMP)
        '''),
        {
            "job_id": job_id,
            "tenant_id": tenant_id or "default",
            "audit_id": audit_id,
            "idempotency_key": idempotency_key,
            "payload": json.dumps({
                "url": url,
                "job_type": job_type,
                **options
            })
        }
    )
    db.commit()
    return audit_id


async def run_audit_task(
    audit_id: str,
    url: str,
    company_name: str,
    keywords: list[str],
    competitors: list[str],
    tier: str,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Background task to run the audit. LEGACY: kept for tests, prefer job queue."""
    import time
    start_time = time.perf_counter()

    metrics.inc_gauge("active_audits")

    db = next(get_db())
    status = "failed"
    audit_data = {}
    try:
        result = await run_full_audit(
            target_url=url, company_name=company_name,
            primary_keywords=keywords, competitor_urls=competitors,
            tier=tier
        )

        scores = calculate_composite_score(result)
        result["overall_score"] = scores.get("overall_score", 0)
        result["grade"] = scores.get("grade", "N/A")
        result["component_scores"] = scores.get("component_scores", {})

        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        report_path = reports_dir / f"{audit_id}.json"
        with open(report_path, "w") as f:
            json.dump(result, f, indent=2, default=str)

        audit = db.query(Audit).filter(Audit.id == audit_id).first()
        if audit:
            audit.status = "completed"
            audit.overall_score = result["overall_score"]
            audit.grade = result["grade"]
            audit.result = result
            audit.report_path = str(report_path)
            audit.completed_at = datetime.utcnow()
            db.commit()

            # Prepare webhook payload
            audit_data = {
                "url": url,
                "company_name": company_name,
                "tier": tier,
                "overall_score": result["overall_score"],
                "grade": result["grade"],
                "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
            }

        status = "completed"

    except Exception as e:
        audit = db.query(Audit).filter(Audit.id == audit_id).first()
        if audit:
            audit.status = "failed"
            audit.result = {"error": str(e)}
            db.commit()

            # Prepare webhook payload for failure
            audit_data = {
                "url": url,
                "company_name": company_name,
                "tier": tier,
                "error": str(e),
            }
        status = "failed"
    finally:
        metrics.dec_gauge("active_audits")

        duration = time.perf_counter() - start_time
        metrics.inc_counter("audit_total", labels={"tier": tier, "status": status})
        metrics.observe_histogram("audit_duration_seconds", duration, labels={"tier": tier})

        # Fire webhook event
        if WEBHOOKS_SERVICE_AVAILABLE and tenant_id and audit_data:
            try:
                event = WebhookEvent.AUDIT_COMPLETED if status == "completed" else WebhookEvent.AUDIT_FAILED
                await fire_audit_webhook(db, audit_id, tenant_id, event, audit_data)
            except Exception as e:
                logger.error(f"Failed to fire webhook for audit {audit_id}: {e}")

        db.close()


# --- Routes ---

@router.post(
    "/audit",
    response_model=AuditResponse,
    summary="Start SEO audit",
    description="Start a new SEO audit for the specified URL. The audit runs asynchronously and can be tracked via the audit ID.",
    responses={
        200: {
            "description": "Audit queued successfully",
            "content": {
                "application/json": {
                    "example": AUDIT_RESPONSE_EXAMPLE
                }
            }
        },
        400: ERROR_RESPONSES[400],
        422: ERROR_RESPONSES[422],
        429: ERROR_RESPONSES[429],
    }
)
async def start_audit(
    request: AuditRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Start a new SEO audit (async via background task)."""
    check_rate_limit(http_request)

    audit_id = f"audit_{uuid.uuid4().hex[:12]}"

    audit = Audit(
        id=audit_id,
        url=request.url,
        company_name=request.company_name,
        tier=request.tier,
        status="queued",
        user_id=user.id,
        tenant_id=user.tenant_id
    )
    db.add(audit)
    db.commit()

    # Run audit in background task (same process) for dev simplicity
    background_tasks.add_task(
        run_audit_task,
        audit_id=audit_id,
        url=request.url,
        company_name=request.company_name,
        keywords=request.keywords,
        competitors=request.competitors,
        tier=request.tier,
        tenant_id=user.tenant_id,
        user_id=user.id
    )

    # Legacy job queue code commented out for now
    # options = {
    #     "company_name": request.company_name,
    #     # ...
    # }
    # result_audit_id = enqueue_audit_job(...)

    return AuditResponse(
        audit_id=audit_id,
        status="queued",
        url=request.url,
        company_name=request.company_name
    )


@router.post(
    "/audit/hello",
    response_model=AuditResponse,
    summary="Start public SEO audit (free tier)",
    description="Start a new SEO audit without authentication. Limited to low tier with max 3 keywords and no competitors.",
    responses={
        200: {
            "description": "Audit queued successfully",
            "content": {
                "application/json": {
                    "example": AUDIT_RESPONSE_EXAMPLE
                }
            }
        },
        400: ERROR_RESPONSES[400],
        422: ERROR_RESPONSES[422],
        429: ERROR_RESPONSES[429],
    }
)
async def start_public_audit(
    request: AuditRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new SEO audit (public endpoint, no auth required)."""
    check_rate_limit(http_request)

    # Force free-tier limitations
    tier = "low"
    keywords = request.keywords[:3] if request.keywords else []
    competitors = []

    audit_id = f"audit_{uuid.uuid4().hex[:12]}"

    audit = Audit(
        id=audit_id,
        url=request.url,
        company_name=request.company_name,
        tier=tier,
        status="queued"
    )
    db.add(audit)
    db.commit()

    # Run audit in background task (same process) for dev simplicity
    background_tasks.add_task(
        run_audit_task,
        audit_id=audit_id,
        url=request.url,
        company_name=request.company_name,
        keywords=keywords,
        competitors=competitors,
        tier=tier,
        tenant_id=None,
        user_id=None
    )

    return AuditResponse(
        audit_id=audit_id,
        status="queued",
        url=request.url,
        company_name=request.company_name
    )


@router.get(
    "/audit/{audit_id}",
    summary="Get audit status",
    description="Get the current status and summary results of an audit.",
    responses={
        200: {
            "description": "Audit status",
            "content": {
                "application/json": {
                    "example": AUDIT_STATUS_EXAMPLE
                }
            }
        },
        404: ERROR_RESPONSES[404],
    }
)
async def get_audit(
    audit_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    """Get audit status and results."""
    query = db.query(Audit).filter(Audit.id == audit_id)

    # If user is authenticated and has tenant_id, scope to their tenant
    if user and user.tenant_id:
        query = query.filter(Audit.tenant_id == user.tenant_id)

    audit = query.first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    return {
        "audit_id": audit.id,
        "status": audit.status,
        "url": audit.url,
        "company_name": audit.company_name,
        "tier": audit.tier,
        "overall_score": audit.overall_score,
        "grade": audit.grade,
        "created_at": audit.created_at.isoformat() if audit.created_at else None,
        "completed_at": audit.completed_at.isoformat() if audit.completed_at else None
    }


@router.get(
    "/audit/{audit_id}/full",
    summary="Get full audit results",
    description="Get complete audit data including detailed results and report download URLs.",
    responses={
        200: {
            "description": "Full audit data",
            "content": {
                "application/json": {
                    "example": AUDIT_FULL_EXAMPLE
                }
            }
        },
        404: ERROR_RESPONSES[404],
    }
)
async def get_full_audit(audit_id: str, db: Session = Depends(get_db)):
    """Get full audit data including result and report URLs."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    response = {
        "audit_id": audit.id,
        "status": audit.status,
        "url": audit.url,
        "company_name": audit.company_name,
        "tier": audit.tier,
        "overall_score": audit.overall_score,
        "grade": audit.grade,
        "created_at": audit.created_at.isoformat() if audit.created_at else None,
        "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
    }

    # Add result if completed
    if audit.status == "completed" and audit.result:
        response["result"] = audit.result

    # Add report URLs
    if hasattr(audit, 'report_html_path') and audit.report_html_path:
        response["report_html_url"] = f"/audits/{audit_id}/report/html"
    if hasattr(audit, 'report_pdf_path') and audit.report_pdf_path:
        response["report_pdf_url"] = f"/audits/{audit_id}/report/pdf"

    return response


@router.get(
    "/audits/{audit_id}/events",
    summary="Get audit progress events",
    description="Get real-time progress events for an in-progress audit.",
    responses={
        200: {
            "description": "Audit events",
            "content": {
                "application/json": {
                    "example": {
                        "audit_id": "audit_abc123def456",
                        "events": [
                            {"event_type": "started", "message": "Audit started", "progress_pct": 0, "timestamp": "2024-01-15T10:30:00Z"},
                            {"event_type": "crawling", "message": "Crawling pages...", "progress_pct": 25, "timestamp": "2024-01-15T10:30:30Z"}
                        ]
                    }
                }
            }
        },
    }
)
async def get_audit_events(audit_id: str, db: Session = Depends(get_db)):
    """Get progress events for an audit."""
    events = db.execute(
        text('''
            SELECT event_type, message, progress_pct, created_at
            FROM audit_progress_events
            WHERE audit_id = :audit_id
            ORDER BY created_at
        '''),
        {"audit_id": audit_id}
    ).fetchall()

    return {
        "audit_id": audit_id,
        "events": [
            {
                "event_type": e[0],
                "message": e[1],
                "progress_pct": e[2],
                "timestamp": e[3].isoformat() if e[3] else None
            }
            for e in events
        ]
    }


@router.get(
    "/audit/{audit_id}/progress",
    summary="Get audit progress",
    description="Get optimized progress data with module-level breakdown and time estimates for UI polling.",
    responses={
        200: {
            "description": "Progress data",
            "content": {
                "application/json": {
                    "example": {
                        "audit_id": "aud_abc123",
                        "overall_status": "running",
                        "overall_progress_pct": 45,
                        "modules": [
                            {"module_name": "technical", "status": "completed", "progress_pct": 100, "started_at": "2025-01-18T10:00:00", "completed_at": "2025-01-18T10:01:30", "error_message": None},
                            {"module_name": "content", "status": "running", "progress_pct": 35, "started_at": "2025-01-18T10:01:30", "completed_at": None, "error_message": None},
                            {"module_name": "ai", "status": "pending", "progress_pct": 0, "started_at": None, "completed_at": None, "error_message": None}
                        ],
                        "started_at": "2025-01-18T10:00:00",
                        "estimated_completion": "2025-01-18T10:05:00",
                        "elapsed_seconds": 120
                    }
                }
            }
        },
        404: ERROR_RESPONSES[404],
    }
)
async def get_audit_progress_endpoint(audit_id: str, db: Session = Depends(get_db)):
    """Get optimized progress data for UI polling."""
    progress = get_audit_progress(db, audit_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Audit not found")
    return progress.to_dict()


@router.get(
    "/audits/{audit_id}/report/{format}",
    summary="Download audit report",
    description="Download the audit report in HTML or PDF format.",
    responses={
        200: {"description": "Report file"},
        400: ERROR_RESPONSES[400],
        404: ERROR_RESPONSES[404],
    }
)
async def get_audit_report_by_format(
    audit_id: str,
    format: str,
    db: Session = Depends(get_db)
):
    """Download audit report in specified format."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if format == "html":
        path = getattr(audit, 'report_html_path', None)
        media_type = "text/html"
        filename = f"SEO_Report_{audit_id}.html"
    elif format == "pdf":
        path = getattr(audit, 'report_pdf_path', None)
        media_type = "application/pdf"
        filename = f"SEO_Report_{audit_id}.pdf"
    else:
        raise HTTPException(status_code=400, detail="Format must be 'html' or 'pdf'")

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"{format.upper()} report not available")

    return FileResponse(path, media_type=media_type, filename=filename)


@router.get(
    "/audit/{audit_id}/pdf",
    summary="Get PDF report",
    description="Generate and download the premium PDF report for a completed audit.",
    responses={
        200: {"description": "PDF file"},
        400: ERROR_RESPONSES[400],
        404: ERROR_RESPONSES[404],
    }
)
async def get_audit_pdf(audit_id: str, db: Session = Depends(get_db)):
    """Generate and return PDF report."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != "completed":
        raise HTTPException(status_code=400, detail=f"Audit status: {audit.status}")

    json_path = audit.report_path
    if not json_path or not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    pdf_path = json_path.replace(".json", "_PREMIUM.pdf")
    if not os.path.exists(pdf_path):
        from packages.seo_health_report.premium_report import generate_premium_report
        generate_premium_report(json_path, pdf_path)

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"SEO_Report_{audit_id}.pdf")


@router.get(
    "/audits",
    summary="List audits",
    description="Get a list of all audits (most recent first, limited to 100).",
    responses={
        200: {
            "description": "List of audits",
            "content": {
                "application/json": {
                    "example": {
                        "audits": [AUDIT_STATUS_EXAMPLE]
                    }
                }
            }
        }
    }
)
async def list_audits(
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List all audits."""
    query = db.query(Audit)

    # Filter by tenant_id if user has one
    if user.tenant_id:
        query = query.filter(Audit.tenant_id == user.tenant_id)

    audits = query.order_by(Audit.created_at.desc()).limit(100).all()
    return {
        "audits": [{
            "audit_id": a.id, "status": a.status, "url": a.url,
            "company_name": a.company_name, "overall_score": a.overall_score,
            "grade": a.grade, "tier": a.tier,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in audits]
    }
