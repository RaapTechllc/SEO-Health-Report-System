# Sprint 5: Tasks

## Overview
**Focus:** Observability, Webhooks, Report Customization & API Polish
**Prerequisites:** Sprint 4 complete (481 tests, CI/CD, rate limiting)
**Duration:** ~5-7 days

---

## Phase 1: Structured Logging & Metrics — Days 1-2

### Task 5.1.1: Structured JSON Logger
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Create structured logging with JSON output and request correlation
- **Deliverables:**
  - [x] `packages/seo_health_report/logging/structured_logger.py`
  - [x] `packages/seo_health_report/logging/middleware.py`
  - [x] ContextVar for request_id and user_id propagation
  - [x] JSONFormatter for structured output
- **Acceptance Criteria:**
  - [x] All logs output as JSON with timestamp, level, request_id
  - [x] X-Request-ID header added to responses
  - [x] Log messages include user_id when authenticated
- **Dependencies:** None
- **Notes:** 37 tests added (test_structured_logging.py, test_logging_middleware.py)

### Task 5.1.2: Metrics Collection System
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Implement in-memory metrics collection with Prometheus export
- **Deliverables:**
  - [x] `packages/seo_health_report/metrics/collector.py`
  - [x] `packages/seo_health_report/metrics/middleware.py`
  - [x] Counter, Histogram, Gauge support
  - [x] `/metrics` endpoint with Prometheus format
- **Acceptance Criteria:**
  - [x] `http_requests_total` counter increments
  - [x] `http_request_duration_seconds` histogram tracks latency
  - [x] `GET /metrics` returns Prometheus text format
  - [x] Metrics collection < 1ms overhead
- **Dependencies:** 5.1.1
- **Notes:** 51 tests added (test_metrics_collector.py, test_metrics_middleware.py)

### Task 5.1.3: Audit Metrics Integration
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Add audit-specific metrics to pipeline
- **Deliverables:**
  - [x] `audit_total{tier, status}` counter
  - [x] `audit_duration_seconds{tier}` histogram
  - [x] `active_audits` gauge
  - [x] Metrics emit from `run_audit_task()` in apps/api/main.py
- **Acceptance Criteria:**
  - [x] Completed audits increment counter
  - [x] Audit duration tracked by tier
  - [x] Active audit count accurate
- **Dependencies:** 5.1.2
- **Notes:** 19 tests added (test_audit_metrics.py), total 588 tests passing

---

## Phase 2: Webhook System — Days 3-4

### Task 5.2.1: Webhook Database Schema
- **Agent:** db-wizard
- **Status:** COMPLETE ✅
- **Effort:** S (1h)
- **Description:** Add webhook and webhook_deliveries tables
- **Deliverables:**
  - [x] `Webhook` model in database.py
  - [x] `WebhookDelivery` model for delivery tracking
  - [x] Indexes on tenant_id, webhook_id
  - [x] Alembic migration (v005_webhooks.py)
- **Acceptance Criteria:**
  - [x] Tables created with `alembic upgrade head`
  - [x] Foreign keys enforced
  - [x] Indexes present for common queries
- **Dependencies:** None
- **Notes:** Added relationship to Tenant model

### Task 5.2.2: Webhook Service Implementation
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (3-4h)
- **Description:** Implement webhook delivery with HMAC signing and retries
- **Deliverables:**
  - [x] `packages/seo_health_report/webhooks/service.py`
  - [x] `packages/seo_health_report/webhooks/security.py`
  - [x] HMAC-SHA256 payload signing
  - [x] Exponential backoff retries (5 attempts: 1m, 5m, 15m, 1h, 4h)
  - [x] SSRF-protected URL validation (blocks private IPs, localhost, metadata endpoints)
- **Acceptance Criteria:**
  - [x] Webhook delivered within 10 seconds (DELIVERY_TIMEOUT)
  - [x] X-Webhook-Signature header present
  - [x] Private IPs rejected
  - [x] Retries on 5xx/timeout
- **Dependencies:** 5.2.1
- **Notes:** 59 tests added (test_webhook_security.py, test_webhook_service.py)

### Task 5.2.3: Webhook API Endpoints
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Create CRUD API for webhook management
- **Deliverables:**
  - [x] `apps/api/routers/webhooks.py`
  - [x] POST /webhooks - register
  - [x] GET /webhooks - list
  - [x] GET /webhooks/{id} - get details
  - [x] DELETE /webhooks/{id} - remove
  - [x] GET /webhooks/{id}/deliveries - delivery log
  - [x] POST /webhooks/{id}/test - test webhook
- **Acceptance Criteria:**
  - [x] Webhooks scoped to tenant
  - [x] Secret generated on create (not returned after)
  - [x] Delivery history queryable
- **Dependencies:** 5.2.2
- **Notes:** Router mounted at /webhooks in main.py, total 647 tests passing

### Task 5.2.4: Audit Completion Webhooks
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (2h)
- **Description:** Fire webhooks when audits complete or fail
- **Deliverables:**
  - [x] Hook into audit completion flow (fire_audit_webhook helper in apps/api/main.py)
  - [x] Fire `audit.completed` event
  - [x] Fire `audit.failed` event
  - [x] Include audit result in payload
- **Acceptance Criteria:**
  - [x] Webhook fires within 5s of completion
  - [x] Payload includes audit_id, score, grade
  - [x] Failed audits include error message
- **Dependencies:** 5.2.3
- **Notes:** Added fire_audit_webhook helper, integrated into run_audit_task with tenant_id parameter

### Task 5.2.5: Webhook Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Unit and integration tests for webhook system
- **Deliverables:**
  - [x] `tests/unit/test_webhook_service.py` (20 tests)
  - [x] `tests/unit/test_webhook_security.py` (24 tests)
  - [x] `tests/unit/test_audit_webhooks.py` (15 tests)
  - [x] `tests/integration/test_webhook_api.py` (10 tests)
  - [x] SSRF protection tests
- **Acceptance Criteria:**
  - [x] >90% coverage on webhook code
  - [x] Retry logic tested
  - [x] SSRF blocking verified
- **Dependencies:** 5.2.4
- **Notes:** 671 total tests passing (up from 647)

---

## Phase 3: Report Customization — Day 5

### Task 5.3.1: Tenant Branding Schema
- **Agent:** db-wizard
- **Status:** COMPLETE ✅
- **Effort:** S (30min)
- **Description:** Add tenant_branding table
- **Deliverables:**
  - [x] `TenantBranding` model in database.py
  - [x] Fields: logo_url, primary_color, secondary_color, footer_text
  - [x] One-to-one with Tenant (uselist=False relationship)
  - [x] Alembic migration (v006_tenant_branding.py)
- **Acceptance Criteria:**
  - [x] Table created with unique constraint on tenant_id
  - [x] Color format validated (hex) in service layer
- **Dependencies:** None
- **Notes:** Added TenantBranding model with relationship to Tenant

### Task 5.3.2: Branding API Endpoints
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (2h)
- **Description:** API for managing tenant branding
- **Deliverables:**
  - [x] `packages/seo_health_report/branding/service.py`
  - [x] `apps/api/routers/branding.py`
  - [x] GET /tenant/branding - get current branding
  - [x] PATCH /tenant/branding - update branding
  - [x] DELETE /tenant/branding - reset to defaults
- **Acceptance Criteria:**
  - [x] Color validation (hex format #RRGGBB)
  - [x] Returns current branding config with is_custom flag
  - [x] Fallback to DEFAULT_BRANDING when no custom branding
- **Dependencies:** 5.3.1
- **Notes:** 25 tests added (test_branding_service.py, test_branding_api.py), 696 total tests passing

### Task 5.3.3: Report Branding Integration
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (3h)
- **Description:** Apply tenant branding to generated reports
- **Deliverables:**
  - [x] `packages/seo_health_report/branding/report_integration.py` - Integration module
  - [x] Updated `generate_html_report.py` with branding parameter
  - [x] `get_pdf_branding_colors()` for PDF generation
  - [x] `apply_html_branding()` for existing HTML transformation
  - [x] Fallback to DEFAULT_BRANDING when no tenant branding
- **Acceptance Criteria:**
  - [x] Logo appears in report header (logo_url support)
  - [x] Report uses tenant primary/secondary colors
  - [x] Footer text uses tenant branding
  - [x] CSS variables generated for web reports
- **Dependencies:** 5.3.2
- **Notes:** 19 tests added (test_report_branding.py), 715 total tests passing

---

## Phase 4: API Documentation — Day 6

### Task 5.4.1: OpenAPI Schema Enhancement
- **Agent:** doc-smith
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Improve OpenAPI documentation
- **Deliverables:**
  - [x] `apps/api/openapi.py` - Custom OpenAPI schema with comprehensive docs
  - [x] Add descriptions to all endpoints
  - [x] Add request/response examples (AUDIT_REQUEST_EXAMPLE, TOKEN_RESPONSE_EXAMPLE, etc.)
  - [x] Document error responses (400, 401, 404, 422, 429, 500)
  - [x] Add security scheme documentation (BearerAuth JWT)
- **Acceptance Criteria:**
  - [x] `/docs` shows complete API documentation
  - [x] Every endpoint has description
  - [x] Example requests work in Swagger UI
- **Dependencies:** None
- **Notes:** 22 tests added (test_openapi.py)

### Task 5.4.2: Python SDK Skeleton
- **Agent:** code-surgeon
- **Status:** COMPLETE ✅
- **Effort:** M (3h)
- **Description:** Create Python SDK for API access
- **Deliverables:**
  - [x] `packages/seo_health_sdk/` - Full SDK package
  - [x] `packages/seo_health_sdk/client.py` - SEOHealthClient & AsyncSEOHealthClient
  - [x] `packages/seo_health_sdk/auth.py` - TokenAuth & RefreshableTokenAuth with auto-refresh
  - [x] `packages/seo_health_sdk/models.py` - Pydantic models (AuditRequest, AuditResponse, Webhook, Branding, etc.)
  - [x] `packages/seo_health_sdk/exceptions.py` - Custom exceptions with raise_for_status helper
  - [x] Methods for audit CRUD, webhooks, and branding
  - [x] Async support with httpx
- **Acceptance Criteria:**
  - [x] SDK imports cleanly from packages.seo_health_sdk
  - [x] Can create and retrieve audits
  - [x] Handles authentication automatically
- **Dependencies:** 5.4.1
- **Notes:** 28 tests added (test_sdk.py), 765 total tests passing

---

## Phase 5: Integration & Polish — Day 7

### Task 5.5.1: Admin Health Dashboard
- **Agent:** frontend-designer
- **Status:** COMPLETE ✅
- **Effort:** M (2-3h)
- **Description:** Simple admin dashboard for system health
- **Deliverables:**
  - [x] `/admin/health` page
  - [x] Display: active audits, error rate, avg completion time
  - [x] Auto-refresh every 30s
  - [x] Admin role required
- **Acceptance Criteria:**
  - [x] Dashboard loads key metrics
  - [x] Protected by admin role
  - [x] Responsive design
- **Dependencies:** 5.1.2
- **Notes:** 8 tests added (test_admin_health.py), admin router mounted at /admin

### Task 5.5.2: Integration Tests
- **Agent:** test-architect
- **Status:** COMPLETE ✅
- **Effort:** M (3h)
- **Description:** End-to-end tests for Sprint 5 features
- **Deliverables:**
  - [x] `tests/integration/test_logging_integration.py`
  - [x] `tests/integration/test_metrics_integration.py`
  - [x] `tests/integration/test_branding_integration.py`
- **Acceptance Criteria:**
  - [x] Logging output validated
  - [x] Metrics endpoint returns valid format
  - [x] Branding persists and applies to reports
- **Dependencies:** 5.1.3, 5.2.5, 5.3.3
- **Notes:** 60 tests added across 3 files, 833 total tests passing

### Task 5.5.3: Documentation Update
- **Agent:** doc-smith
- **Status:** COMPLETE ✅
- **Effort:** S (1-2h)
- **Description:** Update README and docs with Sprint 5 features
- **Deliverables:**
  - [x] Update README with webhook setup
  - [x] Document branding configuration
  - [x] Add metrics/observability section
- **Acceptance Criteria:**
  - [x] README covers all new features
  - [x] Clear setup instructions
- **Dependencies:** All previous tasks
- **Notes:** Added Webhooks, Tenant Branding, Observability, and Python SDK sections to README

---

## Summary

| Phase | Tasks | Effort | Focus |
|-------|-------|--------|-------|
| Logging & Metrics | 5.1.1, 5.1.2, 5.1.3 | M+M+S | Observability |
| Webhooks | 5.2.1-5.2.5 | S+M+M+M+M | Integration |
| Branding | 5.3.1-5.3.3 | S+M+M | Customization |
| API Docs | 5.4.1, 5.4.2 | M+M | Developer Experience |
| Polish | 5.5.1-5.5.3 | M+M+S | Integration |

**Total Tasks:** 16
**Estimated Duration:** 5-7 days

## Critical Path

```
5.1.1 Structured Logger
    ↓
5.1.2 Metrics Collection ──→ 5.1.3 Audit Metrics
    ↓
5.2.1 Webhook Schema ──→ 5.2.2 Service ──→ 5.2.3 API ──→ 5.2.4 Integration ──→ 5.2.5 Tests
    ↓
5.3.1 Branding Schema ──→ 5.3.2 API ──→ 5.3.3 Report Integration
    ↓
5.4.1 OpenAPI ──→ 5.4.2 SDK
    ↓
5.5.1 Admin Dashboard ──→ 5.5.2 Integration Tests ──→ 5.5.3 Docs
    ↓
EXIT CRITERIA MET
```

## Exit Criteria Checklist
- [x] Structured JSON logging enabled
- [x] `/metrics` endpoint returns Prometheus format
- [x] Webhooks fire on audit completion
- [x] Tenant branding applies to reports
- [x] OpenAPI docs complete at `/docs`
- [x] Python SDK created (packages/seo_health_sdk/)
- [x] Test count >520 (currently 833)
- [x] All CI checks pass

## Quick Start

To begin Sprint 5, start with Task 5.1.1 (Structured Logger):

```bash
# Create logging package
mkdir -p packages/seo_health_report/logging
touch packages/seo_health_report/logging/__init__.py

# Run tests after implementation
pytest tests/ -v --ignore=tests/unit/test_async_operations.py --ignore=tests/test_cache.py
```
