# SEO Health Report System Audit

Audit completed: 2026-03-12
Host: Docker VM (`dvm@100.97.87.28`)
Repo: `/home/dvm/SEO-Health-Report-System`

## Executive Summary

This repo is a mixed Python + frontend monorepo for generating SEO audits, exposing an API, and processing background jobs. The backend is materially closer to runnable than the frontend/distribution story.

Current state after verification:
- API starts successfully in Docker and responds healthy on `GET /health`
- Worker starts successfully in Docker and enters its polling loop
- The SQLite `audit_jobs` schema already contains the worker lease/retry columns (`locked_until`, `locked_by`, `attempt`)
- A frontend exists in `apps/web` (React + Vite), but it was not buildable on-host during this audit because Node.js/npm are not installed on the VM
- There is configuration drift and environment inconsistency that should be cleaned up before calling this production-ready

## Architecture Overview

### Backend
- API: FastAPI app in `apps/api`
- Worker: async Python worker in `apps/worker`
- Dashboards: server-rendered admin/dashboard apps in `apps/admin` and `apps/dashboard`
- Packaging/runtime: Python project defined in `pyproject.toml`

### Python packages
- `packages/seo_health_report` - report generation/orchestration logic
- `packages/seo_technical_audit` - technical SEO auditing
- `packages/seo_content_authority` - content authority analysis
- `packages/ai_visibility_audit` - AI visibility/AEO-related auditing
- `packages/seo_health_sdk` - SDK/client models
- `packages/config`, `packages/core`, `packages/storage`, `packages/schemas` - shared foundations

### Frontend
- `apps/web` - React 18 + Vite frontend
- `apps/shared-styles` - Tailwind shared styles package

### Infrastructure
- Dockerfiles present for API and worker in `infrastructure/docker/`
- `docker-compose.yml` currently brings up `api`, `worker`, and `db` (Postgres)

## Database Schema Fix

The reported worker crash was tied to missing `audit_jobs` columns needed for leasing/retries.

Expected columns:
- `locked_until`
- `locked_by`
- `attempt`

### What I verified
I inspected `seo_health.db` directly with Python's sqlite bindings (the `sqlite3` CLI is not installed on-host). The table already contains all required columns:
- `attempt`
- `locked_until`
- `locked_by`
- plus related fields like `max_attempts`, `finished_at`, `last_error`

So at the time of this audit, no additional ALTER TABLE was required. The database already reflects the non-destructive fix.

## What Works

### 1) API boots successfully
Validated with Docker:
- `docker compose up -d --build api`
- `GET /health` returned `{"status":"healthy","database":"connected"}`

### 2) Worker boots successfully
Validated with Docker:
- `docker compose up -d --build worker`
- Worker log reaches steady polling state:
  - `Starting worker ...`
  - `Worker loop started ...`

This confirms the prior lease/retry schema problem is no longer blocking worker startup.

### 3) Repo structure is coherent enough to run core backend services
The repo has a clear split between API, worker, dashboard/admin surfaces, and reusable packages.

## What Is Broken / Risky

### 1) Host environment is incomplete for direct local runs
On the VM:
- `sqlite3` CLI is missing
- `node` / `npm` are missing
- the local `.audit-venv` did not have core Python deps installed (`sqlalchemy`, `fastapi`, `uvicorn` missing)

Impact:
- backend can run in Docker, but not from the host Python environment without setup
- frontend cannot be built on this VM as-is

### 2) Database strategy is inconsistent
`docker-compose.yml` starts a Postgres container, but both API and worker are configured with `DATABASE_URL=sqlite:///./seo_health.db`.

Impact:
- the Postgres service is effectively unused in the current compose setup
- migration/runtime expectations are ambiguous
- production readiness is blocked until one database strategy is chosen and enforced

### 3) Frontend presence is real, but build status is unverified on this machine
There is a real frontend app in `apps/web`:
- React 18
- Vite 5
- Tailwind/PostCSS
- Radix UI, Recharts, Framer Motion

But the VM has no Node.js/npm installed, so I could not complete an on-host build smoke test.

### 4) Local repo is not clean
There were pre-existing local modifications not created by this audit:
- `apps/worker/main.py` modified
- `docker-compose.yml` modified
- `pyproject.toml` modified
- `.audit-venv/` untracked
- `docker-compose.yml.bak.topg` untracked

Impact:
- operational state is ahead of or divergent from Git
- future debugging/deploys may be confusing

### 5) Optional/reporting dependencies may still be incomplete
Worker logs note `weasyprint not available - PDF generation disabled`.

Impact:
- core processing may run, but some report export capability is likely degraded or disabled

## Quick Wins Remaining

1. Pick one database for runtime.
2. Add real migrations for queue/lease columns.
3. Make the host runnable or declare it Docker-only.
4. Prove the frontend in CI with `npm ci && npm run build`.
5. Clean the repo state on the VM.
6. Restore or intentionally disable PDF/report features.

## Roadmap to Production-Ready

### Phase 1 - Stabilize runtime
- Standardize on SQLite-for-dev or Postgres-for-prod, but stop mixing both in default runtime config
- Add/check migrations for all queue-related columns
- Ensure API + worker health checks are part of deployment validation

### Phase 2 - Prove end-to-end flow
- Submit a real audit job through the API
- Confirm worker claims job, processes it, and writes results/reports
- Verify admin/dashboard surfaces can view generated output

### Phase 3 - Frontend hardening
- Install Node in build environment or move frontend builds to CI artifacts
- Build `apps/web` successfully and document how it is deployed/served
- Clarify whether `apps/web` replaces, complements, or is separate from the server-rendered dashboard/admin apps

### Phase 4 - Operational readiness
- Clean secrets/config strategy
- Add smoke tests for API, worker, DB, and report generation
- Add one-command environment bootstrap for developers/operators
- Remove drift between local VM state and Git

## Practical Verdict

This is not a dead repo. The backend stack is active enough to boot in containers, and the worker lease/retry issue appears resolved at the database level.

However, it is not production-ready yet because:
- DB/runtime strategy is inconsistent
- frontend build is not proven on this host
- local environment/bootstrap is incomplete
- some report-generation capability appears optional/broken (`weasyprint`)
- the VM repo has drift from Git

If I had to summarize it in one line:

> The backend is salvageable and runnable now, but the project still needs environment cleanup, DB normalization, and end-to-end verification before it should be treated as a production system.