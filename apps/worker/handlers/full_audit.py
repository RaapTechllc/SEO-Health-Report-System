"""
Full Audit Handler - Runs complete SEO audit via job queue.

Executes technical, content, and AI visibility audits,
calculates scores, generates reports, and delivers webhooks.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from packages.schemas.models import (
    AuditResult,
    AuditStatus,
    AuditTier,
    ProgressStage,
    calculate_grade,
)
from packages.seo_health_report.scripts.calculate_scores import calculate_composite_score
from packages.seo_health_report.scripts.generate_report import generate_pdf_report
from packages.seo_health_report.scripts.orchestrate import run_full_audit
from packages.seo_health_report.scripts.rate_limiter import RateLimiter
from packages.seo_health_report.scripts.redaction import redact_sensitive
from packages.seo_health_report.scripts.webhook import (
    build_audit_webhook_payload,
    deliver_webhook,
)
from packages.seo_health_report.tier_config import get_tier_info, load_tier_config

logger = logging.getLogger(__name__)

LEASE_SECONDS = int(os.getenv("WORKER_LEASE_SECONDS", "300"))


async def write_progress_event(
    db: Session,
    audit_id: str,
    job_id: str,
    stage: ProgressStage,
    progress_pct: int,
    message: str,
) -> None:
    """Write progress event to database."""
    event_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO audit_progress_events
            (event_id, audit_id, job_id, event_type, message, progress_pct, created_at)
            VALUES (:event_id, :audit_id, :job_id, :event_type, :message, :progress_pct, CURRENT_TIMESTAMP)
        """
        ),
        {
            "event_id": event_id,
            "audit_id": audit_id,
            "job_id": job_id,
            "event_type": stage.value if hasattr(stage, "value") else str(stage),
            "message": redact_sensitive(message),
            "progress_pct": progress_pct,
        },
    )
    db.commit()


async def handle_full_audit(
    audit_id: str,
    job_id: str,
    payload: dict[str, Any],
    db: Session,
    worker_id: Optional[str] = None,
    lease_seconds: Optional[int] = None,
) -> dict[str, Any]:
    """
    Execute full SEO audit with all components.

    Args:
        audit_id: Audit record ID
        job_id: Job record ID
        payload: Job payload with url, company_name, tier, etc.
        db: Database session
        worker_id: Worker ID for lease renewal (optional)
        lease_seconds: Lease duration for renewal (optional)

    Returns:
        Result dict with raw and summary data
    """
    url = payload.get("url", "")
    company_name = payload.get("company_name", "")
    tier = payload.get("tier", "low")  # Default to LOW tier
    keywords = payload.get("keywords", [])
    competitors = payload.get("competitors", [])
    callback_url = payload.get("callback_url")
    tenant_id = payload.get("tenant_id", "default")

    # Load tier-specific configuration (models, settings)
    load_tier_config(tier)
    tier_info = get_tier_info()
    logger.info(f"Audit tier: {tier_info.get('display_name', tier)} ({tier})")

    rate_limiter = RateLimiter.for_tier(tier)

    await write_progress_event(
        db,
        audit_id,
        job_id,
        ProgressStage.INITIALIZING,
        0,
        f"Starting audit for {url}",
    )

    try:
        await write_progress_event(
            db,
            audit_id,
            job_id,
            ProgressStage.TECHNICAL_AUDIT,
            10,
            "Running technical SEO audit",
        )

        await write_progress_event(
            db,
            audit_id,
            job_id,
            ProgressStage.CONTENT_AUDIT,
            30,
            "Running content authority audit",
        )

        await write_progress_event(
            db,
            audit_id,
            job_id,
            ProgressStage.AI_VISIBILITY_AUDIT,
            50,
            "Running AI visibility audit",
        )

        raw_result = await run_full_audit(
            target_url=url,
            company_name=company_name,
            primary_keywords=keywords,
            competitor_urls=competitors,
            rate_limiter=rate_limiter,
        )

        scores = calculate_composite_score(raw_result)
        overall_score = scores.get("overall_score", 0)
        grade = calculate_grade(overall_score)
        component_scores = scores.get("component_scores", {})

        technical_score = None
        content_score = None
        ai_visibility_score = None

        if "technical" in component_scores:
            technical_score = int(component_scores["technical"].get("score", 0))
        if "content" in component_scores:
            content_score = int(component_scores["content"].get("score", 0))
        if "ai_visibility" in component_scores:
            ai_visibility_score = int(component_scores["ai_visibility"].get("score", 0))

        await write_progress_event(
            db,
            audit_id,
            job_id,
            ProgressStage.GENERATING_REPORT,
            80,
            "Generating audit report",
        )

        audit_tier = AuditTier.BASIC
        if tier in [t.value for t in AuditTier]:
            audit_tier = AuditTier(tier)

        audit_result = AuditResult(
            audit_id=audit_id,
            url=url,
            company_name=company_name,
            tier=audit_tier,
            status=AuditStatus.COMPLETED,
            overall_score=overall_score,
            grade=grade,
            technical_score=technical_score,
            content_score=content_score,
            ai_visibility_score=ai_visibility_score,
            completed_at=datetime.utcnow().isoformat(),
        )

        html_path = await generate_html_report_simple(audit_result, raw_result, tenant_id)
        audit_result.report_path = html_path

        # Try PDF generation (graceful fallback if unavailable)
        pdf_path = await generate_pdf_report(audit_result, raw_result, tenant_id, html_path)
        if pdf_path:
            audit_result.report_pdf_path = pdf_path
            logger.info(f"PDF report generated: {pdf_path}")

        result_json = {"raw": raw_result, "summary": audit_result.to_dict()}

        grade_value = grade.value if hasattr(grade, "value") else str(grade)

        db.execute(
            text(
                """
                UPDATE audits SET
                    status = 'completed',
                    overall_score = :score,
                    grade = :grade,
                    result = :result,
                    report_html_path = :html_path,
                    report_pdf_path = :pdf_path,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = :audit_id
            """
            ),
            {
                "audit_id": audit_id,
                "score": overall_score,
                "grade": grade_value,
                "result": json.dumps(result_json),
                "html_path": html_path,
                "pdf_path": pdf_path,
            },
        )
        db.commit()

        await write_progress_event(
            db,
            audit_id,
            job_id,
            ProgressStage.COMPLETED,
            100,
            f"Audit completed with score {overall_score} ({grade_value})",
        )

        if callback_url:
            webhook_payload = build_audit_webhook_payload(
                audit_id=audit_id,
                status="completed",
                overall_score=overall_score,
                grade=grade_value,
                report_url=html_path,
            )
            webhook_secret = get_webhook_secret(tenant_id)
            webhook_result = await deliver_webhook(
                callback_url, webhook_payload, webhook_secret
            )

            if webhook_result.success:
                db.execute(
                    text(
                        "UPDATE audits SET callback_delivered_at = CURRENT_TIMESTAMP WHERE id = :id"
                    ),
                    {"id": audit_id},
                )
                db.commit()

        return result_json

    except Exception as e:
        error_msg = redact_sensitive(str(e))
        await write_progress_event(
            db,
            audit_id,
            job_id,
            ProgressStage.FAILED,
            0,
            f"Audit failed: {error_msg}",
        )

        db.execute(
            text("UPDATE audits SET status = :status WHERE id = :id"),
            {"status": "failed", "id": audit_id},
        )
        db.commit()

        if callback_url:
            webhook_payload = build_audit_webhook_payload(
                audit_id=audit_id, status="failed", error_message=error_msg
            )
            await deliver_webhook(
                callback_url, webhook_payload, get_webhook_secret(tenant_id)
            )

        raise


async def handle_full_audit_with_lease_renewal(
    audit_id: str,
    job_id: str,
    payload: dict[str, Any],
    db: Session,
    worker_id: str,
    lease_seconds: int = LEASE_SECONDS,
) -> dict[str, Any]:
    """
    Wrapper for handle_full_audit with automatic lease renewal.

    Starts a background task that renews the job lease every LEASE_SECONDS/2
    to prevent the job from being reclaimed during long-running audits.

    Args:
        audit_id: Audit record ID
        job_id: Job record ID
        payload: Job payload with url, company_name, tier, etc.
        db: Database session
        worker_id: Worker ID for lease renewal
        lease_seconds: Lease duration in seconds

    Returns:
        Result dict with raw and summary data
    """
    from apps.worker.executor import renew_lease_async

    async def lease_renewal_task():
        """Background task to renew lease periodically."""
        renewal_interval = lease_seconds // 2
        while True:
            await asyncio.sleep(renewal_interval)
            renewed = await renew_lease_async(job_id, worker_id, lease_seconds)
            if renewed:
                logger.debug(f"Lease renewed for job {job_id}")
            else:
                logger.warning(f"Failed to renew lease for job {job_id}")

    renewal_task = asyncio.create_task(lease_renewal_task())
    try:
        return await handle_full_audit(
            audit_id=audit_id,
            job_id=job_id,
            payload=payload,
            db=db,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )
    finally:
        renewal_task.cancel()
        try:
            await renewal_task
        except asyncio.CancelledError:
            pass


async def generate_html_report_simple(
    audit_result: AuditResult,
    raw_result: dict,
    tenant_id: str,
) -> str:
    """Generate simple HTML report and return path."""
    reports_dir = Path("reports") / tenant_id
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f"{audit_result.audit_id}.html"

    grade_value = (
        audit_result.grade.value
        if hasattr(audit_result.grade, "value")
        else audit_result.grade
    )
    tier_value = (
        audit_result.tier.value
        if hasattr(audit_result.tier, "value")
        else audit_result.tier
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SEO Audit Report - {audit_result.company_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        .score {{ font-size: 48px; font-weight: bold; }}
        .grade {{ font-size: 24px; padding: 10px 20px; border-radius: 5px; }}
        .grade-A {{ background: #22c55e; color: white; }}
        .grade-B {{ background: #84cc16; color: white; }}
        .grade-C {{ background: #eab308; color: white; }}
        .grade-D {{ background: #f97316; color: white; }}
        .grade-F {{ background: #ef4444; color: white; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .component {{ display: inline-block; margin: 10px; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>SEO Health Report</h1>
    <h2>{audit_result.company_name}</h2>
    <p>URL: <a href="{audit_result.url}">{audit_result.url}</a></p>
    <p>Generated: {audit_result.completed_at or datetime.utcnow().isoformat()}</p>

    <div class="section">
        <h3>Overall Score</h3>
        <span class="score">{audit_result.overall_score or 0}</span>
        <span class="grade grade-{grade_value}">{grade_value}</span>
    </div>

    <div class="section">
        <h3>Component Scores</h3>
        <div class="component">
            <strong>Technical</strong><br>
            {audit_result.technical_score if audit_result.technical_score is not None else 'N/A'}
        </div>
        <div class="component">
            <strong>Content</strong><br>
            {audit_result.content_score if audit_result.content_score is not None else 'N/A'}
        </div>
        <div class="component">
            <strong>AI Visibility</strong><br>
            {audit_result.ai_visibility_score if audit_result.ai_visibility_score is not None else 'N/A'}
        </div>
    </div>

    <div class="section">
        <h3>Tier</h3>
        <p>{tier_value}</p>
    </div>
</body>
</html>"""

    with open(report_path, "w") as f:
        f.write(html)

    return str(report_path)


def get_webhook_secret(tenant_id: str) -> str:
    """Get webhook signing secret for tenant."""
    return os.getenv("WEBHOOK_SECRET", f"webhook-secret-{tenant_id}")
