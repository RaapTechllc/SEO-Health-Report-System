# Brownfield Cleanup Completion Report

**Date:** 2026-03-19
**Agent:** Damien (Claude Opus 4.6)

## Phase 1: Critical Security Fixes

| Item | Status | Details |
|------|--------|---------|
| 1.1 Auth on audit/competitor endpoints | DONE | `require_auth` added to `start_audit`, `list_audits`, `add_competitor`, `list_competitors`, `delete_competitor`. Results filtered by `user_id`. |
| 1.2 bcrypt password hashing | DONE | `passlib.hash.bcrypt` replaces SHA-256. Legacy SHA-256 verified + rehashed on login via `needs_rehash()`. |
| 1.3 Docker compose secrets | DONE | Replaced hardcoded `JWT_SECRET_KEY` and `POSTGRES_PASSWORD` with `${VAR:?must be set}` fail-fast syntax. |
| 1.4 Deduplicate .env.example | DONE | Removed duplicate `JWT_SECRET_KEY`, `STRIPE_SECRET_KEY`, `DATABASE_URL`, `BASE_URL` sections (lines 206-247). |
| 1.5 Migration v007 collision | DONE | `v007_tenant_quotas.py` renamed to `v008_tenant_quotas.py`, `down_revision` updated to `007_audit_trade_fields`. |
| 1.6 CORS restriction | DONE | `allow_methods` and `allow_headers` changed from `["*"]` to explicit lists in `apps/api/main.py`. |

## Phase 2: Architecture Consolidation

| Item | Status | Details |
|------|--------|---------|
| 2.1 Consolidate safe_fetch | DONE | `packages/core/safe_fetch.py` is now the single httpx-based implementation. `scripts/safe_fetch.py` re-exports from core. |
| 2.2 Move root modules to packages/ | DONE | `auth.py`, `database.py`, `payments.py`, `rate_limiter.py` canonical code in `packages/`. Root files are re-export shims. |
| 2.3 Merge competitive_monitor DB | SKIPPED | Module archived in Phase 4. Separate SQLite DB is moot once archived. |
| 2.4 Consolidate Docker Compose | DONE | Deleted `docker-compose.yml.bak.topg` and `infrastructure/docker-compose.prod.yml`. 4 -> 2 files. |
| 2.5 Consolidate CI workflows | DONE | Deleted `ci.yml` (subsumed by `ci-cd.yml`) and `docker.yml` (subsumed by `docker-build.yml`). |
| 2.6 Wire up job queue | NOT DONE | `enqueue_audit_job()` exists but commented out. Wiring requires runtime testing with worker. Documented for follow-up. |
| 2.7 Dashboard sessions to Redis | NOT DONE | Requires Redis client dependency and runtime integration. Documented for follow-up. |
| 2.8 Fix datetime consistency | DONE | Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)` across 12+ source files. |

## Phase 3: Code Quality & Performance

| Item | Status | Details |
|------|--------|---------|
| 3.1 Standardize HTTP client | PARTIAL | `safe_fetch` consolidated on httpx. Full migration of `requests`/`aiohttp` deferred per spec ("don't migrate entire codebase in one pass"). |
| 3.2 Redis-backed rate limiting | NOT DONE | Requires Redis runtime dependency. In-memory rate limiter remains. |
| 3.3 Pagination on list endpoints | DONE | `/audits` now accepts `skip`/`limit` params (default 20, max 100). |
| 3.4 Fix DB strategy | PARTIAL | Docker compose now defaults to PostgreSQL. Runtime default remains SQLite for local dev. |
| 3.5 .gitignore entries | DONE | Added `*.sqlite`, `.audit-venv/`. |

## Phase 4: Cleanup & Dead Code Removal

| Item | Status | Details |
|------|--------|---------|
| Delete dead files | DONE | Removed: `raaptech-branding-skill/`, `infrastructure/api/mobile-routes.js`, `infrastructure/services/realtime-service.js`, `archive/deprecated/`, `sheetmetal_audit_*.json`, `apps/web/App.jsx`, `apps/web/components/` |
| Archive social-media-audit | DONE | Moved to `archive/social-media-audit/` |
| Remove react-redux | DONE | Removed from `apps/web/package.json` (no Redux store exists) |
| Move planning docs | DONE | 10 markdown files moved to `docs/planning/`. `sprint plan.md` renamed to `sprint-plan.md`. |
| Remove .audit-venv from tracking | DONE | `git rm -r --cached .audit-venv` |

## Phase 5: Testing

| Item | Status | Details |
|------|--------|---------|
| Tests written | DONE | 32 tests in `tests/unit/test_brownfield_fixes.py` |
| All tests passing | DONE | `pytest tests/unit/test_brownfield_fixes.py` = 32 passed |

### Test Coverage

1. Auth endpoint enforcement (5 tests) - P0
2. Bcrypt password hashing (4 tests) - P0
3. SSRF protection / safe_fetch (12 tests) - P0
4. Rate limiter behavior (2 tests) - P1
5. Migration chain integrity (2 tests) - P1
6. Audit CRUD with tenant filtering + pagination (2 tests) - P1
7. Datetime consistency (2 tests) - P2
8. Docker compose security (2 tests) - P0
9. CORS restriction (1 test) - P0

## Known Blockers (deferred)

| Item | Reason |
|------|--------|
| 2.6 Job queue wiring | Requires runtime worker process testing |
| 2.7 Redis sessions | Requires Redis client dependency |
| 3.2 Redis rate limiting | Requires Redis client dependency |
| `pip-audit` / `npm audit` | Not run (no pip/npm available in this environment) |

## Git History

```
51e33d7 brownfield: phase 1 - critical security fixes
9cc33c4 brownfield: phase 2 - architecture consolidation
78da050 brownfield: phase 3 - code quality improvements
095b4cb brownfield: phase 4 - cleanup and dead code removal
00dabc3 brownfield: phase 5 - testing (32 tests passing)
```
