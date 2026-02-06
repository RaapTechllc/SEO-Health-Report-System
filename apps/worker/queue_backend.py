"""
Queue backend abstraction for the worker process.

Supports SQLite (dev) and Redis (production) backends.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class QueueBackend(ABC):
    """Abstract job queue backend."""

    @abstractmethod
    async def enqueue(self, job_id: str, payload: dict[str, Any]) -> None:
        """Add a job to the queue."""
        ...

    @abstractmethod
    async def claim(self, worker_id: str, lease_seconds: int) -> Optional[dict[str, Any]]:
        """Claim the next available job. Returns job dict or None."""
        ...

    @abstractmethod
    async def mark_done(self, job_id: str) -> None:
        """Mark a job as completed."""
        ...

    @abstractmethod
    async def mark_failed(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""
        ...

    @abstractmethod
    async def wait_for_job(self, timeout: int = 5) -> Optional[dict[str, Any]]:
        """Wait for a job (blocking pop for Redis, polling for SQLite)."""
        ...


class SQLiteQueueBackend(QueueBackend):
    """SQLite-based queue backend wrapping existing executor functions."""

    async def enqueue(self, job_id: str, payload: dict[str, Any]) -> None:
        # Handled by the API layer via enqueue_audit_job()
        pass

    async def claim(self, worker_id: str, lease_seconds: int) -> Optional[dict[str, Any]]:
        from executor import claim_job_async
        job = await claim_job_async(worker_id, lease_seconds)
        if job is None:
            return None
        return {
            "job_id": job.job_id,
            "audit_id": job.audit_id,
            "payload": job.payload,
            "attempt": job.attempt,
            "max_attempts": job.max_attempts,
            "_job": job,  # Keep original for executor compat
        }

    async def mark_done(self, job_id: str) -> None:
        from executor import mark_job_done_async
        await mark_job_done_async(job_id)

    async def mark_failed(self, job_id: str, error: str) -> None:
        from executor import mark_job_failed_async
        await mark_job_failed_async(job_id, error)

    async def wait_for_job(self, timeout: int = 5) -> Optional[dict[str, Any]]:
        # SQLite uses polling
        import asyncio
        await asyncio.sleep(timeout)
        return None


class RedisQueueBackend(QueueBackend):
    """Redis-based queue backend using reliable queue pattern (BRPOPLPUSH)."""

    QUEUE_KEY = "seo:jobs:pending"
    PROCESSING_KEY = "seo:jobs:processing"

    def __init__(self, redis_url: str):
        import redis as redis_lib
        self._redis = redis_lib.from_url(redis_url, decode_responses=True)
        self._redis.ping()
        logger.info("Redis queue backend connected")

    async def enqueue(self, job_id: str, payload: dict[str, Any]) -> None:
        job_data = json.dumps({"job_id": job_id, **payload})
        self._redis.lpush(self.QUEUE_KEY, job_data)
        logger.debug(f"Enqueued job {job_id} to Redis")

    async def claim(self, worker_id: str, lease_seconds: int) -> Optional[dict[str, Any]]:
        # Use BRPOPLPUSH for reliable queue processing
        raw = self._redis.brpoplpush(self.QUEUE_KEY, self.PROCESSING_KEY, timeout=0)
        if raw is None:
            return None
        job = json.loads(raw)
        # Set lease expiry
        lease_key = f"seo:lease:{job['job_id']}"
        self._redis.setex(lease_key, lease_seconds, worker_id)
        return job

    async def mark_done(self, job_id: str) -> None:
        # Remove from processing list
        self._remove_from_processing(job_id)
        self._redis.delete(f"seo:lease:{job_id}")
        logger.debug(f"Job {job_id} marked done in Redis")

    async def mark_failed(self, job_id: str, error: str) -> None:
        self._remove_from_processing(job_id)
        self._redis.delete(f"seo:lease:{job_id}")
        # Store failure info
        self._redis.hset(f"seo:job:failed:{job_id}", mapping={
            "error": error[:1000],
            "failed_at": str(time.time()),
        })
        self._redis.expire(f"seo:job:failed:{job_id}", 86400 * 7)  # 7 days
        logger.debug(f"Job {job_id} marked failed in Redis")

    async def wait_for_job(self, timeout: int = 5) -> Optional[dict[str, Any]]:
        raw = self._redis.brpoplpush(self.QUEUE_KEY, self.PROCESSING_KEY, timeout=timeout)
        if raw is None:
            return None
        return json.loads(raw)

    def _remove_from_processing(self, job_id: str) -> None:
        """Remove job from processing list by job_id."""
        items = self._redis.lrange(self.PROCESSING_KEY, 0, -1)
        for item in items:
            try:
                data = json.loads(item)
                if data.get("job_id") == job_id:
                    self._redis.lrem(self.PROCESSING_KEY, 1, item)
                    break
            except (json.JSONDecodeError, KeyError):
                continue


def create_queue_backend() -> QueueBackend:
    """Create appropriate queue backend based on environment."""
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            return RedisQueueBackend(redis_url)
        except Exception as e:
            logger.warning(f"Failed to create Redis queue backend: {e}. Falling back to SQLite.")
    return SQLiteQueueBackend()


__all__ = [
    "QueueBackend",
    "SQLiteQueueBackend",
    "RedisQueueBackend",
    "create_queue_backend",
]
