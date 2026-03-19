"""Admin routes for system health monitoring."""
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from auth import require_admin
from packages.seo_health_report.metrics import metrics

router = APIRouter()
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def _get_metrics_data() -> dict:
    """Gather all metrics data for the health dashboard."""
    active_audits = metrics.get_gauge("active_audits")

    completed = sum(
        metrics.get_counter("audit_total", {"tier": tier, "status": "completed"})
        for tier in ["basic", "pro", "enterprise"]
    )
    failed = sum(
        metrics.get_counter("audit_total", {"tier": tier, "status": "failed"})
        for tier in ["basic", "pro", "enterprise"]
    )

    total = completed + failed
    error_rate = (failed / total * 100) if total > 0 else 0.0

    stats = metrics.get_histogram_stats("audit_duration_seconds")
    avg_duration = (stats["sum"] / stats["count"]) if stats["count"] > 0 else 0.0

    return {
        "active_audits": int(active_audits),
        "total_audits": int(total),
        "completed_audits": int(completed),
        "failed_audits": int(failed),
        "error_rate": round(error_rate, 2),
        "avg_duration_seconds": round(avg_duration, 2),
    }


@router.get("/health", response_class=HTMLResponse)
async def admin_health(request: Request, user=Depends(require_admin)):
    """Display system health metrics dashboard."""
    data = _get_metrics_data()
    return templates.TemplateResponse(request, "health.html", data)


@router.get("/health/metrics")
async def admin_health_metrics_json(user=Depends(require_admin)):
    """Return metrics as JSON for AJAX refresh."""
    return JSONResponse(_get_metrics_data())
