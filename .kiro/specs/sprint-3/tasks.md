# Sprint 3: Tasks

## Phase 1: Real Audit Handler — Days 1-3

### Task 3.1.1: Full Audit Handler
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** L (6-8h)
- **Description:** Replace hello_audit with real audit that runs orchestrate.py
- **Deliverables:**
  - [ ] `apps/worker/handlers/full_audit.py`
  - [ ] Calls `orchestrate.run_full_audit()` with all parameters
  - [ ] Calls `calculate_scores.calculate_composite_score()`
  - [ ] Builds canonical `AuditResult` from `packages/schemas/models.py`
  - [ ] Emits progress events for each stage
  - [ ] Stores result in `audits.result_json`
- **Acceptance Criteria:**
  - [ ] Audit produces scores for technical/content/AI visibility
  - [ ] Progress events show: initializing → technical → content → ai_visibility → generating_report → completed
  - [ ] `AuditResult` stored with issues and recommendations
- **Dependencies:** Sprint 2 complete

### Task 3.1.2: Lease Renewal for Long Audits
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** S (2-3h)
- **Description:** Background task renews job lease during long-running audits
- **Deliverables:**
  - [ ] `renew_lease_task()` runs every LEASE_SECONDS/2
  - [ ] Cancels cleanly when audit completes
  - [ ] Integrated into full_audit handler
- **Acceptance Criteria:**
  - [ ] 5-minute audit doesn't timeout
  - [ ] Lease renewed automatically
- **Dependencies:** 3.1.1

### Task 3.1.3: Update Executor Dispatch
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** S (1-2h)
- **Description:** Route "audit" job type to full_audit handler
- **Deliverables:**
  - [ ] `executor.py` dispatches "audit" to `handle_full_audit`
  - [ ] Error mapping: SSRF → PermanentError, network → TransientError
  - [ ] Keep "hello_audit" for diagnostics
- **Acceptance Criteria:**
  - [ ] `POST /audit` triggers full_audit handler
  - [ ] Transient errors retry; permanent errors fail immediately
- **Dependencies:** 3.1.1

---

## Phase 2: Rate Limiting — Days 3-4

### Task 3.2.1: Rate Limiter Module
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (3-4h)
- **Description:** Rate limiting for external HTTP requests
- **Deliverables:**
  - [ ] `packages/seo_health_report/scripts/rate_limiter.py`
  - [ ] `RateLimiterConfig` dataclass with tier settings
  - [ ] `RateLimiter` class with semaphore + per-host throttling
  - [ ] `rate_limited_fetch()` wrapper for safe_fetch
  - [ ] `TIER_LIMITS` configuration (basic/pro/enterprise)
- **Acceptance Criteria:**
  - [ ] Concurrent fetches limited to config max
  - [ ] Per-host delay enforced between requests
  - [ ] Different limits per tier
- **Dependencies:** Sprint 2 safe_fetch

### Task 3.2.2: Integrate Rate Limiting
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** S (2h)
- **Description:** Use rate limiter in full_audit handler
- **Deliverables:**
  - [ ] Full audit creates RateLimiter based on tier
  - [ ] All fetches go through rate_limited_fetch
  - [ ] Pass rate limiter to orchestrate.run_full_audit
- **Acceptance Criteria:**
  - [ ] Audit respects rate limits during crawling
  - [ ] No more than N concurrent fetches
- **Dependencies:** 3.2.1, 3.1.1

---

## Phase 3: Report Generation — Days 4-6

### Task 3.3.1: HTML Report Generator
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (4-5h)
- **Description:** Generate HTML report from AuditResult
- **Deliverables:**
  - [ ] `packages/seo_health_report/scripts/generate_report.py`
  - [ ] `generate_html_report(audit_result, tenant_id) -> path`
  - [ ] Template with: overall score, component scores, issues, recommendations
  - [ ] Apply branding (use existing apply_branding.py)
  - [ ] Store in storage backend
- **Acceptance Criteria:**
  - [ ] HTML report generated for completed audit
  - [ ] Report includes all scores and top issues
  - [ ] Stored at predictable path
- **Dependencies:** 3.1.1

### Task 3.3.2: PDF Report Generator
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (3-4h)
- **Description:** Generate PDF from HTML report (stretch goal)
- **Deliverables:**
  - [ ] `generate_pdf_report(audit_result, tenant_id) -> path`
  - [ ] Use existing generate_premium_report.py or weasyprint/puppeteer
  - [ ] Fallback: return None if PDF generation unavailable
- **Acceptance Criteria:**
  - [ ] PDF generated when tooling available
  - [ ] Graceful fallback to HTML-only
- **Dependencies:** 3.3.1

### Task 3.3.3: DB Schema for Report Paths
- **Agent:** db-wizard
- **Status:** DONE
- **Effort:** S (1-2h)
- **Description:** Add report path columns to audits table
- **Deliverables:**
  - [ ] `infrastructure/migrations/versions/v004_report_columns.py`
  - [ ] Columns: report_html_path, report_pdf_path, callback_url, callback_delivered_at
- **Acceptance Criteria:**
  - [ ] Migration runs successfully
  - [ ] Audit record can store report paths
- **Dependencies:** None

### Task 3.3.4: Report Download Endpoint
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** S (2h)
- **Description:** API endpoint to download reports
- **Deliverables:**
  - [ ] `GET /audits/{audit_id}/report/html` returns HTML file
  - [ ] `GET /audits/{audit_id}/report/pdf` returns PDF file
  - [ ] 404 if report not available
- **Acceptance Criteria:**
  - [ ] Reports downloadable via API
  - [ ] Proper content-type headers
- **Dependencies:** 3.3.1, 3.3.3

---

## Phase 4: Webhook Callbacks — Days 6-7

### Task 3.4.1: Webhook Utility Module
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** M (3-4h)
- **Description:** Secure webhook delivery with signing and retries
- **Deliverables:**
  - [ ] `packages/seo_health_report/scripts/webhook.py`
  - [ ] `sign_webhook_payload(payload, secret) -> signature`
  - [ ] `validate_callback_url(url)` - block private IPs (reuse safe_fetch logic)
  - [ ] `deliver_webhook(url, payload, secret)` with retries
- **Acceptance Criteria:**
  - [ ] HMAC-SHA256 signature in X-Webhook-Signature header
  - [ ] Private IP callback URLs blocked
  - [ ] Retry with exponential backoff (max 5 attempts)
- **Dependencies:** Sprint 2 safe_fetch

### Task 3.4.2: Integrate Webhook Delivery
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** S (2h)
- **Description:** Call webhook on audit completion/failure
- **Deliverables:**
  - [ ] Full audit handler calls deliver_webhook if callback_url set
  - [ ] Payload includes: audit_id, status, scores, report_url
  - [ ] Update audit.callback_delivered_at on success
- **Acceptance Criteria:**
  - [ ] Webhook delivered on audit completion
  - [ ] Webhook delivered on audit failure (with error info, redacted)
  - [ ] Delivery timestamp recorded
- **Dependencies:** 3.4.1, 3.1.1

---

## Phase 5: API Enhancements — Days 7-8

### Task 3.5.1: Progress Events Endpoint
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** S (2h)
- **Description:** API to retrieve audit progress events
- **Deliverables:**
  - [ ] `GET /audits/{audit_id}/events` returns event timeline
  - [ ] Events include: event_type, message, progress_pct, timestamp
  - [ ] Ordered by created_at
- **Acceptance Criteria:**
  - [ ] Progress visible via API
  - [ ] Events match what worker wrote
- **Dependencies:** Sprint 2 progress_events table

### Task 3.5.2: Enhanced Audit Detail Endpoint
- **Agent:** code-surgeon
- **Status:** DONE
- **Effort:** S (2h)
- **Description:** Return full audit result with scores and issues
- **Deliverables:**
  - [ ] `GET /audits/{audit_id}/full` returns complete AuditResult
  - [ ] Include: scores, grade, issues, recommendations, report URLs
  - [ ] Handle in-progress audits (return partial data)
- **Acceptance Criteria:**
  - [ ] Full result accessible via API
  - [ ] Matches stored result_json
- **Dependencies:** 3.1.1

---

## Phase 6: Dashboard UI — Days 8-10

### Task 3.6.1: Dashboard Routes Setup
- **Agent:** frontend-designer
- **Status:** DONE
- **Effort:** M (2-3h)
- **Description:** FastAPI routes for dashboard pages
- **Deliverables:**
  - [ ] `apps/dashboard/routes.py`
  - [ ] Jinja2 template integration
  - [ ] Mount at `/dashboard`
- **Acceptance Criteria:**
  - [ ] Dashboard accessible at /dashboard
  - [ ] Templates render correctly
- **Dependencies:** None

### Task 3.6.2: Audit List View
- **Agent:** frontend-designer
- **Status:** DONE
- **Effort:** M (3-4h)
- **Description:** List all audits with status and scores
- **Deliverables:**
  - [ ] `apps/dashboard/templates/audit_list.html`
  - [ ] Table with: URL, company, status, score, grade, created_at
  - [ ] Status badges (queued/running/completed/failed)
  - [ ] Link to detail view
  - [ ] Tenant-scoped (if multi-tenant)
- **Acceptance Criteria:**
  - [ ] All audits visible in list
  - [ ] Sortable/filterable (basic)
  - [ ] Links work
- **Dependencies:** 3.6.1

### Task 3.6.3: Audit Detail View
- **Agent:** frontend-designer
- **Status:** DONE
- **Effort:** L (4-5h)
- **Description:** Single audit with progress, scores, and results
- **Deliverables:**
  - [ ] `apps/dashboard/templates/audit_detail.html`
  - [ ] Progress timeline (poll /events endpoint)
  - [ ] Score cards for overall/technical/content/AI visibility
  - [ ] Issues list (sorted by severity)
  - [ ] Recommendations list (sorted by priority)
  - [ ] Report download buttons
- **Acceptance Criteria:**
  - [ ] All audit data visible
  - [ ] Progress updates in real-time (polling)
  - [ ] Report links work
- **Dependencies:** 3.6.1, 3.5.1, 3.5.2

---

## Phase 7: Testing & Documentation — Days 10-11

### Task 3.7.1: Full Audit Test Suite
- **Agent:** test-architect
- **Status:** DONE
- **Effort:** M (3-4h)
- **Description:** Integration tests for full audit flow
- **Deliverables:**
  - [ ] `tests/test_full_audit.py`
  - [ ] Test: enqueue → claim → execute → complete
  - [ ] Test: progress events written correctly
  - [ ] Test: result stored in correct format
  - [ ] Mock external fetches
- **Acceptance Criteria:**
  - [ ] Full flow tested end-to-end
  - [ ] Tests pass in CI
- **Dependencies:** 3.1.1

### Task 3.7.2: Rate Limiter Tests
- **Agent:** test-architect
- **Status:** DONE
- **Effort:** S (2h)
- **Description:** Unit tests for rate limiting
- **Deliverables:**
  - [ ] `tests/test_rate_limiter.py`
  - [ ] Test: concurrency limit enforced
  - [ ] Test: per-host delay enforced
  - [ ] Test: tier-specific limits
- **Acceptance Criteria:**
  - [ ] Rate limiting behavior verified
- **Dependencies:** 3.2.1

### Task 3.7.3: Webhook Tests
- **Agent:** test-architect
- **Status:** DONE
- **Effort:** S (2h)
- **Description:** Unit tests for webhook delivery
- **Deliverables:**
  - [ ] `tests/test_webhook.py`
  - [ ] Test: signature generation
  - [ ] Test: callback URL validation (blocks private IPs)
  - [ ] Test: retry logic
- **Acceptance Criteria:**
  - [ ] Webhook security verified
- **Dependencies:** 3.4.1

### Task 3.7.4: Sprint 3 Documentation
- **Agent:** doc-smith
- **Status:** DONE
- **Effort:** M (2-3h)
- **Description:** Update docs for new features
- **Deliverables:**
  - [ ] `docs/audits.md` - How audits work end-to-end
  - [ ] `docs/reports.md` - Report generation and download
  - [ ] `docs/webhooks.md` - Webhook integration guide
  - [ ] Update README with dashboard instructions
- **Acceptance Criteria:**
  - [ ] New features documented
  - [ ] Integration guide for webhooks
- **Dependencies:** All other tasks

---

## Summary

| Phase | Tasks | Effort | Agents |
|-------|-------|--------|--------|
| Real Audit | 3.1.1, 3.1.2, 3.1.3 | L+S+S | code-surgeon |
| Rate Limiting | 3.2.1, 3.2.2 | M+S | code-surgeon |
| Report Generation | 3.3.1-3.3.4 | M+M+S+S | code-surgeon, db-wizard |
| Webhooks | 3.4.1, 3.4.2 | M+S | code-surgeon |
| API | 3.5.1, 3.5.2 | S+S | code-surgeon |
| Dashboard | 3.6.1-3.6.3 | M+M+L | frontend-designer |
| Testing | 3.7.1-3.7.4 | M+S+S+M | test-architect, doc-smith |

## Critical Path

```
3.1.1 Full Audit Handler
    ↓
3.1.3 Executor Dispatch ──→ 3.2.2 Rate Limiting Integration
    ↓
3.3.1 HTML Report ──→ 3.3.4 Report Download
    ↓
3.4.2 Webhook Integration
    ↓
3.5.1 + 3.5.2 API Endpoints
    ↓
3.6.2 + 3.6.3 Dashboard Views
    ↓
EXIT CRITERIA MET
```

## Exit Criteria Checklist
- [x] Real audit completes with scores for technical/content/AI visibility
- [x] HTML report generated and downloadable via API
- [x] Progress events visible (initializing → ... → completed)
- [x] Rate limiting enforced (per-host delay, global concurrency)
- [x] Webhook callback delivered on completion (if callback_url provided)
- [x] Dashboard shows audit list and detail views
