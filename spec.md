# SEO Health Report System — Implementation Spec

## Architecture Overview

The system is a Python monorepo that orchestrates three independent audit pillars (Technical SEO 30%, Content/Authority 35%, AI Visibility 35%) into a weighted composite score, then renders branded PDF/HTML reports. A FastAPI API server accepts audit requests and enqueues them as jobs; a lease-based async worker claims jobs, executes the three-pillar pipeline, calculates scores, generates reports, and delivers webhooks. A Jinja2 dashboard provides a web UI over the same database. All pillars call external APIs (Google PageSpeed, OpenAI, Anthropic, Perplexity, Grok, Gemini) with tier-based model selection (LOW/MEDIUM/HIGH cost tiers). Pydantic models in `packages/schemas/` enforce data contracts across the boundary between API, worker, and audit packages.

## Milestone 1: Foundation Hardening

The MVP exists and ~90% works. This milestone closes the critical bugs, security gaps, and structural issues identified in the audit — making the existing code production-safe without adding new features.

### Deliverables

1. **`packages/ai_visibility_audit/scripts/aeo_engine.py`** — Fix division-by-zero on line 358, fix undefined variable reference on line 415, remove dead code on line 317.
2. **`packages/ai_visibility_audit/__init__.py`** — Remove dead code (line 52), add component failure isolation (try/except per pillar component so one failure doesn't crash the whole audit).
3. **`packages/ai_visibility_audit/scripts/analyze_responses.py`** — Remove dead code (line 52).
4. **`competitive_intel/analyzer.py`** — Replace unsafe `sys.path` manipulation with proper absolute imports; add URL input validation; narrow exception handling from bare `except Exception` to specific types.
5. **`competitive_monitor/alerts.py`** — Move hardcoded SMTP from/recipient to environment variables; sanitize email body content.
6. **`generate_tier_comparison.py`** — Fix dead code on line 74 where computed output path is discarded (bug: tier comparison output naming is broken).
7. **`generate_one_pager.py`** — Remove hardcoded "Sheet Metal Werks" logo path; parameterize it. Add `plt.close()` after figure generation to prevent resource leaks.
8. **`packages/seo_health_report/__init__.py`** — Add URL/company name validation at orchestrator entry point; replace bare `except` on cache operations with specific exceptions.
9. **`packages/ai_visibility_audit/test_aeo_engine.py`**, **`basic_test.py`**, **`direct_test.py`** — Fix relative imports to absolute imports so they run under pytest from project root.
10. **Root cleanup** — Delete `debug_import.py` (dead utility).

### Acceptance Criteria

- [ ] `pytest tests/` passes with zero new failures
- [ ] `ruff check .` passes with zero errors
- [ ] `aeo_engine.py` handles empty `system_responses` list without crash
- [ ] `competitive_intel/analyzer.py` has no `sys.path` manipulation
- [ ] `competitive_monitor/alerts.py` reads SMTP config from env vars
- [ ] `generate_tier_comparison.py` produces correctly-named tier output files
- [ ] `generate_one_pager.py` accepts logo path as parameter (no hardcoded client)
- [ ] All test files in `packages/ai_visibility_audit/` are runnable via `pytest` from project root
- [ ] No bare `except Exception` remains in `seo_health_report/__init__.py`

### Risks & Dependencies

- Fixing imports in `competitive_intel/analyzer.py` may require adjusting `pyproject.toml` package mappings if `competitive_intel` isn't currently installable.
- Some test files in `packages/ai_visibility_audit/` may need to move to `tests/` if they cannot be made importable from their current location.
- The deprecated `packages/seo_health_report/config.py` is still referenced by other modules — full removal deferred to Milestone 2 to avoid cascading breakage.

## Milestone 2: Core Resilience

With the critical bugs fixed, this milestone adds the defensive layers needed for production reliability: circuit breakers, input validation, configuration externalization, and distributed session support.

### Deliverables

1. **Input validation module** (`packages/core/validators.py`) — URL schema validation, company name sanitization, keyword normalization. Used by orchestrator, API, and CLI entry points.
2. **Circuit breaker for AI providers** (`packages/core/circuit_breaker.py`) — Per-provider circuit breaker (closed/open/half-open states) so a failing provider (e.g., Perplexity down) doesn't block the entire audit. Fallback to degraded scoring when a provider is unavailable.
3. **Configuration externalization** — Extract all hardcoded scoring weights, page limits, query counts, and sentiment keywords into `packages/config/audit_defaults.py` loaded from tier env files.
4. **Distributed session store** (`apps/dashboard/session_store.py`) — Abstract session interface with in-memory (dev) and database-backed (prod) implementations. Replace current in-memory dict in `apps/dashboard/auth.py`.
5. **Deprecated config migration** — Remove `packages/seo_health_report/config.py`; update all imports to use `packages/config/settings.py`.
6. **Structured logging** — Replace print statements and basic logging with structured JSON logging using Python's `logging` module across all packages.

### Acceptance Criteria

- [ ] Invalid URLs (missing scheme, private IPs, non-HTTP schemes) rejected at API and CLI layers with clear error messages
- [ ] Circuit breaker trips after 3 consecutive failures; recovers after 60s half-open probe
- [ ] Audit completes with degraded score when 1 of 5 AI providers is unavailable
- [ ] Scoring weights, page limits, query counts configurable via tier env files without code changes
- [ ] Dashboard sessions survive API server restart when using database backend
- [ ] No remaining imports from `packages/seo_health_report/config.py`
- [ ] All log output is structured JSON in production mode

### Risks & Dependencies

- Circuit breaker adds complexity to audit scoring — need clear degraded-mode scoring rules (e.g., redistribute weight among available providers).
- Session store migration requires database migration (v008) for sessions table.
- Structured logging migration is high-touch (many files) — risk of missed spots.

## Milestone 3: Hardening & Production Readiness

Final polish for production deployment: comprehensive testing, security audit, performance validation, documentation, and deployment verification.

### Deliverables

1. **Security audit fixes** — Address the 12 critical + 8 high vulnerabilities identified in `docs/PROGRESS.md` security review. Specifically: SQL injection in competitive modules, missing auth on competitive_intel API, input sanitization gaps.
2. **Composite health endpoint** (`/health/deep`) — Checks DB connectivity, storage backend, and probes each AI provider with a lightweight ping. Returns degraded/healthy/unhealthy status.
3. **Performance benchmarks** — Baseline timing for LOW/MEDIUM/HIGH tier audits. Add `@pytest.mark.performance` tests that validate audit completes within tier-specific time bounds.
4. **Test coverage improvement** — Target: 80% line coverage on `packages/` code. Add missing unit tests for scoring functions, report generation, and webhook delivery.
5. **Production deployment verification** — Docker Compose smoke test that boots API + Worker + PostgreSQL, runs a hello audit, and validates report output.
6. **Documentation refresh** — Update `README.md`, `docs/DEPLOYMENT_CHECKLIST.md`, and `docs/COMPLETE_SYSTEM_README.md` to reflect current architecture, all env vars, and deployment procedure.

### Acceptance Criteria

- [ ] Zero known SQL injection or path traversal vulnerabilities
- [ ] `/health/deep` returns structured JSON with per-dependency status
- [ ] LOW tier audit completes in <30s, MEDIUM <60s, HIGH <120s (mocked AI providers)
- [ ] `pytest --cov` reports >=80% line coverage on `packages/`
- [ ] `docker compose up && curl /health` returns 200 within 30s of container start
- [ ] README accurately describes current setup, commands, and architecture
- [ ] All CI workflows pass on a clean checkout

### Risks & Dependencies

- Performance targets depend on AI provider response times — benchmarks must use mocked providers for deterministic results.
- Coverage target may require refactoring untestable code paths (e.g., deeply nested try/except blocks).
- Docker smoke test requires PostgreSQL to be healthy before API starts — depends on proper health check ordering in compose.
