# Sprint 3: Real Audits + Reports + Production Hardening

## Overview
Replace the hello_audit with real audit handlers that run technical/content/AI visibility audits, generate reports, and support production workflows with rate limiting and webhooks.

## Duration
Weeks 5-6 (2-week sprint)

## Goal
Real audits run end-to-end with report generation; production-ready with rate limiting and webhooks.

## Business Requirements

### BR-1: Real Audit Execution
- **Description**: Audits must run the full technical/content/AI visibility pipeline via the job queue
- **Rationale**: The hello_audit was a proof-of-concept; users need actual SEO analysis
- **Success Metric**: Audit produces scores for all three components with issues and recommendations

### BR-2: Report Generation
- **Description**: Each completed audit generates downloadable HTML and PDF reports
- **Rationale**: Users need shareable, branded reports for their clients
- **Success Metric**: Reports accessible via API; HTML always generated, PDF when possible

### BR-3: Rate Limiting
- **Description**: External API calls and crawling must respect rate limits
- **Rationale**: Prevent overwhelming target sites and hitting API quotas
- **Success Metric**: Configurable per-host delays; global concurrency limits enforced

### BR-4: Webhook Callbacks
- **Description**: Notify external systems when audits complete or fail
- **Rationale**: Enable integrations and automation workflows
- **Success Metric**: Signed webhook payloads delivered with retry logic

### BR-5: Dashboard Visibility
- **Description**: Minimal UI to view audit list, details, progress, and reports
- **Rationale**: Internal users need visibility without API tooling
- **Success Metric**: List/detail views with progress timeline and report links

## Functional Requirements

### FR-1: Full Audit Handler
- Worker handler calls `orchestrate.run_full_audit()`
- Computes composite score via `calculate_scores.calculate_composite_score()`
- Emits progress events: initializing → technical → content → ai_visibility → generating_report → completed
- Stores canonical `AuditResult` in `audits.result_json`

### FR-2: Result Storage
- Persist structured results matching `AuditResult` schema
- Store both raw section outputs and normalized summary
- Update audit record with overall_score, grade, component scores

### FR-3: Report Artifacts
- Generate HTML report from `AuditResult`
- Generate PDF report (stretch: HTML-only if PDF tooling unavailable)
- Store artifacts at `{tenant_id}/{audit_id}/report.html` and `.pdf`
- Persist paths in audit record

### FR-4: Progress API
- `GET /audits/:id/events` returns progress timeline
- Events include stage, percent, message, timestamp
- Enable polling or streaming for real-time updates

### FR-5: Rate Limiting
- Per-host crawl throttling (configurable min delay)
- Global concurrency semaphore (max simultaneous fetches)
- Per-provider API limits (requests/minute, backoff on 429)

### FR-6: Webhook Delivery
- POST to `callback_url` on audit completion/failure
- Payload includes audit_id, status, scores, report_urls
- HMAC signature header for verification
- Exponential backoff retries (max 5 attempts)
- Validate callback URL (block private IPs like safe_fetch)

### FR-7: Dashboard Views
- Audit list: status, url, score, grade, created_at
- Audit detail: progress timeline, scores, issues, recommendations
- Report download links
- Tenant-scoped with RBAC

## Non-Functional Requirements

### NFR-1: Performance
- Audit completion within 5 minutes for typical sites
- Report generation < 30 seconds
- API responses < 200ms

### NFR-2: Reliability
- Lease renewal for long-running audits (prevent timeout)
- Transient errors (network, 429) retry with backoff
- Permanent errors (SSRF, 404) fail immediately

### NFR-3: Security
- SSRF protection on all fetches (existing safe_fetch)
- Callback URL validation (block private IPs)
- Redaction on all stored errors and webhook payloads
- HMAC signatures on webhook deliveries

### NFR-4: Scalability
- Multiple workers can run audits concurrently
- Rate limits per worker, not globally (simple model)

## Exit Criteria
- [ ] Real audit completes with scores for technical/content/AI visibility
- [ ] HTML report generated and downloadable via API
- [ ] Progress events visible in DB (initializing → ... → completed)
- [ ] Rate limiting enforced (per-host delay, global concurrency)
- [ ] Webhook callback delivered on completion (if callback_url provided)
- [ ] Dashboard shows audit list and detail views

## Dependencies
- Sprint 2: Job queue, worker, safe_fetch, redaction, progress events
- Existing: orchestrate.py, calculate_scores.py, report generation scripts
