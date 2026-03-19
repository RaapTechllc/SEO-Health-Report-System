# Job System Documentation

## Overview

The SEO Health Report System uses a database-backed job queue for processing audit requests asynchronously. Jobs are stored in the `audit_jobs` table and processed by worker instances that poll for available work.

## Running the Worker Locally

```bash
python apps/worker/main.py
```

## Required Environment Variables

Reference `.env.example` for all configuration options.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `WORKER_LEASE_SECONDS` | How long a worker holds a job lock | 300 |
| `APP_ENV` | Environment (development/staging/production) | development |

## Job Lifecycle

```
queued → running → done/failed
```

1. **queued**: Job created, waiting for a worker
2. **running**: Worker has acquired lease and is processing
3. **done**: Audit completed successfully
4. **failed**: Audit failed after exhausting retries

## Database Schema

### `audit_jobs` Table

| Column | Description |
|--------|-------------|
| `status` | Current job state (queued/running/done/failed) |
| `attempt` | Current attempt number |
| `max_attempts` | Maximum retry attempts before permanent failure |
| `locked_until` | Timestamp when current lease expires |
| `locked_by` | Worker instance ID holding the lease |
| `last_error` | Most recent error message |

### `audit_progress_events` Table

| Column | Description |
|--------|-------------|
| `event_type` | Type of progress event |
| `message` | Human-readable status message |
| `progress_pct` | Completion percentage (0-100) |

## Lease Renewal

Long-running audits automatically renew their lease every `WORKER_LEASE_SECONDS / 2` to prevent other workers from stealing the job. If a worker crashes, the lease expires and another worker can pick up the job.

## Debugging Stuck Jobs

Check these fields to diagnose issues:

```sql
SELECT id, status, locked_until, locked_by, last_error, attempt
FROM audit_jobs
WHERE status = 'running' AND locked_until < NOW();
```

- **locked_until < NOW()**: Lease expired, worker likely crashed
- **attempt = max_attempts**: Job exhausted retries
- **last_error**: Contains the failure reason

## Retry Behavior

- **Exponential backoff**: Wait time doubles with each attempt
- **Max attempts**: Jobs fail permanently after `max_attempts` (default: 3)
- **Automatic unlock**: Expired leases allow retry by any worker
