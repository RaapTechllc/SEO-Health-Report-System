"""
Job executor module for claiming and processing audit jobs.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.worker.handlers.full_audit import handle_full_audit_with_lease_renewal
from database import SessionLocal
from packages.seo_health_report.scripts.safe_fetch import SSRFError

logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Retry-able errors: timeouts, 429, 503, network issues."""
    pass


class PermanentError(Exception):
    """Non-retry-able: 404, invalid URL, SSRF blocked."""
    pass


@dataclass
class AuditJob:
    """Represents an audit job from the database."""
    job_id: str
    tenant_id: str
    audit_id: str
    status: str
    attempt: int
    max_attempts: int
    queued_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    locked_until: Optional[datetime]
    locked_by: Optional[str]
    idempotency_key: str
    payload: dict[str, Any]
    last_error: Optional[str]

    @classmethod
    def from_row(cls, row) -> "AuditJob":
        """Create AuditJob from database row."""
        payload = row.payload_json
        if isinstance(payload, str):
            payload = json.loads(payload)
        return cls(
            job_id=row.job_id,
            tenant_id=row.tenant_id,
            audit_id=row.audit_id,
            status=row.status,
            attempt=row.attempt,
            max_attempts=row.max_attempts,
            queued_at=row.queued_at,
            started_at=row.started_at,
            finished_at=row.finished_at,
            locked_until=row.locked_until,
            locked_by=row.locked_by,
            idempotency_key=row.idempotency_key,
            payload=payload,
            last_error=row.last_error,
        )


def _redact_error(error_message: str) -> str:
    """Redact sensitive data from error messages."""
    try:
        from packages.seo_health_report.scripts.redaction import redact_sensitive
        return redact_sensitive(error_message)
    except ImportError:
        import re
        patterns = [
            (r"(?i)(api[_-]?key|token|secret|password|auth)['\"]?\s*[:=]\s*['\"]?[\w\-\.]+", "[REDACTED]"),
            (r"(?i)authorization:\s*bearer\s+[\w\-\.]+", "Authorization: Bearer [REDACTED]"),
        ]
        result = error_message
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        return result


def claim_job(worker_id: str, lease_seconds: int = 300) -> Optional[AuditJob]:
    """
    Atomically claim a job using UPDATE with optimistic locking (SQLite compatible).

    Args:
        worker_id: Unique identifier for this worker instance.
        lease_seconds: Duration to hold the lease in seconds.

    Returns:
        AuditJob if a job was claimed, None otherwise.
    """
    db: Session = SessionLocal()
    try:
        query = text("""
            UPDATE audit_jobs
            SET
                status = 'running',
                started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                locked_until = datetime('now', '+' || :lease_seconds || ' seconds'),
                locked_by = :worker_id,
                attempt = attempt + 1
            WHERE job_id = (
                SELECT job_id FROM audit_jobs
                WHERE status = 'queued'
                   OR (status = 'running' AND locked_until < CURRENT_TIMESTAMP)
                ORDER BY queued_at
                LIMIT 1
            )
            RETURNING *
        """)

        result = db.execute(query, {"worker_id": worker_id, "lease_seconds": lease_seconds})
        row = result.fetchone()
        db.commit()

        if row is None:
            return None

        return AuditJob.from_row(row)
    except Exception as e:
        db.rollback()
        logger.error(f"Error claiming job: {e}")
        raise
    finally:
        db.close()


async def claim_job_async(worker_id: str, lease_seconds: int = 300) -> Optional[AuditJob]:
    """Async wrapper for claim_job."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, claim_job, worker_id, lease_seconds)


def mark_job_done(job_id: str) -> None:
    """
    Mark a job as successfully completed.

    Args:
        job_id: The job ID to mark as done.
    """
    db: Session = SessionLocal()
    try:
        query = text("""
            UPDATE audit_jobs
            SET
                status = 'done',
                finished_at = CURRENT_TIMESTAMP,
                locked_until = NULL,
                locked_by = NULL
            WHERE job_id = :job_id
        """)
        db.execute(query, {"job_id": job_id})
        db.commit()
        logger.info(f"Job {job_id} marked as done")
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking job done: {e}")
        raise
    finally:
        db.close()


async def mark_job_done_async(job_id: str) -> None:
    """Async wrapper for mark_job_done."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, mark_job_done, job_id)


def mark_job_failed(job_id: str, error_message: str) -> None:
    """
    Mark a job as failed with a redacted error message.

    Args:
        job_id: The job ID to mark as failed.
        error_message: The error message (will be redacted).
    """
    db: Session = SessionLocal()
    try:
        redacted_error = _redact_error(error_message)
        query = text("""
            UPDATE audit_jobs
            SET
                status = 'failed',
                finished_at = CURRENT_TIMESTAMP,
                locked_until = NULL,
                locked_by = NULL,
                last_error = :error_message
            WHERE job_id = :job_id
        """)
        db.execute(query, {"job_id": job_id, "error_message": redacted_error})
        db.commit()
        logger.warning(f"Job {job_id} marked as failed: {redacted_error}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking job failed: {e}")
        raise
    finally:
        db.close()


async def mark_job_failed_async(job_id: str, error_message: str) -> None:
    """Async wrapper for mark_job_failed."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, mark_job_failed, job_id, error_message)


def calculate_backoff(attempt: int, base_seconds: int = 30, max_seconds: int = 3600) -> int:
    """
    Calculate exponential backoff with jitter.

    Args:
        attempt: Current attempt number (1-indexed).
        base_seconds: Base delay in seconds.
        max_seconds: Maximum delay cap.

    Returns:
        Delay in seconds.
    """
    import random
    delay = min(base_seconds * (2 ** (attempt - 1)), max_seconds)
    jitter = random.uniform(0, delay * 0.1)
    return int(delay + jitter)


def mark_job_queued(job_id: str, retry_after_seconds: int) -> None:
    """
    Reset a job to queued status for retry with backoff.

    Args:
        job_id: The job ID to requeue.
        retry_after_seconds: Seconds to wait before retrying.
    """
    db: Session = SessionLocal()
    try:
        query = text("""
            UPDATE audit_jobs
            SET
                status = 'queued',
                locked_until = NULL,
                locked_by = NULL,
                queued_at = datetime('now', '+' || :retry_after || ' seconds')
            WHERE job_id = :job_id
        """)
        db.execute(query, {"job_id": job_id, "retry_after": retry_after_seconds})
        db.commit()
        logger.info(f"Job {job_id} requeued with {retry_after_seconds}s backoff")
    except Exception as e:
        db.rollback()
        logger.error(f"Error requeuing job: {e}")
        raise
    finally:
        db.close()


async def mark_job_queued_async(job_id: str, retry_after_seconds: int) -> None:
    """Async wrapper for mark_job_queued."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, mark_job_queued, job_id, retry_after_seconds)


def renew_lease(job_id: str, worker_id: str, lease_seconds: int = 300) -> bool:
    """
    Extend the lock for a long-running job.

    Args:
        job_id: The job ID to renew.
        worker_id: The worker ID that holds the lease.
        lease_seconds: New lease duration in seconds.

    Returns:
        True if lease was renewed, False if lease was lost.
    """
    db: Session = SessionLocal()
    try:
        query = text("""
            UPDATE audit_jobs
            SET locked_until = datetime('now', '+' || :lease_seconds || ' seconds')
            WHERE job_id = :job_id AND locked_by = :worker_id
        """)
        result = db.execute(query, {
            "job_id": job_id,
            "worker_id": worker_id,
            "lease_seconds": lease_seconds
        })
        db.commit()
        renewed = result.rowcount > 0
        if renewed:
            logger.debug(f"Lease renewed for job {job_id}")
        else:
            logger.warning(f"Failed to renew lease for job {job_id} - lease may be lost")
        return renewed
    except Exception as e:
        db.rollback()
        logger.error(f"Error renewing lease: {e}")
        raise
    finally:
        db.close()


async def renew_lease_async(job_id: str, worker_id: str, lease_seconds: int = 300) -> bool:
    """Async wrapper for renew_lease."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, renew_lease, job_id, worker_id, lease_seconds)


async def execute_job(job: AuditJob) -> None:
    """
    Execute an audit job by dispatching to the appropriate handler.

    Args:
        job: The AuditJob to execute.

    Raises:
        TransientError: For retry-able errors.
        PermanentError: For non-retry-able errors.
    """
    logger.info(f"Executing job {job.job_id} (attempt {job.attempt}/{job.max_attempts})")

    job_type = job.payload.get("type", "audit")

    handlers = {
        "audit": _execute_audit,
        "competitor_audit": _execute_competitor_audit,
        "hello_audit": _execute_hello_audit,
    }

    handler = handlers.get(job_type)
    if handler is None:
        raise PermanentError(f"Unknown job type: {job_type}")

    await handler(job)


async def _execute_audit(job: AuditJob, worker_id: str = None, lease_seconds: int = 300) -> None:
    """Execute a full SEO audit job using the new handler with lease renewal."""
    url = job.payload.get("url")
    company_name = job.payload.get("company_name")

    if not url or not company_name:
        raise PermanentError(f"Missing required payload fields: url={url}, company_name={company_name}")

    db: Session = SessionLocal()
    try:
        await handle_full_audit_with_lease_renewal(
            audit_id=job.audit_id,
            job_id=job.job_id,
            payload=job.payload,
            db=db,
            worker_id=worker_id or job.locked_by or "unknown",
            lease_seconds=lease_seconds,
        )
    except SSRFError as e:
        raise PermanentError(f"SSRF blocked: {e}")
    except httpx.TimeoutException as e:
        raise TransientError(f"Request timeout: {e}")
    except httpx.NetworkError as e:
        raise TransientError(f"Network error: {e}")
    except Exception as e:
        error_str = str(e).lower()
        if any(term in error_str for term in ["timeout", "connection", "429", "503", "rate limit"]):
            raise TransientError(str(e))
        elif any(term in error_str for term in ["404", "not found", "invalid url"]):
            raise PermanentError(str(e))
        raise
    finally:
        db.close()


async def _execute_competitor_audit(job: AuditJob) -> None:
    """Execute a competitor monitoring audit job."""
    try:
        url = job.payload.get("url")
        company_name = job.payload.get("company_name")
        job.payload.get("competitor_id")

        if not url or not company_name:
            raise PermanentError("Missing required payload fields")

        logger.info(f"Running competitor audit for {company_name} ({url})")

    except Exception as e:
        error_str = str(e).lower()
        if any(term in error_str for term in ["timeout", "connection", "429", "503"]):
            raise TransientError(str(e))
        raise


async def _execute_hello_audit(job: AuditJob) -> None:
    """Execute a hello audit job - minimal pipeline test."""
    from apps.worker.handlers.hello_audit import handle_hello_audit

    url = job.payload.get("url")
    if not url:
        raise PermanentError("Missing required payload field: url")

    db: Session = SessionLocal()
    try:
        result = await handle_hello_audit(job.audit_id, job.job_id, url, db)

        db.execute(
            text("""
                UPDATE audits
                SET result_json = :result, status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE audit_id = :audit_id
            """),
            {"audit_id": job.audit_id, "result_json": json.dumps(result)},
        )
        db.commit()
        logger.info(f"Hello audit completed for {url}: {result}")
    except Exception as e:
        db.rollback()
        error_str = str(e).lower()
        if any(term in error_str for term in ["timeout", "connection", "429", "503", "rate limit"]):
            raise TransientError(str(e))
        elif any(term in error_str for term in ["404", "not found", "invalid url", "ssrf"]):
            raise PermanentError(str(e))
        raise
    finally:
        db.close()
