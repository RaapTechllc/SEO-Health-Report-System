"""
Dashboard routes for SEO Health Report System.
Provides web UI for viewing audits and reports.
"""

import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Optional

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from apps.dashboard.auth import (
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    create_session,
    delete_session,
    get_current_dashboard_user,
    require_dashboard_auth,
    set_session_cookie,
    update_session_tenant,
)
from auth import authenticate_user, hash_password, verify_password
from database import Audit, Tenant, User, get_db
from packages.seo_health_report.quotas.service import QuotaExceededError, QuotaService
from packages.seo_health_report.scripts.idempotency import compute_idempotency_key

logger = logging.getLogger(__name__)

router = APIRouter()

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


class SwitchTenantRequest(BaseModel):
    tenant_id: str


def get_user_tenants(db: Session, user_id: str) -> list[dict]:
    """
    Get all tenants a user has access to.
    For now, returns the user's default tenant as a stub.
    Can be extended later to support multi-tenant user-tenant mapping.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.tenant_id:
        return []

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        return []

    return [{"id": tenant.id, "name": tenant.name}]


def get_tenant_name(db: Session, tenant_id: Optional[str]) -> Optional[str]:
    """Get tenant name by ID."""
    if not tenant_id:
        return None
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant.name if tenant else None


def get_quota_for_user(db: Session, tenant_id: Optional[str]) -> Optional[dict]:
    """Get quota status for template context."""
    if not tenant_id:
        return None
    quota_service = QuotaService(db)
    status = quota_service.check_quota(tenant_id)
    return {
        "monthly_audits_used": status.monthly_audits_used,
        "monthly_audits_limit": status.monthly_audits_limit,
        "monthly_audits_remaining": status.monthly_audits_remaining,
        "concurrent_audits": status.concurrent_audits,
        "max_concurrent": status.max_concurrent,
        "can_start_audit": status.can_start_audit,
        "reset_date": status.reset_date,
    }


@router.get("/", response_class=RedirectResponse)
async def dashboard_index():
    """Redirect to audit list."""
    return RedirectResponse(url="/dashboard/audits", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    error: str = None,
    db: Session = Depends(get_db)
):
    """Display login page. Redirects to audits if already logged in."""
    user = get_current_dashboard_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard/audits", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error}
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login form submission."""
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password"},
            status_code=401
        )

    session_id = create_session(
        user_id=user.id,
        tenant_id=getattr(user, 'tenant_id', None),
        role=user.role
    )

    response = RedirectResponse(url="/dashboard/audits", status_code=302)
    set_session_cookie(response, session_id)
    return response


@router.post("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    """Handle logout - delete session and clear cookie."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        delete_session(session_id)

    response = RedirectResponse(url="/dashboard/login", status_code=302)
    clear_session_cookie(response)
    return response


@router.get("/audits", response_class=HTMLResponse)
async def audit_list(
    request: Request,
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Display list of all audits with filtering and pagination."""
    per_page = 20

    query = db.query(Audit)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Audit.url.ilike(search_term),
                Audit.company_name.ilike(search_term)
            )
        )

    if status:
        if status == 'pending':
            query = query.filter(Audit.status.in_(['pending', 'queued']))
        else:
            query = query.filter(Audit.status == status)

    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Audit.created_at >= from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Audit.created_at <= to_date)
        except ValueError:
            pass

    total = query.count()
    total_pages = ceil(total / per_page) if total > 0 else 1

    page = min(page, total_pages)

    audits = query.order_by(Audit.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    tenant_name = get_tenant_name(db, user.get("tenant_id"))
    quota = get_quota_for_user(db, user.get("tenant_id"))

    filters = {
        "search": search,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
    }

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }

    return templates.TemplateResponse(
        "audit_list.html",
        {
            "request": request,
            "audits": audits,
            "user": user,
            "tenant_name": tenant_name,
            "quota": quota,
            "filters": filters,
            "pagination": pagination,
        }
    )


@router.get("/audits/new", response_class=HTMLResponse)
async def audit_new(
    request: Request,
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """Display new audit intake form."""
    tenant_name = get_tenant_name(db, user.get("tenant_id"))
    quota = get_quota_for_user(db, user.get("tenant_id"))
    return templates.TemplateResponse(
        "audit_new.html",
        {"request": request, "user": user, "tenant_name": tenant_name, "quota": quota}
    )


def validate_url(url: str) -> tuple[bool, str, str]:
    """Validate and normalize URL. Returns (is_valid, error_message, normalized_url)."""
    if not url or not url.strip():
        return False, "Website URL is required", ""

    url = url.strip().lower()
    url = re.sub(r'^(https?://)?(www\.)?', '', url)
    url = url.rstrip('/')

    domain_pattern = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$'
    if not re.match(domain_pattern, url, re.IGNORECASE):
        return False, "Please enter a valid domain (e.g., example.com)", ""

    return True, "", f"https://{url}"


def enqueue_audit_job(
    db: Session,
    audit_id: str,
    tenant_id: str,
    url: str,
    options: dict,
    job_type: str = "dashboard_audit"
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


@router.post("/audits/new", response_class=HTMLResponse)
async def audit_create(
    request: Request,
    url: str = Form(""),
    company_name: str = Form(""),
    trade_type: str = Form(""),
    tier: str = Form("basic"),
    service_areas: str = Form(""),
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """Handle new audit form submission with quota checking and validation."""
    tenant_id = user.get("tenant_id")
    user_id = user.get("id")
    tenant_name = get_tenant_name(db, tenant_id)
    errors = {}

    is_valid, url_error, normalized_url = validate_url(url)
    if not is_valid:
        errors["url"] = url_error

    if not company_name or not company_name.strip():
        errors["company_name"] = "Company name is required"

    if not trade_type:
        errors["trade_type"] = "Please select a trade type"

    if tier not in ["basic", "pro", "enterprise"]:
        errors["tier"] = "Please select a valid audit tier"

    if errors:
        return templates.TemplateResponse(
            "audit_new.html",
            {
                "request": request,
                "user": user,
                "tenant_name": tenant_name,
                "errors": errors,
                "form_data": {
                    "url": url,
                    "company_name": company_name,
                    "trade_type": trade_type,
                    "tier": tier,
                    "service_areas": service_areas,
                }
            },
            status_code=422
        )

    if tenant_id:
        try:
            quota_service = QuotaService(db)
            quota_service.enforce_quota(tenant_id)
        except QuotaExceededError as e:
            return templates.TemplateResponse(
                "audit_new.html",
                {
                    "request": request,
                    "user": user,
                    "tenant_name": tenant_name,
                    "quota_error": str(e),
                    "quota_details": {
                        "type": e.quota_type,
                        "limit": e.limit,
                        "used": e.used,
                    },
                    "form_data": {
                        "url": url,
                        "company_name": company_name,
                        "trade_type": trade_type,
                        "tier": tier,
                        "service_areas": service_areas,
                    }
                },
                status_code=429
            )

    parsed_service_areas = None
    if service_areas and service_areas.strip():
        areas = [a.strip() for a in re.split(r'[;,]', service_areas) if a.strip()]
        if areas:
            parsed_service_areas = areas

    audit_id = f"audit_{uuid.uuid4().hex[:12]}"

    audit = Audit(
        id=audit_id,
        url=normalized_url,
        company_name=company_name.strip(),
        trade_type=trade_type,
        tier=tier,
        service_areas=parsed_service_areas,
        status="queued",
        user_id=user_id,
        tenant_id=tenant_id,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    options = {
        "company_name": company_name.strip(),
        "trade_type": trade_type,
        "tier": tier,
        "service_areas": parsed_service_areas,
    }

    try:
        result_audit_id = enqueue_audit_job(
            db=db,
            audit_id=audit_id,
            tenant_id=tenant_id,
            url=normalized_url,
            options=options,
            job_type="dashboard_audit"
        )

        if result_audit_id != audit_id:
            db.delete(audit)
            db.commit()
            logger.info(f"Returning existing audit {result_audit_id} for duplicate request")
            return RedirectResponse(url=f"/dashboard/audits/{result_audit_id}", status_code=302)

        if tenant_id:
            quota_service = QuotaService(db)
            quota_service.increment_usage(tenant_id)

        logger.info(f"Created audit {audit_id} for {normalized_url} by user {user_id}")

    except Exception as e:
        logger.error(f"Failed to enqueue audit job: {e}")
        audit.status = "failed"
        audit.result = {"error": f"Failed to queue audit: {str(e)}"}
        db.commit()

        return templates.TemplateResponse(
            "audit_new.html",
            {
                "request": request,
                "user": user,
                "tenant_name": tenant_name,
                "error": "Failed to start audit. Please try again.",
                "form_data": {
                    "url": url,
                    "company_name": company_name,
                    "trade_type": trade_type,
                    "tier": tier,
                    "service_areas": service_areas,
                }
            },
            status_code=500
        )

    return RedirectResponse(url=f"/dashboard/audits/{audit.id}", status_code=302)


@router.get("/audits/{audit_id}", response_class=HTMLResponse)
async def audit_detail(
    request: Request,
    audit_id: str,
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """Display single audit details with progress and results."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        return templates.TemplateResponse(
            "audit_detail.html",
            {"request": request, "audit": None, "error": "Audit not found", "user": user},
            status_code=404
        )
    tenant_name = get_tenant_name(db, user.get("tenant_id"))
    quota = get_quota_for_user(db, user.get("tenant_id"))
    return templates.TemplateResponse(
        "audit_detail.html",
        {"request": request, "audit": audit, "user": user, "tenant_name": tenant_name, "quota": quota}
    )


@router.get("/audits/{audit_id}/download/{format}")
async def download_audit_report(
    audit_id: str,
    format: str,
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """Download audit report in HTML or PDF format with company name in filename."""
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Report not ready - audit still in progress")

    safe_company_name = re.sub(r'[^\w\s-]', '', audit.company_name or 'Report')
    safe_company_name = re.sub(r'\s+', '_', safe_company_name.strip())

    if format == "html":
        path = getattr(audit, 'report_html_path', None)
        media_type = "text/html"
        filename = f"{safe_company_name}_SEO_Report.html"
    elif format == "pdf":
        path = getattr(audit, 'report_pdf_path', None)
        if not path:
            json_path = getattr(audit, 'report_path', None)
            if json_path:
                path = json_path.replace(".json", "_PREMIUM.pdf")
        media_type = "application/pdf"
        filename = f"{safe_company_name}_SEO_Report.pdf"
    else:
        raise HTTPException(status_code=400, detail="Format must be 'html' or 'pdf'")

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"{format.upper()} report not available")

    return FileResponse(
        path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/tenants")
async def list_tenants(
    request: Request,
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """List all tenants the user has access to. Returns JSON."""
    tenants = get_user_tenants(db, user["id"])
    return JSONResponse(content={
        "tenants": tenants,
        "current_tenant_id": user.get("tenant_id"),
    })


@router.post("/switch-tenant")
async def switch_tenant(
    request: Request,
    body: SwitchTenantRequest,
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """Switch the active tenant for the current session."""
    tenants = get_user_tenants(db, user["id"])
    tenant_ids = [t["id"] for t in tenants]

    if body.tenant_id not in tenant_ids:
        return JSONResponse(
            status_code=403,
            content={"detail": "You do not have access to this tenant"}
        )

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(
            status_code=401,
            content={"detail": "No active session"}
        )

    success = update_session_tenant(session_id, body.tenant_id)
    if not success:
        return JSONResponse(
            status_code=400,
            content={"detail": "Failed to update session"}
        )

    tenant = db.query(Tenant).filter(Tenant.id == body.tenant_id).first()
    return JSONResponse(content={
        "success": True,
        "tenant_id": body.tenant_id,
        "tenant_name": tenant.name if tenant else None,
    })


@router.get("/quota")
async def get_quota_status(
    request: Request,
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """Get current quota status for the authenticated user's tenant."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return JSONResponse(content={
            "monthly_audits_used": 0,
            "monthly_audits_limit": -1,
            "monthly_audits_remaining": -1,
            "concurrent_audits": 0,
            "max_concurrent": 1,
            "can_start_audit": True,
            "quota_exceeded_reason": None,
            "reset_date": None,
        })

    quota_service = QuotaService(db)
    status = quota_service.check_quota(tenant_id)

    return JSONResponse(content={
        "monthly_audits_used": status.monthly_audits_used,
        "monthly_audits_limit": status.monthly_audits_limit,
        "monthly_audits_remaining": status.monthly_audits_remaining,
        "concurrent_audits": status.concurrent_audits,
        "max_concurrent": status.max_concurrent,
        "can_start_audit": status.can_start_audit,
        "quota_exceeded_reason": status.quota_exceeded_reason,
        "reset_date": status.reset_date.isoformat() if status.reset_date else None,
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    success: str = None,
    error: str = None,
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """Display user settings page."""
    user_record = db.query(User).filter(User.id == user["id"]).first()
    tenant_name = get_tenant_name(db, user.get("tenant_id"))
    quota = get_quota_for_user(db, user.get("tenant_id"))

    user_data = {
        "email": user_record.email if user_record else user.get("email"),
        "role": user.get("role"),
        "created_at": user_record.created_at if user_record else None,
    }

    tenant_info = None
    if user.get("tenant_id"):
        tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
        if tenant:
            tier = None
            if tenant.settings_json and isinstance(tenant.settings_json, dict):
                tier = tenant.settings_json.get("tier")
            tenant_info = {
                "name": tenant.name,
                "tier": tier,
            }

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": user,
            "user_data": user_data,
            "tenant_info": tenant_info,
            "tenant_name": tenant_name,
            "quota": quota,
            "success": success,
            "error": error,
        }
    )


@router.post("/settings/password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: dict = Depends(require_dashboard_auth),
    db: Session = Depends(get_db)
):
    """Handle password change form submission."""
    if new_password != confirm_password:
        return RedirectResponse(
            url="/dashboard/settings?error=Passwords+do+not+match",
            status_code=302
        )

    if len(new_password) < 8:
        return RedirectResponse(
            url="/dashboard/settings?error=Password+must+be+at+least+8+characters",
            status_code=302
        )

    user_record = db.query(User).filter(User.id == user["id"]).first()
    if not user_record:
        return RedirectResponse(
            url="/dashboard/settings?error=User+not+found",
            status_code=302
        )

    if not verify_password(current_password, user_record.password_hash):
        return RedirectResponse(
            url="/dashboard/settings?error=Current+password+is+incorrect",
            status_code=302
        )

    user_record.password_hash = hash_password(new_password)
    db.commit()

    return RedirectResponse(
        url="/dashboard/settings?success=Password+updated+successfully",
        status_code=302
    )
