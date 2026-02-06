# Sprint 6: Tasks

## Overview
**Focus:** Web Dashboard MVP + Security/Quotas + E2E Testing
**Prerequisites:** Sprint 5 complete (833 tests, structured logging, webhooks, branding)
**Duration:** ~10-14 days

---

## Phase 1: Auth + Tenant Switch UI — Days 1-2

### Task 6.1.1: Login Page UI
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Create login page with RaapTech branding
- **Deliverables:**
  - [ ] `apps/dashboard/templates/login.html`
  - [ ] Email/password form with validation
  - [ ] Error message display
  - [ ] "Forgot password" link (stub)
  - [ ] Redirect to /dashboard on success
- **Acceptance Criteria:**
  - [ ] Form submits to POST /auth/login
  - [ ] Shows validation errors inline
  - [ ] Matches RaapTech dark theme (base.html)
  - [ ] Mobile responsive
- **Dependencies:** None

### Task 6.1.2: Session-Based Auth for Dashboard
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Add session/cookie auth for web dashboard
- **Deliverables:**
  - [ ] `apps/dashboard/auth.py` - Session management
  - [ ] Cookie-based session with secure flags
  - [ ] `get_current_dashboard_user` dependency
  - [ ] Login/logout routes in dashboard router
- **Acceptance Criteria:**
  - [ ] Sessions persist across requests
  - [ ] Secure cookies (HttpOnly, SameSite, Secure in prod)
  - [ ] Session expiry after 24h
  - [ ] Logout clears session
- **Dependencies:** 6.1.1

### Task 6.1.3: Tenant Context & Switch UI
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Display current tenant and allow switching (for multi-tenant users)
- **Deliverables:**
  - [ ] Tenant name in navbar (base.html update)
  - [ ] `apps/dashboard/templates/tenant_switch.html`
  - [ ] GET /dashboard/tenants - list user's tenants
  - [ ] POST /dashboard/switch-tenant - switch active tenant
- **Acceptance Criteria:**
  - [ ] Current tenant shown in UI
  - [ ] Users with multiple tenants can switch
  - [ ] Tenant switch updates session
  - [ ] Audits filtered by active tenant
- **Dependencies:** 6.1.2

### Task 6.1.4: User Settings Page
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Basic user settings/profile page
- **Deliverables:**
  - [ ] `apps/dashboard/templates/settings.html`
  - [ ] Display email, role, created date
  - [ ] Change password form
  - [ ] Link to branding settings (if admin)
- **Acceptance Criteria:**
  - [ ] Settings accessible from navbar
  - [ ] Password change works
  - [ ] Shows tenant info
- **Dependencies:** 6.1.2

---

## Phase 2: Audit Intake Flow — Days 3-4

### Task 6.2.1: New Audit Form UI
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Create comprehensive audit intake form
- **Deliverables:**
  - [ ] `apps/dashboard/templates/audit_new.html`
  - [ ] Fields: URL, company name, trade type dropdown, service areas
  - [ ] Tier selection with pricing info
  - [ ] Form validation (client-side)
  - [ ] Submit button with loading state
- **Acceptance Criteria:**
  - [ ] URL auto-prefixes https:// if missing
  - [ ] Trade types: Plumber, Electrician, HVAC, Roofer, General Contractor, Other
  - [ ] Service areas as comma-separated or multi-select
  - [ ] Tier shows features comparison
- **Dependencies:** 6.1.2

### Task 6.2.2: Trade Type & Service Area Models
- **Agent:** db-wizard
- **Status:** COMPLETE ✅
- **Effort:** S (1h)
- **Description:** Add trade type and service areas to Audit model
- **Deliverables:**
  - [ ] Add `trade_type` column to Audit
  - [ ] Add `service_areas` JSON column to Audit
  - [ ] Alembic migration (v007_audit_trade_fields.py)
- **Acceptance Criteria:**
  - [ ] Migration runs cleanly
  - [ ] Existing audits default to null trade_type
  - [ ] Service areas stored as JSON array
- **Dependencies:** None

### Task 6.2.3: Audit Creation Dashboard Route
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (2h)
- **Description:** Dashboard route to create audits
- **Deliverables:**
  - [ ] GET /dashboard/audits/new - show form
  - [ ] POST /dashboard/audits/new - create audit
  - [ ] Redirect to audit detail on success
  - [ ] Show errors on validation failure
- **Acceptance Criteria:**
  - [ ] Creates audit via internal API
  - [ ] Associates with current user/tenant
  - [ ] Shows in audit list immediately
- **Dependencies:** 6.2.1, 6.2.2

### Task 6.2.4: Audit Intake Tests
- **Agent:** test-architect
- **Status:** NOT STARTED
- **Effort:** M (2h)
- **Description:** Tests for audit intake flow
- **Deliverables:**
  - [ ] `tests/integration/test_audit_intake.py`
  - [ ] Form validation tests
  - [ ] Successful creation test
  - [ ] Tier selection test
- **Acceptance Criteria:**
  - [ ] All trade types accepted
  - [ ] Invalid URLs rejected
  - [ ] Tenant scoping verified
- **Dependencies:** 6.2.3

---

## Phase 3: Audit Status & Progress UI — Days 5-6

### Task 6.3.1: Progress Polling Component
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** JavaScript component for polling audit progress
- **Deliverables:**
  - [ ] `apps/dashboard/static/js/audit-progress.js`
  - [ ] Poll /audit/{id} every 3 seconds
  - [ ] Update progress bar and status text
  - [ ] Stop polling when completed/failed
- **Acceptance Criteria:**
  - [ ] No excessive polling (exponential backoff on errors)
  - [ ] Smooth progress bar animation
  - [ ] Works without page refresh
- **Dependencies:** None

### Task 6.3.2: Module Progress Display
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Show per-module progress in audit detail
- **Deliverables:**
  - [ ] Update `apps/dashboard/templates/audit_detail.html`
  - [ ] Module progress cards (Technical, Content, AI)
  - [ ] Individual module status indicators
  - [ ] Time elapsed display
- **Acceptance Criteria:**
  - [ ] Each module shows: pending/running/complete/failed
  - [ ] Overall progress percentage shown
  - [ ] Elapsed time updates in real-time
- **Dependencies:** 6.3.1

### Task 6.3.3: Error State Display
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Clean error display for failed/partial audits
- **Deliverables:**
  - [ ] Error message card in audit_detail.html
  - [ ] Partial results indication
  - [ ] Retry button (for failed audits)
  - [ ] Error code display
- **Acceptance Criteria:**
  - [ ] User-friendly error messages
  - [ ] Technical details hidden by default (expandable)
  - [ ] Clear indication of what succeeded vs failed
- **Dependencies:** 6.3.2

### Task 6.3.4: Progress Events API Enhancement
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (2h)
- **Description:** Enhance progress events for UI consumption
- **Deliverables:**
  - [ ] Add module_name to progress events
  - [ ] Add estimated_time_remaining
  - [ ] GET /audit/{id}/progress - optimized endpoint
- **Acceptance Criteria:**
  - [ ] Events include module context
  - [ ] Time estimates based on tier/page count
  - [ ] Response < 50ms
- **Dependencies:** None

---

## Phase 4: Results Viewer & Report Download — Days 7-8

### Task 6.4.1: Score Cards UI
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Display audit scores in visual cards
- **Deliverables:**
  - [ ] `apps/dashboard/templates/partials/score_card.html`
  - [ ] Overall score with grade badge
  - [ ] Module scores (Technical, Content, AI)
  - [ ] Score trend indicator (if previous audit exists)
- **Acceptance Criteria:**
  - [ ] Color-coded grades (A=green, B=blue, C=yellow, D=orange, F=red)
  - [ ] Animated score counter on load
  - [ ] Responsive grid layout
- **Dependencies:** 6.3.2

### Task 6.4.2: Top Fixes List
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Display prioritized fixes with evidence
- **Deliverables:**
  - [ ] `apps/dashboard/templates/partials/fixes_list.html`
  - [ ] Priority badges (Critical, High, Medium, Low)
  - [ ] Expandable evidence section
  - [ ] Link to affected URLs
- **Acceptance Criteria:**
  - [ ] Fixes sorted by priority
  - [ ] Evidence URLs are clickable
  - [ ] Impact estimate shown
  - [ ] Filter by priority level
- **Dependencies:** 6.4.1

### Task 6.4.3: Report Download UI
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Download buttons for HTML/PDF reports
- **Deliverables:**
  - [ ] Download buttons in audit_detail.html
  - [ ] Format selection (HTML, PDF)
  - [ ] Download progress indication
- **Acceptance Criteria:**
  - [ ] Downloads work via signed URL
  - [ ] File names include company name
  - [ ] Shows "generating" state if report not ready
- **Dependencies:** 6.4.1

### Task 6.4.4: Audit History List
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** M (2h)
- **Description:** Enhanced audit list with filters
- **Deliverables:**
  - [ ] Update `apps/dashboard/templates/audit_list.html`
  - [ ] Status filter (all/pending/completed/failed)
  - [ ] Date range filter
  - [ ] Search by URL/company
  - [ ] Pagination
- **Acceptance Criteria:**
  - [ ] Filters update URL params (bookmarkable)
  - [ ] 20 audits per page default
  - [ ] Sort by date (newest first)
- **Dependencies:** 6.1.2

---

## Phase 5: Rate Limiting & Quotas — Days 9-10

### Task 6.5.1: Per-Tenant Quota Model
- **Agent:** db-wizard
- **Status:** COMPLETE ✅
- **Effort:** S (1h)
- **Description:** Add quota tracking to tenant
- **Deliverables:**
  - [ ] `TenantQuota` model in database.py
  - [ ] Fields: monthly_audits_limit, monthly_audits_used, max_concurrent, max_pages_per_audit
  - [ ] Alembic migration (v008_tenant_quotas.py)
- **Acceptance Criteria:**
  - [ ] Quotas linked to tenant
  - [ ] Default quotas by tier (basic=10/mo, pro=50/mo, enterprise=unlimited)
- **Dependencies:** None

### Task 6.5.2: Quota Enforcement Service
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Service to check and enforce quotas
- **Deliverables:**
  - [ ] `packages/seo_health_report/quotas/service.py`
  - [ ] `check_quota(tenant_id, action)` function
  - [ ] `increment_usage(tenant_id, action)` function
  - [ ] `get_quota_status(tenant_id)` function
- **Acceptance Criteria:**
  - [ ] Returns clear error when quota exceeded
  - [ ] Concurrent audit limit enforced
  - [ ] Page limit per audit enforced
  - [ ] Monthly reset on billing cycle
- **Dependencies:** 6.5.1

### Task 6.5.3: Rate Limit Enhancement
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Enhance rate limiter with tier-based limits
- **Deliverables:**
  - [ ] Update `rate_limiter.py` with tier configs
  - [ ] Per-tenant rate limit overrides
  - [ ] X-RateLimit-* headers in responses
- **Acceptance Criteria:**
  - [ ] Basic: 100 req/min, Pro: 500 req/min, Enterprise: 2000 req/min
  - [ ] Headers show remaining/reset time
  - [ ] 429 response includes retry-after
- **Dependencies:** 6.5.2

### Task 6.5.4: Quota UI in Dashboard
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Display quota usage in dashboard
- **Deliverables:**
  - [ ] Quota widget in dashboard sidebar
  - [ ] Usage bar (X of Y audits used)
  - [ ] Warning at 80% usage
  - [ ] Link to upgrade
- **Acceptance Criteria:**
  - [ ] Real-time usage display
  - [ ] Clear visual warning near limit
  - [ ] Shows reset date
- **Dependencies:** 6.5.2

### Task 6.5.5: Quota Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Tests for quota enforcement
- **Deliverables:**
  - [ ] `tests/unit/test_quota_service.py`
  - [ ] `tests/integration/test_quota_enforcement.py`
  - [ ] Concurrent limit tests
  - [ ] Monthly reset tests
- **Acceptance Criteria:**
  - [ ] Quota exceeded returns 429
  - [ ] Concurrent limit blocks new audits
  - [ ] Monthly reset works correctly
- **Dependencies:** 6.5.2

---

## Phase 6: E2E Testing & Release Verification — Days 11-14

### Task 6.6.1: Fixture Sites Library
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Create test fixture sites with expected results
- **Deliverables:**
  - [ ] `tests/fixtures/sites.py` - Site definitions
  - [ ] `tests/fixtures/expected_results/` - Expected outputs
  - [ ] 5-10 fixture sites covering different scenarios
  - [ ] Documentation of each fixture's purpose
- **Acceptance Criteria:**
  - [ ] Sites cover: broken sitemap, redirect chains, missing schema, good site, crawl blocked
  - [ ] Expected results include score ranges
  - [ ] Fixtures can be run offline (mocked responses)
- **Dependencies:** None

### Task 6.6.2: Golden Path E2E Test
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** L (4-6h)
- **Description:** Full E2E test: submit → progress → results → download
- **Deliverables:**
  - [ ] `tests/e2e/test_golden_path.py`
  - [ ] Uses Playwright/Selenium for browser automation
  - [ ] Tests: login, create audit, wait for completion, verify score, download report
  - [ ] CI configuration for E2E
- **Acceptance Criteria:**
  - [ ] Runs in CI against staging env
  - [ ] Completes in < 5 minutes
  - [ ] Fails CI on regression
  - [ ] Screenshots on failure
- **Dependencies:** 6.6.1

### Task 6.6.3: Sequential Audit Stress Test
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Run 20 sequential audits without manual intervention
- **Deliverables:**
  - [ ] `tests/stress/test_sequential_audits.py`
  - [ ] 20 audits with varied parameters
  - [ ] Verify no stuck jobs
  - [ ] Report timing statistics
- **Acceptance Criteria:**
  - [ ] All 20 complete (success or partial)
  - [ ] No database deadlocks
  - [ ] Average completion time reported
  - [ ] No memory leaks (stable RSS)
- **Dependencies:** 6.6.1

### Task 6.6.4: Partial Results Verification
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (2h)
- **Description:** Verify partial results on failures
- **Deliverables:**
  - [ ] `tests/integration/test_partial_results.py`
  - [ ] Test timeout scenarios
  - [ ] Test API failure scenarios
  - [ ] Verify partial data saved
- **Acceptance Criteria:**
  - [ ] Audit marked "partial" not "failed" when some modules succeed
  - [ ] Partial results downloadable
  - [ ] Clear indication of what failed
- **Dependencies:** 6.6.1

### Task 6.6.5: verify_release.sh Script
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Release verification script
- **Deliverables:**
  - [ ] `scripts/verify_release.sh`
  - [ ] Runs: lint, unit tests, integration tests
  - [ ] Builds: API, worker, web
  - [ ] Runs: minimal mock audit
  - [ ] Prints: clear pass/fail summary
- **Acceptance Criteria:**
  - [ ] Exit code 0 only if all checks pass
  - [ ] Colored output (green=pass, red=fail)
  - [ ] Runs in < 10 minutes
  - [ ] Can be run locally or in CI
- **Dependencies:** 6.6.2

### Task 6.6.6: CI Pipeline Update
- **Agent:** devops-automator
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Update CI to run E2E and verify_release
- **Deliverables:**
  - [ ] Update `.github/workflows/ci.yml`
  - [ ] Add E2E job (runs on staging)
  - [ ] Add release verification job
  - [ ] Block merge on failure
- **Acceptance Criteria:**
  - [ ] E2E runs on PR to main
  - [ ] verify_release.sh gates deployment
  - [ ] Artifacts uploaded on failure
- **Dependencies:** 6.6.5

---

## Summary

| Phase | Tasks | Effort | Focus |
|-------|-------|--------|-------|
| Auth + Tenant UI | 6.1.1-6.1.4 | M+M+M+S | Authentication |
| Audit Intake | 6.2.1-6.2.4 | M+S+M+M | Intake Flow |
| Progress UI | 6.3.1-6.3.4 | M+M+S+M | Status Updates |
| Results Viewer | 6.4.1-6.4.4 | M+M+S+M | Results Display |
| Quotas | 6.5.1-6.5.5 | S+M+M+S+M | Rate Limiting |
| E2E Testing | 6.6.1-6.6.6 | M+L+M+M+M+S | Verification |

**Total Tasks:** 24
**Estimated Duration:** 10-14 days

## Critical Path

```
6.1.1 Login UI ──→ 6.1.2 Session Auth ──→ 6.1.3 Tenant Switch ──→ 6.1.4 Settings
                         ↓
6.2.2 Trade Fields ──→ 6.2.1 Audit Form ──→ 6.2.3 Create Route ──→ 6.2.4 Tests
                                                    ↓
6.3.4 Progress API ──→ 6.3.1 Polling ──→ 6.3.2 Module Progress ──→ 6.3.3 Errors
                                                    ↓
                        6.4.1 Score Cards ──→ 6.4.2 Fixes List ──→ 6.4.3 Download
                                                    ↓
6.5.1 Quota Model ──→ 6.5.2 Quota Service ──→ 6.5.3 Rate Limits ──→ 6.5.5 Tests
                                                    ↓
6.6.1 Fixtures ──→ 6.6.2 Golden Path E2E ──→ 6.6.5 verify_release.sh ──→ 6.6.6 CI
                         ↓
              6.6.3 Stress Test + 6.6.4 Partial Results
                         ↓
                    EXIT CRITERIA MET
```

## Exit Criteria Checklist
- [ ] Login/logout works in dashboard
- [ ] Tenant switching works for multi-tenant users
- [ ] Audit intake form creates audits
- [ ] Progress polling shows real-time updates
- [ ] Score cards display for completed audits
- [ ] Report download works (HTML + PDF)
- [ ] Rate limiting by tier enforced
- [ ] Per-tenant quotas enforced
- [ ] Golden path E2E passes in CI
- [ ] 20 sequential audits complete without intervention
- [ ] Partial results return cleanly on failure
- [ ] verify_release.sh passes
- [ ] Test count >900 (currently 833)
- [ ] All CI checks pass

## Quick Start

To begin Sprint 6, start with Task 6.1.1 (Login Page UI):

```bash
# Create login template
touch apps/dashboard/templates/login.html

# Run tests after implementation
python3 -m pytest tests/ -v --ignore=tests/unit/test_async_operations.py --ignore=tests/test_cache.py
```

## Notes

- Existing auth.py has JWT-based auth; dashboard needs session-based auth
- Dashboard templates use Tailwind CSS dark mode (see base.html)
- Rate limiter exists in rate_limiter.py; needs tier-based enhancement
- Admin health dashboard already at /admin/health
- Metrics endpoint at /metrics for monitoring
