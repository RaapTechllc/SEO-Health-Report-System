# 🎯 SEO Health Report System — FINISH PLAN

**Created:** January 19, 2026  
**Status:** Active Development Sprint  
**Goal:** Production-Ready MVP with Unified Premium Report Engine

---

## 📊 Current State Assessment

### ✅ Completed (Ready to Ship)

| Component | Status | Notes |
|-----------|--------|-------|
| **Tiered Cost System** | ✅ Complete | LOW/MED/HIGH configs at $0.02/$0.05/$0.16 |
| **Grok Sentiment Analysis** | ✅ Verified | `grok-4-1-fast-reasoning` integration live |
| **Logo Fallback Pipeline** | ✅ Complete | 5-tier fallback (Logo.dev → Brandfetch → Scrape → Google S2 → AI) |
| **Premium PDF Generator** | ✅ Complete | Full-featured `generate_premium_report.py` (96KB) |
| **Tier Comparison Tool** | ✅ Complete | `generate_tier_comparison.py` for side-by-side reports |
| **Frontend Tier Selection** | ✅ Complete | Budget/Balanced/Premium UI in AuditForm.jsx |
| **Executive Summary AI** | ✅ Refined | Human-readable percentiles, strategic copy |
| **API Tier Parameter** | ✅ Complete | Accepts low/medium/high + legacy aliases (basic/pro/enterprise) |
| **Worker Tier Loading** | ✅ Complete | `tier_config.py` loads tier-specific model configs |
| **Human Copy Module** | ✅ Complete | `human_copy.py` cleans AI text, bans robotic phrases |
| **Legacy File Cleanup** | ✅ Complete | Duplicates deleted, legacy files archived |

### 🔄 In Progress / Remaining

| Component | Status | Blocker |
|-----------|--------|---------|
| **Logo.dev API Key** | ⚠️ Optional | Better logos if `LOGODEV_PUBLIC_KEY` is added |
| **E2E Tests** | 🟡 Partial | Verified Tier Config Loading & Switching logic |
| **Cost Tracking Verification** | 🔄 Planned | Verify `cost_events` table usage |

### ❌ Legacy (Archived/Deleted)

| Component | Action | Status |
|-----------|--------|--------|
| `generate_free_report.py` | Archived to `archive/deprecated/` | ✅ Done |
| `generate_html_report.py` | Archived to `archive/deprecated/` | ✅ Done |
| `generate_html_report 2.py` | Deleted | ✅ Done |
| `generate_premium_report 2.py` | Deleted | ✅ Done |
| `run_premium_audit 2.py` | Deleted | ✅ Done |
| `start_app 2.sh` | Deleted | ✅ Done |

---

## 🚀 Phase 1: Core Wire-Up ✅ COMPLETE

### Task 1.1: API Tier Parameter Integration ✅
**Priority:** 🔴 P0 | **Status:** ✅ Complete

```
1. [x] Update `apps/api/main.py` to accept `tier` parameter (low/medium/high)
2. [x] Added TIER_MAPPING for backwards compatibility (basic→low, pro→medium, enterprise→high)
3. [x] Pass tier configuration to worker via job payload
4. [x] Add tier validation (reject invalid tier values)
```

### Task 1.2: Worker Tier Config Loading ✅
**Priority:** 🔴 P0 | **Status:** ✅ Complete

```
1. [x] Created `packages/seo_health_report/tier_config.py` to load tier env vars
2. [x] Worker calls `load_tier_config(tier)` at start of each audit
3. [x] Environment variables set for correct models per tier
4. [x] Test: Run LOW tier audit → verify cheap models used (Verified in Integration Test)
5. [x] Test: Run HIGH tier audit → verify premium models used (Verified in Integration Test)
```

### Task 1.3: Default to LOW Tier (Deprecate Legacy) ✅
**Priority:** 🔴 P0 | **Status:** ✅ Complete

```
1. [x] Changed default behavior: No tier specified = LOW tier
2. [x] Changed job type from "hello_audit" to "full_audit"
3. [x] Stripe webhook uses TIER_MAPPING for paid tiers
4. [x] All audit paths now route through unified engine
```

### Task 1.4: Clean Up Duplicate Files ✅
**Priority:** 🟡 P1 | **Status:** ✅ Complete

```
1. [x] Archive: Moved `generate_free_report.py`, `generate_html_report.py` to `archive/deprecated/`
2. [x] Delete: Removed `*2.py` and `*2.sh` duplicates
3. [x] No broken imports (files were standalone)
```

### Task 1.5: Human Copy Guidelines (Added) ✅
**Priority:** 🟡 P1 | **Status:** ✅ Complete

```
1. [x] Created `packages/seo_health_report/human_copy.py`
2. [x] Added `clean_ai_copy()` function to remove robotic phrases
3. [x] Added `score_copy_humanness()` for quality checking
4. [x] Integrated into executive summary generation
5. [x] Banned phrases list: "delving into", "paradigm", "synergy", etc.
```

## 🛡️ Phase 2: Hardening & Quality (Current)

**Objective:** Verify system reliability, error handling, and logical correctness.

### Task 2.1: Tier Switching & Config Verification ✅
**Priority:** 🔴 P0 | **Status:** ✅ Complete

```
1. [x] Identify Import-Time Constant Bug: AI modules were caching env vars at import.
2. [x] Fix: Updated `query_ai_systems.py` to read `os.environ` dynamically.
3. [x] Test: Created `tests/integration/test_tier_configuration.py`.
4. [x] Verify: Passed test confirming LOW vs HIGH tier switches models correctly.
```

### Task 2.2: Error Handling & Graceful Degradation ✅
**Priority:** 🔴 P0 | **Status:** ✅ Complete

```
1. [x] Test missing API keys handling (Grok, Claude verified)
2. [x] Verify "Partial Success" state for audits (Social Audit logic verified)
3. [x] Ensure PDF generated even if 1 sub-audit fails (PDF Generator has robust .get() checks)
```

### Task 2.3: Cost Tracking Verification ❌
**Priority:** 🟡 P1 | **Status:** ❌ Missing

```
1. [ ] Check `cost_events` table usage (Confirmed MISSING in worker & schemas)
2. [ ] Implement cost tracking if required (Needs User Input)
```

---

## 🔧 Phase 2: Hardening & Quality (Next Week)

**Objective:** Production-grade reliability and testing.

### Task 2.1: Error Handling & Graceful Degradation
**Priority:** 🔴 P0 | **Effort:** 1 day

```
1. [ ] Verify all API endpoints return clean error messages (no stack traces)
2. [ ] Add fallback for each external service (PageSpeed, Grok, Logo APIs)
3. [ ] Test report generation when individual services fail
4. [ ] Ensure partial results are returned (not job failure)
```

### Task 2.2: E2E Test for Tiered Reports
**Priority:** 🔴 P0 | **Effort:** 1 day

```
1. [ ] Create test: Submit LOW tier audit → verify PDF generated
2. [ ] Create test: Submit MEDIUM tier audit → verify PDF generated  
3. [ ] Create test: Submit HIGH tier audit → verify PDF generated
4. [ ] Add to CI pipeline
5. [ ] Fixture site: Use a known-good test URL
```

### Task 2.3: Cost Tracking Verification
**Priority:** 🟡 P1 | **Effort:** 0.5 day

```
1. [ ] Verify `cost_events` table is populated per audit
2. [ ] Calculate actual cost vs. estimated cost per tier
3. [ ] Add cost summary to admin dashboard (if exists)
```

### Task 2.4: Security Audit
**Priority:** 🟡 P1 | **Effort:** 0.5 day

```
1. [ ] Verify SSRF protections still work (private IPs blocked)
2. [ ] Verify log redaction (no API keys in logs)
3. [ ] Verify rate limiting is enforced
4. [ ] Verify tenant isolation (cross-tenant access denied)
```

---

## 📦 Phase 3: Deployment (Week 3)

**Objective:** Ship to staging, validate, then production.

### Task 3.1: Staging Deployment
**Priority:** 🔴 P0 | **Effort:** 1 day

```
1. [ ] Deploy API + Worker to staging environment
2. [ ] Run database migrations
3. [ ] Configure staging env vars (tier configs, API keys)
4. [ ] Run golden path E2E test
```

### Task 3.2: Production Deployment
**Priority:** 🔴 P0 | **Effort:** 1 day

```
1. [ ] Production env var configuration
2. [ ] Manual approval gate for prod deploy
3. [ ] Deploy with zero-downtime strategy
4. [ ] Post-deploy smoke test
5. [ ] Rollback plan documented and tested
```

### Task 3.3: Monitoring Setup
**Priority:** 🟡 P1 | **Effort:** 0.5 day

```
1. [ ] Set up error alerting (failed jobs, 5xx errors)
2. [ ] Set up cost alerting (daily spend thresholds)
3. [ ] Dashboard for job queue depth and latency
```

---

## 🎁 Phase 4: Value Adds (Post-MVP)

**Objective:** Features that enhance value but aren't blocking launch.

### Task 4.1: Logo.dev Integration (Optional)
**Priority:** 🟢 P2 | **Effort:** 1 hour

```
1. [ ] Sign up for Logo.dev free tier
2. [ ] Add LOGODEV_PUBLIC_KEY to .env
3. [ ] Test logo quality improvement
```

### Task 4.2: Content Coverage Audit (Milestone 7)
**Priority:** 🟡 P1 | **Effort:** 1 week

```
See PLAN.md Issue 7.1-7.4:
- [ ] Service taxonomy builder
- [ ] City/service area coverage mapping
- [ ] Cannibalization detection
- [ ] Internal linking plan generator
```

### Task 4.3: Diamond Ops Features (Milestone 17)
**Priority:** 🟡 P1 | **Effort:** 2 weeks

```
See PLAN.md Issue 17.1-17.3:
- [ ] Implementation backlog generator
- [ ] "What changed since last audit" diff
- [ ] Monthly Diamond report
```

### Task 4.4: Integrations (Milestone 18)
**Priority:** 🟢 P2 | **Effort:** 3 weeks

```
See PLAN.md Issue 18.1-18.3:
- [ ] GA4 connector
- [ ] Google Search Console connector
- [ ] GBP connector
```

---

## 📋 Quick Reference: File Locations

### Critical Files to Modify

| File | Purpose |
|------|---------|
| `apps/api/main.py` | API endpoint - add tier parameter |
| `apps/worker/handlers/full_audit.py` | Worker - load tier config |
| `generate_premium_report.py` | Report engine - already complete |
| `config/tier_low.env` | LOW tier model config |
| `config/tier_medium.env` | MEDIUM tier model config |
| `config/tier_high.env` | HIGH tier model config |

### Files to Archive/Delete

| File | Action |
|------|--------|
| `generate_free_report.py` | Archive |
| `generate_html_report.py` | Archive |
| `generate_html_report 2.py` | Delete |
| `generate_premium_report 2.py` | Delete |
| `run_premium_audit 2.py` | Delete |
| `start_app 2.sh` | Delete |

---

## ⏱️ Timeline Summary

| Phase | Duration | Target Date |
|-------|----------|-------------|
| Phase 1: Core Wire-Up | 3 days | Jan 22, 2026 |
| Phase 2: Hardening | 4 days | Jan 28, 2026 |
| Phase 3: Deployment | 2 days | Jan 30, 2026 |
| **MVP LAUNCH** | - | **Jan 30, 2026** |
| Phase 4: Value Adds | Ongoing | Feb+ |

---

## 🏁 MVP Launch Checklist

Before flipping the switch to production:

- [ ] All Phase 1 tasks complete
- [ ] All Phase 2 P0 tasks complete
- [ ] Staging E2E tests passing
- [ ] Cost tracking verified
- [ ] Error handling verified (no job deadlocks)
- [ ] Rollback plan tested
- [ ] API keys separated (staging vs prod)
- [ ] Rate limiting enforced
- [ ] 3 successful full audits in staging

---

## 📞 Notes for Development

1. **Single Engine Philosophy**: All reports (Free/Budget/Premium) now use the same PDF engine with different model configs. No more maintaining separate codepaths.

2. **Graceful Degradation**: Every external service should have a fallback. If Grok fails, skip sentiment. If Logo APIs fail, use Google S2. If AI fails, use template text.

3. **Cost Awareness**: The LOW tier at $0.02/report is cheap enough to be the "free" tier. No reason to maintain a separate zero-cost HTML experience.

4. **Test with Real Sites**: Use fixture sites that exercise all report features. Avoid mock data for final validation.

---

*Last Updated: 2026-01-19T15:30:00-06:00*
