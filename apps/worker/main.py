"""
Worker process entrypoint with graceful shutdown.

Polls the job queue, claims jobs, and executes them.
"""

import asyncio
import logging
import os
import signal
import sys
import uuid
from typing import Optional

from executor import (
    AuditJob,
    PermanentError,
    TransientError,
    calculate_backoff,
    claim_job_async,
    execute_job,
    mark_job_done_async,
    mark_job_failed_async,
    mark_job_queued_async,
)

try:
    from packages.core.logging import setup_logging
    setup_logging(service_name="seo-health-worker")
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
logger = logging.getLogger(__name__)

POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "5"))
LEASE_SECONDS = int(os.getenv("WORKER_LEASE_SECONDS", "300"))
WORKER_ID = os.getenv("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")

shutdown_requested = False


def _redact_error(error_message: str) -> str:
    """Redact sensitive data from error messages."""
    try:
        from packages.seo_health_report.scripts.redaction import redact_sensitive
        return redact_sensitive(error_message)
    except ImportError:
        import re
        patterns = [
            (r"(?i)(api[_-]?key|token|secret|password|auth)['\"]?\s*[:=]\s*['\"]?[\w\-\.]+", "[REDACTED]"),
        ]
        result = error_message
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        return result


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name}, initiating graceful shutdown...")
    shutdown_requested = True


async def webhook_retry_loop() -> None:
    """Background loop that processes pending webhook retries."""
    retry_interval = int(os.getenv("WEBHOOK_RETRY_INTERVAL", "60"))
    logger.info(f"Webhook retry loop started (interval: {retry_interval}s)")

    while not shutdown_requested:
        try:
            from database import SessionLocal
            db = SessionLocal()
            try:
                from packages.seo_health_report.webhooks.service import WebhookService
                service = WebhookService(db)
                count = await service.process_pending_retries()
                if count > 0:
                    logger.info(f"Processed {count} webhook retries")
                await service.close()
            except ImportError:
                pass  # Webhook service not available
            except Exception as e:
                logger.error(f"Error in webhook retry loop: {e}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to create DB session for webhook retries: {e}")

        await asyncio.sleep(retry_interval)

    logger.info("Webhook retry loop exiting")


async def worker_loop(worker_id: str) -> None:
    """
    Main worker loop that polls for and executes jobs.

    Args:
        worker_id: Unique identifier for this worker instance.
    """
    logger.info(f"Worker loop started for {worker_id}")

    while not shutdown_requested:
        job: Optional[AuditJob] = None

        try:
            job = await claim_job_async(worker_id, LEASE_SECONDS)

            if job is None:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            logger.info(f"Claimed job {job.job_id} (type: {job.payload.get('type', 'audit')})")

            try:
                await execute_job(job)
                await mark_job_done_async(job.job_id)
                logger.info(f"Job {job.job_id} completed successfully")

            except TransientError as e:
                error_msg = _redact_error(str(e))
                logger.warning(f"Transient error for job {job.job_id}: {error_msg}")

                if job.attempt < job.max_attempts:
                    backoff = calculate_backoff(job.attempt)
                    await mark_job_queued_async(job.job_id, backoff)
                    logger.info(f"Job {job.job_id} requeued for retry in {backoff}s (attempt {job.attempt}/{job.max_attempts})")
                else:
                    await mark_job_failed_async(job.job_id, error_msg)
                    logger.error(f"Job {job.job_id} failed after {job.max_attempts} attempts: {error_msg}")

            except PermanentError as e:
                error_msg = _redact_error(str(e))
                await mark_job_failed_async(job.job_id, error_msg)
                logger.error(f"Job {job.job_id} permanently failed: {error_msg}")

            except Exception as e:
                error_msg = _redact_error(str(e))
                await mark_job_failed_async(job.job_id, error_msg)
                logger.exception(f"Unexpected error for job {job.job_id}: {error_msg}")

        except Exception as e:
            logger.exception(f"Error in worker loop: {e}")
            await asyncio.sleep(POLL_INTERVAL)

    logger.info(f"Worker loop exiting for {worker_id}")


async def main() -> None:
    """Main entrypoint for the worker process."""
    logger.info(f"Starting worker {WORKER_ID}")
    logger.info(f"Poll interval: {POLL_INTERVAL}s, Lease duration: {LEASE_SECONDS}s")

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        await asyncio.gather(
            worker_loop(WORKER_ID),
            webhook_retry_loop(),
        )
    except Exception as e:
        logger.exception(f"Fatal error in worker: {e}")
        sys.exit(1)

    logger.info(f"Worker {WORKER_ID} shut down gracefully")


if __name__ == "__main__":
    asyncio.run(main())
