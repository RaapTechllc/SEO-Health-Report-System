"""Progress tracking service with time estimation."""
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

MODULE_NAMES = ["technical", "content", "ai"]

BASE_TIMES = {
    "basic": 120,
    "pro": 300,
    "enterprise": 900,
}

PER_PAGE_TIMES = {
    "basic": 2,
    "pro": 5,
    "enterprise": 10,
}


@dataclass
class ModuleProgress:
    module_name: str  # "technical", "content", "ai"
    status: str  # "pending", "running", "completed", "failed"
    progress_pct: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        result = asdict(self)
        if result["started_at"]:
            result["started_at"] = result["started_at"].isoformat()
        if result["completed_at"]:
            result["completed_at"] = result["completed_at"].isoformat()
        return result


@dataclass
class AuditProgress:
    audit_id: str
    overall_status: str
    overall_progress_pct: int
    modules: list[ModuleProgress]
    started_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    elapsed_seconds: int

    def to_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "overall_status": self.overall_status,
            "overall_progress_pct": self.overall_progress_pct,
            "modules": [m.to_dict() for m in self.modules],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "elapsed_seconds": self.elapsed_seconds,
        }


def estimate_completion_time(tier: str, page_count: int = 10) -> int:
    """Estimate seconds to completion based on tier and pages."""
    base = BASE_TIMES.get(tier, BASE_TIMES["basic"])
    per_page = PER_PAGE_TIMES.get(tier, PER_PAGE_TIMES["basic"])
    return base + (per_page * page_count)


def _parse_module_events(events: list) -> dict[str, ModuleProgress]:
    """Parse events into module progress objects."""
    modules = {
        name: ModuleProgress(module_name=name, status="pending", progress_pct=0)
        for name in MODULE_NAMES
    }

    for event in events:
        event_type, message, progress_pct, created_at, data_json = event
        msg_lower = (message or "").lower()

        module_name = None
        for name in MODULE_NAMES:
            if name in msg_lower:
                module_name = name
                break

        if not module_name:
            continue

        mod = modules[module_name]

        if event_type == "step_started":
            if mod.status == "pending":
                mod.status = "running"
                mod.started_at = created_at
        elif event_type == "step_done":
            mod.status = "completed"
            mod.completed_at = created_at
            mod.progress_pct = 100
        elif event_type == "error":
            mod.status = "failed"
            mod.error_message = message

        if progress_pct is not None and mod.status == "running":
            mod.progress_pct = max(mod.progress_pct, progress_pct)

    return modules


def get_audit_progress(db: Session, audit_id: str) -> Optional[AuditProgress]:
    """Get comprehensive progress for an audit."""
    audit_row = db.execute(
        text("""
            SELECT status, tier, created_at, completed_at
            FROM audits
            WHERE id = :audit_id
        """),
        {"audit_id": audit_id}
    ).fetchone()

    if not audit_row:
        return None

    status, tier, started_at, completed_at = audit_row

    events = db.execute(
        text("""
            SELECT event_type, message, progress_pct, created_at, data_json
            FROM audit_progress_events
            WHERE audit_id = :audit_id
            ORDER BY created_at
        """),
        {"audit_id": audit_id}
    ).fetchall()

    modules_dict = _parse_module_events(events)
    modules = list(modules_dict.values())

    if status == "completed":
        overall_pct = 100
        for mod in modules:
            if mod.status != "failed":
                mod.status = "completed"
                mod.progress_pct = 100
    elif status == "failed":
        overall_pct = max((m.progress_pct for m in modules), default=0)
    else:
        completed_count = sum(1 for m in modules if m.status == "completed")
        running_pcts = [m.progress_pct for m in modules if m.status == "running"]
        running_contrib = sum(running_pcts) / len(MODULE_NAMES) if running_pcts else 0
        overall_pct = int((completed_count * 100 / len(MODULE_NAMES)) + running_contrib / len(MODULE_NAMES))
        overall_pct = min(overall_pct, 99)

    elapsed = 0
    estimated_completion = None
    if started_at:
        now = datetime.utcnow()
        elapsed = int((now - started_at).total_seconds())

        if status not in ("completed", "failed") and overall_pct > 0:
            estimated_total = estimate_completion_time(tier or "basic", 10)
            remaining = max(0, estimated_total - elapsed)
            from datetime import timedelta
            estimated_completion = now + timedelta(seconds=remaining)

    return AuditProgress(
        audit_id=audit_id,
        overall_status=status,
        overall_progress_pct=overall_pct,
        modules=modules,
        started_at=started_at,
        estimated_completion=estimated_completion,
        elapsed_seconds=elapsed,
    )
