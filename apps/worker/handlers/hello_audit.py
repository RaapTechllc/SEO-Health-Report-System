"""
Hello Audit Handler - Minimal audit that exercises full pipeline.

This handler:
1. Uses safe_fetch to get the homepage
2. Extracts basic info (title, status, final URL, content hash)
3. Writes progress events to DB
4. Updates audit with result
"""

import hashlib
import re
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from packages.seo_health_report.scripts.redaction import redact_sensitive
from packages.seo_health_report.scripts.safe_fetch import safe_fetch


async def handle_hello_audit(
    audit_id: str,
    job_id: str,
    url: str,
    db_session: Session,
) -> dict:
    """
    Execute hello audit - fetches page and extracts basic info.

    Args:
        audit_id: The audit record ID.
        job_id: The job ID for progress tracking.
        url: The URL to audit.
        db_session: Database session for writing progress events.

    Returns:
        dict with: title, status_code, final_url, html_hash
    """
    await write_progress_event(
        db_session, audit_id, job_id, "step_started", "Hello audit started", 0
    )

    await write_progress_event(
        db_session, audit_id, job_id, "step_started", f"Fetching {url}", 25
    )

    result = await safe_fetch(url)

    await write_progress_event(
        db_session, audit_id, job_id, "step_started", "Parsing response", 50
    )

    title = extract_title(result.content)
    html_hash = hashlib.sha256(result.content).hexdigest()[:16]

    audit_result = {
        "title": title,
        "status_code": result.status_code,
        "final_url": result.final_url,
        "html_hash": html_hash,
        "content_length": len(result.content),
        "completed_at": datetime.utcnow().isoformat(),
    }

    await write_progress_event(
        db_session, audit_id, job_id, "step_done", "Hello audit completed", 100
    )

    return audit_result


def extract_title(html_bytes: bytes) -> Optional[str]:
    """Extract <title> from HTML content."""
    try:
        html = html_bytes.decode("utf-8", errors="ignore")
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None
    except Exception:
        return None


async def write_progress_event(
    db_session: Session,
    audit_id: str,
    job_id: str,
    event_type: str,
    message: str,
    progress_pct: int,
) -> None:
    """Write a progress event to the database."""
    event_id = str(uuid.uuid4())

    db_session.execute(
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
            "event_type": event_type,
            "message": redact_sensitive(message),
            "progress_pct": progress_pct,
        },
    )
    db_session.commit()
