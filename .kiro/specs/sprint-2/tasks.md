# Sprint 2: Tasks

## Prerequisites (Sprint 1 Carryover) — Days 1-2

### Task 2.0.1: Env Config + Secrets
- **Agent:** devops-automator
- **Status:** DONE
- **Effort:** M (2-4h)
- **Description:** Single source of truth for env vars across API, worker, and CI
- **Deliverables:**
  - [ ] `.env.example` with all required vars documented
  - [ ] Secrets loading strategy (dotenv for local, env injection for prod)
  - [ ] Safe defaults: network fetch disabled unless explicitly enabled
  - [ ] CI boots with dummy keys (no secrets required for unit tests)
- **Acceptance Criteria:**
  - [ ] API and worker boot with `ENV=local` using `.env`
  - [ ] CI runs without real API keys
  - [ ] Staging/prod inject secrets without code changes
- **Dependencies:** None

### Task 2.0.2: Shared Schemas Package
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (2-4h)
- **Description:** Canonical models shared between API and worker
- **Deliverables:**
  - [ ] `packages/shared-schemas/jobs.py` with:
    - `AuditJobPayload` dataclass
    - `AuditStatus` enum (queued, running, done, failed, canceled)
    - `ProgressEvent` dataclass
    - `RedactedLogEvent` dataclass
- **Acceptance Criteria:**
  - [ ] API and worker import same schema package
  - [ ] Schema changes enforced by mypy
  - [ ] No duplicated enums/DTOs
- **Dependencies:** None

### Task 2.0.3: DB Schema v1 + Migrations
- **Agent:** db-wizard
- **Status:** DONE
- **Effort:** L (4-8h)
- **Description:** Postgres migrations for audits, jobs, and progress events
- **Deliverables:**
  - [ ] `infrastructure/migrations/001_base_schema.sql` (if not exists)
  - [ ] `infrastructure/migrations/002_audit_jobs.sql`
  - [ ] `infrastructure/migrations/003_progress_events.sql`
  - [ ] Migration rollback scripts
- **Acceptance Criteria:**
  - [ ] `migrate up` works from empty DB locally and in CI
  - [ ] DB constraints prevent impossible states
  - [ ] Indexes support efficient job claiming
- **Dependencies:** None

---

## Phase 1: Job Framework — Days 3-5

### Task 2.1.1: Job Table + State Machine
- **Agent:** db-wizard
- **Status:** DONE
- **Effort:** M (2-4h)
- **Description:** Create audit_jobs table with proper constraints
- **Deliverables:**
  - [ ] `audit_jobs` table with columns:
    - job_id, tenant_id, audit_id
    - status (queued|running|done|failed|canceled)
    - attempt, max_attempts
    - queued_at, started_at, finished_at
    - locked_until, locked_by (lease management)
    - idempotency_key (unique)
    - payload_json
    - last_error (redacted)
  - [ ] Check constraints for status values
  - [ ] Index on claimable jobs
- **Acceptance Criteria:**
  - [ ] Status transitions enforced via constraints
  - [ ] Unique constraint on idempotency_key
  - [ ] Efficient index for job claiming query
- **Dependencies:** 2.0.3

### Task 2.1.2: Worker Runner
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** L (6-8h)
- **Description:** Worker process that polls, claims, and executes jobs
- **Deliverables:**
  - [ ] `apps/worker/main.py` - entrypoint with graceful shutdown
  - [ ] `apps/worker/executor.py` - job claim + execute logic
  - [ ] Postgres leasing with `SELECT FOR UPDATE SKIP LOCKED`
  - [ ] Exponential backoff + jitter for retries
  - [ ] Lease renewal for long-running jobs
- **Acceptance Criteria:**
  - [ ] Two workers don't double-process same job
  - [ ] Crashed worker's job re-claimable after lease expires
  - [ ] Unit tests cover: claim logic, retry increments, lease expiry
- **Dependencies:** 2.1.1, 2.0.2

### Task 2.1.3: API Enqueue Wiring
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (2-4h)
- **Description:** API endpoint enqueues job instead of inline execution
- **Deliverables:**
  - [ ] `POST /audits` creates audit record + job record
  - [ ] Returns audit_id immediately (no blocking)
  - [ ] Computes idempotency_key and checks for duplicates
- **Acceptance Criteria:**
  - [ ] API returns in <200ms (local)
  - [ ] Job visible as `queued` in DB
  - [ ] Duplicate request returns existing audit
- **Dependencies:** 2.1.1, 2.3.1

---

## Phase 2: Progress & Observability — Days 5-6

### Task 2.2.1: Progress/Event Schema
- **Agent:** db-wizard
- **Status:** DONE
- **Effort:** M (2-4h)
- **Description:** Append-only event log for audit progress
- **Deliverables:**
  - [ ] `audit_progress_events` table with:
    - event_id, audit_id, job_id, created_at
    - event_type (status_changed, step_started, step_done, warning, error, metric)
    - message (redacted), data_json (redacted), progress_pct
  - [ ] Index for timeline queries
  - [ ] Helper functions for writing events
- **Acceptance Criteria:**
  - [ ] Events are append-only (no updates/deletes)
  - [ ] Timeline query performs well (index scan)
  - [ ] `GET /audits/{id}` reflects latest status
- **Dependencies:** 2.0.3

### Task 2.2.2: Hello Audit Handler
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (3-4h)
- **Description:** Minimal audit that exercises full pipeline
- **Deliverables:**
  - [ ] `apps/worker/handlers/hello_audit.py`
  - [ ] Fetches homepage HTML using safe_fetch
  - [ ] Extracts: title, status_code, final_url, html_hash
  - [ ] Writes progress events: started, fetching, parsing, done
  - [ ] Stores result in audit_results table
- **Acceptance Criteria:**
  - [ ] End-to-end: enqueue → worker run → DB status `done`
  - [ ] Result stored with title + status_code
  - [ ] Progress events visible in DB
- **Dependencies:** 2.1.2, 2.2.1, 2.4.1

---

## Phase 3: Idempotency — Days 6-7

### Task 2.3.1: Audit Hashing + Canonicalization
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (3-4h)
- **Description:** Deterministic hash for deduplication
- **Deliverables:**
  - [ ] `packages/seo_health_report/scripts/idempotency.py`
  - [ ] `compute_idempotency_key(tenant_id, url, options, version)`
  - [ ] URL canonicalization:
    - Lowercase scheme/host
    - Strip default ports (80, 443)
    - Normalize trailing slash
    - Remove fragments
  - [ ] Options JSON sorted keys
  - [ ] Recipe version string for invalidation
- **Acceptance Criteria:**
  - [ ] Same input always produces same hash
  - [ ] Duplicate requests return existing audit
  - [ ] Unit tests cover edge cases (http/https, ports, slashes)
- **Dependencies:** 2.0.2

---

## Phase 4: Safe Fetching — Days 7-9

### Task 2.4.1: SSRF-Protected HTTP Client
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** L (6-8h)
- **Description:** HTTP client that blocks SSRF attacks
- **Deliverables:**
  - [ ] `packages/seo_health_report/scripts/safe_fetch.py`
  - [ ] `safe_fetch(url, timeout, max_bytes, max_redirects, user_agent)`
  - [ ] Scheme validation (http/https only)
  - [ ] Credentials rejection (no user:pass in URL)
  - [ ] DNS resolution before connect
  - [ ] IP validation against blocked ranges:
    - IPv4: 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16
    - IPv6: ::1/128, fc00::/7, fe80::/10
  - [ ] Redirect hop validation (re-check each Location)
  - [ ] Timeout and size limits
- **Acceptance Criteria:**
  - [ ] Blocks localhost, private IPs, metadata IP
  - [ ] Blocks redirect-to-private attacks
  - [ ] Blocks non-http schemes (file://, gopher://)
  - [ ] Happy path works for public URLs
- **Dependencies:** None

### Task 2.4.2: SSRF Test Suite
- **Agent:** test-architect
- **Status:** DONE
- **Effort:** M (3-4h)
- **Description:** Comprehensive SSRF protection tests
- **Deliverables:**
  - [ ] `tests/test_safe_fetch.py`
  - [ ] Tests for each blocked range (IPv4 + IPv6)
  - [ ] Redirect-to-private tests
  - [ ] Scheme validation tests
  - [ ] Credential rejection tests
  - [ ] Happy path with mocked transport
- **Acceptance Criteria:**
  - [ ] 100% coverage of blocked patterns
  - [ ] All SSRF tests pass in CI
  - [ ] Exit criteria: "SSRF unit tests pass"
- **Dependencies:** 2.4.1

---

## Phase 5: Security — Days 9-10

### Task 2.5.1: Redaction Utility
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (2-3h)
- **Description:** Strip secrets from strings before logging/storage
- **Deliverables:**
  - [ ] `packages/seo_health_report/scripts/redaction.py`
  - [ ] `redact_sensitive(text) -> str`
  - [ ] `redact_dict(data) -> dict`
  - [ ] Patterns for:
    - API keys (*_API_KEY, token, secret)
    - Authorization headers
    - Cookies
    - Query params (token=, key=, signature=)
- **Acceptance Criteria:**
  - [ ] Secrets removed from strings and nested dicts
  - [ ] Integration with job error storage
  - [ ] Integration with progress event writes
- **Dependencies:** None

### Task 2.5.2: Redaction Tests
- **Agent:** test-architect
- **Status:** DONE
- **Effort:** S (1-2h)
- **Description:** Prove secrets never reach storage
- **Deliverables:**
  - [ ] `tests/test_redaction.py`
  - [ ] Tests for each redaction pattern
  - [ ] Nested dict redaction tests
  - [ ] Integration test: forced error stores redacted string
- **Acceptance Criteria:**
  - [ ] All redaction patterns verified
  - [ ] No raw headers in stored events
- **Dependencies:** 2.5.1

---

## Phase 6: Supporting — Days 10-11

### Task 2.6.1: Worker Docker/K8s Manifest
- **Agent:** devops-automator
- **Status:** DONE
- **Effort:** M (2-4h)
- **Description:** Worker execution target for deployment
- **Deliverables:**
  - [ ] `infrastructure/docker/worker.Dockerfile`
  - [ ] `docker-compose.yml` updated with worker service
  - [ ] K8s manifest (if using): `infrastructure/k8s/worker-deployment.yaml`
  - [ ] Health check endpoint for worker
- **Acceptance Criteria:**
  - [ ] Worker boots in docker-compose
  - [ ] Worker boots in CI/staging
  - [ ] Graceful shutdown on SIGTERM
- **Dependencies:** 2.1.2

### Task 2.6.2: Status UI Indicator
- **Agent:** frontend-designer
- **Status:** DONE
- **Effort:** S (2-3h)
- **Description:** Show audit status in dashboard
- **Deliverables:**
  - [ ] Status pill component (queued/running/done/failed)
  - [ ] Refresh status button
  - [ ] Progress percentage (if available)
- **Acceptance Criteria:**
  - [ ] Status visible in audit list
  - [ ] Colors match score-* semantics
  - [ ] Refresh works without page reload
- **Dependencies:** 2.2.1

### Task 2.6.3: Job System Documentation
- **Agent:** doc-smith
- **Status:** DONE
- **Effort:** M (2-3h)
- **Description:** Runbook for operating job system
- **Deliverables:**
  - [ ] `docs/jobs.md` - How jobs run
    - Running worker locally
    - Required env vars
    - Debugging stuck jobs
    - Retry behavior
  - [ ] `docs/security.md` - SSRF protections
    - What is blocked
    - What is allowed
    - How to add allowlist entries
- **Acceptance Criteria:**
  - [ ] New developer can run worker locally from docs
  - [ ] Ops can diagnose stuck job from docs
- **Dependencies:** 2.1.2, 2.4.1

---

## Summary

| Phase | Tasks | Effort | Agents |
|-------|-------|--------|--------|
| Prerequisites | 2.0.1, 2.0.2, 2.0.3 | M+M+L | devops, code-surgeon, db-wizard |
| Job Framework | 2.1.1, 2.1.2, 2.1.3 | M+L+M | db-wizard, code-surgeon |
| Progress | 2.2.1, 2.2.2 | M+M | db-wizard, code-surgeon |
| Idempotency | 2.3.1 | M | code-surgeon |
| Safe Fetching | 2.4.1, 2.4.2 | L+M | code-surgeon, test-architect |
| Security | 2.5.1, 2.5.2 | M+S | code-surgeon, test-architect |
| Supporting | 2.6.1, 2.6.2, 2.6.3 | M+S+M | devops, frontend, doc-smith |

## Critical Path
```
2.0.1 Env Config
    ↓
2.0.3 DB Migrations → 2.1.1 Job Table → 2.1.2 Worker Runner
                                              ↓
2.4.1 Safe Fetch ────────────────────→ 2.2.2 Hello Audit
                                              ↓
2.2.1 Progress Events ───────────────→ EXIT CRITERIA MET
```

## Exit Criteria Checklist
- [x] "Hello audit" job completes end-to-end without manual intervention
- [x] Progress changes show in DB (queued → running → done)
- [x] SSRF unit tests pass (private IPs blocked)
