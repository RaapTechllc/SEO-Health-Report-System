# Sprint 2: Job Framework + Worker Wiring + Safe Fetching

## Overview
Build the async job infrastructure for production audit processing with progress tracking and security protections.

## Duration
Weeks 3-4 (2-week sprint)

## Goal
Audits run async with progress tracking; safe fetch client exists.

## Business Requirements

### BR-1: Async Audit Processing
- **Description**: Audits must run asynchronously via a worker process, not inline with API requests
- **Rationale**: Production audits can take minutes; blocking API requests is not viable
- **Success Metric**: API returns audit_id in <200ms; actual work happens in background

### BR-2: Observable Progress
- **Description**: Users and operators must see audit progress (queued → running → done/failed)
- **Rationale**: Long-running jobs need visibility for debugging and user confidence
- **Success Metric**: DB reflects accurate status transitions; API can surface current state

### BR-3: Idempotent Requests
- **Description**: Duplicate audit requests must not create duplicate work
- **Rationale**: Prevents accidental double-billing, wasted resources, and data inconsistency
- **Success Metric**: Same request submitted twice returns existing audit, not new row

### BR-4: Secure Fetching
- **Description**: HTTP fetching must block SSRF attacks (private IPs, metadata endpoints, redirects)
- **Rationale**: Audit target URLs are user-provided; must not allow access to internal resources
- **Success Metric**: All SSRF test vectors blocked; no access to 127.0.0.1, 169.254.x, private ranges

### BR-5: No Secret Leakage
- **Description**: Logs, error messages, and DB events must not contain API keys, tokens, or credentials
- **Rationale**: Event logs are queryable; secrets in logs = security incident
- **Success Metric**: Forced errors store redacted strings only

## Functional Requirements

### FR-1: Job Enqueue
- API endpoint enqueues audit job to database
- Returns audit_id immediately
- Job visible as `queued` status

### FR-2: Worker Execution
- Worker polls for available jobs
- Claims job with lease (prevents double-processing)
- Executes audit handler
- Marks job `done` or `failed`

### FR-3: Progress Events
- Worker writes events: queued, running, step progress, done/failed
- Events are append-only (audit trail)
- Current status derivable from latest event

### FR-4: Idempotency
- Compute hash from (tenant, URL, options, recipe version)
- Reject duplicate enqueue with existing audit reference
- Retries don't corrupt state

### FR-5: Safe HTTP Client
- Only http/https schemes allowed
- DNS resolution validates IP before connect
- Block private/reserved/loopback/link-local ranges (IPv4 + IPv6)
- Validate every redirect hop
- Enforce timeout and response size limits

### FR-6: Redaction
- Utility function strips secrets from strings/dicts
- Applied to: job errors, progress events, HTTP error paths
- Patterns: API keys, Authorization headers, cookies, token params

## Non-Functional Requirements

### NFR-1: Reliability
- Two concurrent workers must not double-process same job
- Crashed worker's job must be re-claimable after lease expires
- Transient failures retry with exponential backoff

### NFR-2: Performance
- API enqueue response <200ms
- Worker job claim <50ms
- Progress event writes <10ms

### NFR-3: Security
- SSRF protection is mandatory, not optional
- No secrets in any persistent storage (logs, DB, files)

## Exit Criteria
- [ ] "Hello audit" job completes end-to-end without manual intervention
- [ ] Progress changes show in DB (queued → running → done)
- [ ] SSRF unit tests pass (private IPs blocked)

## Dependencies
- Sprint 1 carryover: Env Config, Shared Schemas, DB Migrations (must complete first)
