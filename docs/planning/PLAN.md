# SEO Health Report System — Project Plan & Backlog

## Sprint Plan

This section outlines the 2-week sprint schedule for the MVP and subsequent phases.

### Sprint 1 (Weeks 1–2) — Platform Skeleton + Multi-Tenant Core

**Goal:** The system can create tenants/projects and start an audit job record safely.

**Scope (from backlog)**
* 1.1 Monorepo structure + conventions
* 1.2 Env config + secrets strategy
* 1.3 Shared schemas package
* 2.1 DB schema v1 + migrations
* 2.2 Tenant + RBAC rules
* 2.3 Storage buckets + signed URLs (basic)
* 3.1 Audit lifecycle endpoints (stubbed statuses)

**Deliverables**
* DB migrations run from empty DB
* Auth works (tenant scoped)
* `POST /audits` creates an audit record + returns `audit_id`

**Exit criteria**
* [ ] Migrations + seed work in local + staging
* [ ] Tenant scoping enforced at API layer
* [ ] Audit record created and visible via `GET /audits/{id}`

### Sprint 2 (Weeks 3–4) — Job Framework + Worker Wiring + Safe Fetching

**Goal:** Audits run async with progress tracking; safe fetch client exists.

**Scope**
* 3.2 Worker runner + queue wiring
* 3.3 Progress model + event log
* 3.4 Idempotent audit hashing
* 4.1 HTTP fetch client with SSRF protections
* 14.2 Sensitive data redaction (start here, not later)

**Deliverables**
* Worker consumes audit jobs and updates progress
* Retries for transient failures (timeouts/429)
* SSRF protections block private IPs and unsafe schemes
* Cost event scaffolding ready (even if not fully used)

**Exit criteria**
* [ ] A “hello audit” job completes end-to-end without manual intervention
* [ ] Progress changes show in DB (queued → running → done)
* [ ] SSRF unit tests pass (private IPs blocked)

### Sprint 3 (Weeks 5–6) — Crawl Foundations (Robots + Sitemaps + Crawl Graph)

**Goal:** Deterministic crawl data exists (the truth source for everything else).

**Scope**
* 4.2 robots.txt parser + policy mode
* 4.3 Sitemap discovery + validation
* 4.4 Crawl engine v1 (links, depth, orphans)
* 13.1 Structured logging + correlation IDs (audit_id everywhere)

**Deliverables**
* Crawl outputs stored in `audit_results` (raw + normalized summaries)
* Robots respected by default
* Sitemap URLs validated (status codes, canonical patterns)

**Exit criteria**
* [ ] Crawl can complete on 3 fixture sites within tier page limits
* [ ] Link graph and click depth computed
* [ ] Robots/sitemap results visible in results endpoint

### Sprint 4 (Weeks 7–8) — Technical SEO Audit v1 + Trades Local/Conversion v1

**Goal:** MVP “first paid win” audits are real: Technical + Local/Conversion.

**Scope**
* 5.1 Status codes + redirect chain analysis
* 5.2 Canonical + indexation directives audit
* 5.4 Structured data extraction + rule-based validation
* 6.1 NAP + service area extraction
* 6.2 Conversion readiness checks
* 6.3 Trades trust blocks detector
* 10.1 scoring.yaml + scoring versioning (start)
* 10.2 Composite scorer (basic, with caps)

**Deliverables**
* Technical score + Local/Conversion score + overall score produced
* “Top fixes” prioritized with evidence URLs
* Grade caps work (e.g., indexing blocked caps grade)

**Exit criteria**
* [ ] Deterministic outputs (repeat run produces same findings if site unchanged)
* [ ] Each issue includes evidence (URL + snippet/metric reference)
* [ ] Overall score + grade + explanation generated

### Sprint 5 (Weeks 9–10) — AI Layer (Future-Proof) + Reporting v1 + Cost Tracking

**Goal:** AI is used safely and pragmatically; reports render reliably.

**Scope**
* 8.1 AI Gateway (provider-agnostic)
* 8.2 Structured outputs + schema validation + fallback
* 8.3 Site Facts pipeline (`site_facts.json`)
* 8.4 Trades prompt library + versioning
* 8.5 AI eval harness (CI regression)
* 5.5 PageSpeed/CWV integration + caching
* 11.1 Report template v1 (trades-friendly)
* 11.2 Report renderer in worker + artifact storage
* 13.2 Cost tracking (`cost_events`) for crawl/pagespeed/AI

**Deliverables**
* Report downloads work (PDF/DOCX per your choice; at least one must be rock solid)
* AI produces only structured, validated outputs
* Site Facts powers AI accuracy checks and summaries
* PageSpeed is cached and not a runaway cost

**Exit criteria**
* [ ] Report renders for 3 fixture sites without breaking fonts/assets
* [ ] AI eval harness runs in CI and blocks drift
* [ ] Cost per audit can be computed and shown (even if internal)

### Sprint 6 (Weeks 11–12) — Web Dashboard MVP + Security/Quotas + E2E “Works 150%”

**Goal:** A contractor can run an audit in the UI and download a report; system is hardened.

**Scope**
* 12.1 Auth + tenant switch UI
* 12.2 New audit intake flow
* 12.3 Audit status + progress UI
* 12.4 Results viewer + report download
* 14.1 Rate limiting + per-tenant quotas
* 15.1 Golden path E2E test
* 15.2 Fixture sites library + expected checks
* 15.4 verify_release.sh

**Deliverables**
* Full golden path: submit → progress → results → download
* Rate limits and tier caps enforced
* One command validates release readiness

**Exit criteria**
* [ ] Golden path E2E passes in CI against staging
* [ ] 20 sequential audits run without manual resets
* [ ] Failure modes return “partial results” cleanly (no stuck jobs)

---

# MVP Launch Gate (After Sprint 6)
Ship only when these are true:
* [ ] Staging mirrors production infra (keys separated)
* [ ] CI blocks merges on failing tests/evals
* [ ] Cost guardrails prevent surprise spend
* [ ] SSRF + quotas + redaction are verified in staging

---

### Sprint 7 (Weeks 13–14) — CI/CD + Staging→Prod + Chaos Hardening

**Goal:** Reliable deployments and recovery, not heroics.

**Scope**
* 16.1 Build/push containers (API + worker)
* 16.2 Staging deploy pipeline + migrations + smoke tests
* 16.3 Prod deploy pipeline + rollback plan
* 15.3 Chaos tests (timeouts, 429s, robots blocks)

**Exit criteria**
* [ ] One-click deploy to staging
* [ ] Prod deploy has manual approval + rollback steps
* [ ] Chaos tests prove “no deadlocks + partial results work”

### Post-MVP (P1) — Platinum + Diamond Value Sprints

#### Sprint 8 (Weeks 15–16) — Content + Coverage (Platinum Core)
**Goal:** Generate the “coverage map” that sells Platinum in trades.

#### Sprint 9 (Weeks 17–18) — AI Readiness + ASV v1
**Goal:** AI features that are stable: readiness + accuracy vs Site Facts.

#### Sprint 10 (Weeks 19–20) — Diamond Ops (Done-For-You Engine)
**Goal:** Productized delivery: backlog, diffs, monthly reporting.

#### Sprint 11+ (Optional) — Integrations for Proof and Retention (P2)
**Goal:** Tie work to leads and rankings (stickiness).

---

## Detailed GitHub Backlog (Epics → Stories → Acceptance Criteria)

This backlog follows the sprint plan above. Use **Milestones** for epics and **Issues** for stories.

### Global labels
#### Priority
- `P0` Must ship for MVP.
- `P1` Next after MVP.
- `P2` Later but planned.
- `P3` Optional / nice-to-have.

#### Area
- `area:api`
- `area:worker`
- `area:web`
- `area:db`
- `area:seo-tech`
- `area:seo-content`
- `area:local`
- `area:ai`
- `area:reporting`
- `area:security`
- `area:observability`
- `area:ci-cd`
- `area:ops`

### Type
- `type:feature`
- `type:chore`
- `type:bug`
- `type:spike`
- `type:docs`
- `type:test`

### Size
- `size:S` (≤ 1 day)
- `size:M` (2–4 days)
- `size:L` (1–2 weeks)

---

## Global Definition of Done (applies to every issue)
- [ ] Code merged to main with review.
- [ ] Unit tests added or updated.
- [ ] Logs are structured (JSON) and include `audit_id` when relevant.
- [ ] Errors are caught and return a clean message (no raw stack traces to users).
- [ ] Config is via env + config files, not hard-coded.
- [ ] Any schema changes include migrations.

---

# Milestone 1 — Foundation + Repo Standards (P0)

## Issue 1.1 — Create monorepo structure + conventions
**Labels:** `P0`, `area:ops`, `type:chore`, `size:S`  
**Acceptance criteria**
- [ ] Repo folders exist: `/api`, `/worker`, `/web`, `/docs`, `/infra`, `/shared`
- [ ] Formatting + linting config committed
- [ ] Pre-commit hooks documented
- [ ] Local dev quickstart in README

## Issue 1.2 — Environment config and secrets strategy
**Labels:** `P0`, `area:ops`, `type:chore`, `size:S`  
**Acceptance criteria**
- [ ] `.env.example` created with required keys
- [ ] No secrets committed in repo
- [ ] Secret naming conventions documented
- [ ] Staging vs prod env separation defined

## Issue 1.3 — Shared types package
**Labels:** `P0`, `area:ops`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Shared schemas for audit inputs/outputs exist in `/shared`
- [ ] JSON schema validation available to API + worker
- [ ] Versioned schema folder structure (`/shared/schemas/v1/...`)

---

# Milestone 2 — Multi-Tenant Platform Core (Auth + DB + Storage) (P0)

## Issue 2.1 — DB schema v1 + migrations
**Labels:** `P0`, `area:db`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Tables exist: `tenants`, `users`, `projects`, `audits`, `audit_tasks`, `audit_results`, `audit_scores`, `reports`, `cost_events`
- [ ] Migration can run from empty DB
- [ ] Indexes added for `tenant_id`, `audit_id`, timestamps

## Issue 2.2 — Tenant + RBAC rules
**Labels:** `P0`, `area:db`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Every table enforces tenant scoping
- [ ] Role model defined (owner, admin, member, viewer)
- [ ] API rejects cross-tenant access

## Issue 2.3 — File storage for report artifacts
**Labels:** `P0`, `area:db`, `area:ops`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Storage bucket created for `reports/` and `artifacts/`
- [ ] Signed URL generation supported
- [ ] Report metadata stored in `reports` table
- [ ] Upload/download tested in staging

---

# Milestone 3 — Audit Job Framework (API + Queue + Worker) (P0)

## Issue 3.1 — Create audit lifecycle endpoints
**Labels:** `P0`, `area:api`, `type:feature`, `size:M`  
**Endpoints**
- `POST /audits`
- `GET /audits/{id}`
- `GET /audits/{id}/results`
- `GET /audits/{id}/report`
**Acceptance criteria**
- [ ] `POST /audits` returns `audit_id` immediately
- [ ] Status updates work: queued → running → done/failed/partial
- [ ] Tenant auth enforced

## Issue 3.2 — Worker runner + task queue wiring
**Labels:** `P0`, `area:worker`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Worker consumes audit jobs from queue
- [ ] Worker writes progress updates to DB
- [ ] Worker retries on transient failures (429/timeouts)
- [ ] Worker respects per-tier limits (pages, prompts, calls)

## Issue 3.3 — Progress model + event log
**Labels:** `P0`, `area:api`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] `audit_tasks` represents module steps with status + timings
- [ ] Progress % computed deterministically
- [ ] Event log stored for debugging (non-sensitive)

## Issue 3.4 — Idempotent audit hashing
**Labels:** `P0`, `area:api`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Audit inputs produce a stable `inputs_hash`
- [ ] Option to reuse cached results for same hash within TTL
- [ ] Cache rules are configurable per tier

---

# Milestone 4 — Safe Fetching + Crawl Engine (SSRF + Robots + Sitemaps) (P0)

## Issue 4.1 — HTTP fetch client with SSRF protections
**Labels:** `P0`, `area:security`, `area:worker`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Blocks private IP ranges and localhost
- [ ] Blocks non-http(s) protocols
- [ ] Enforces timeouts + size limits
- [ ] Logs redacted request details (no secrets)

## Issue 4.2 — robots.txt parser + policy mode
**Labels:** `P0`, `area:seo-tech`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Fetch and parse robots.txt
- [ ] “Respect robots” mode default ON
- [ ] Records allow/deny results per URL
- [ ] Stores results in `audit_results` (robots check)

## Issue 4.3 — Sitemap discovery + validation
**Labels:** `P0`, `area:seo-tech`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Discover from robots + common paths
- [ ] Parse sitemap index + child sitemaps
- [ ] Validate URL status codes and canonical patterns
- [ ] Store results in `audit_results`

## Issue 4.4 — Crawl engine v1 (internal links, depth, orphans)
**Labels:** `P0`, `area:seo-tech`, `area:worker`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Crawl respects max pages per tier
- [ ] Builds link graph (inlinks/outlinks)
- [ ] Computes click depth distribution
- [ ] Detects orphan candidates (from sitemap vs crawl)

---

# Milestone 5 — Technical SEO Audit Module (P0)

## Issue 5.1 — Status code + redirect chain analysis
**Labels:** `P0`, `area:seo-tech`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Detects 3xx chains and loops
- [ ] Flags 4xx/5xx pages found in crawl and sitemaps
- [ ] Soft-404 heuristic included
- [ ] Outputs “top impacted URLs” list

## Issue 5.2 — Canonical + indexation directives audit
**Labels:** `P0`, `area:seo-tech`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Extracts canonical tags
- [ ] Detects missing, conflicting, cross-domain canonicals
- [ ] Captures meta robots and X-Robots-Tag
- [ ] Flags “indexed but noindex” contradictions (where detectable)

## Issue 5.3 — Security + mixed content + headers
**Labels:** `P0`, `area:seo-tech`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] TLS basics verified
- [ ] Mixed content detection on key pages
- [ ] Records key headers (HSTS, CSP presence checks)
- [ ] Outputs fix recommendations with evidence

## Issue 5.4 — Structured data extraction + rule-based validation
**Labels:** `P0`, `area:seo-tech`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Extract JSON-LD blocks per page
- [ ] Detect required schema types for trades (LocalBusiness, Service, FAQ when applicable)
- [ ] Flags mismatch between visible content and schema facts
- [ ] Stores normalized schema summary

## Issue 5.5 — PageSpeed / CWV integration + caching
**Labels:** `P0`, `area:seo-tech`, `area:worker`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Runs PageSpeed for key templates (home, service, location, contact)
- [ ] Caches results by URL + strategy for configurable TTL
- [ ] Stores LCP/INP/CLS and lab signals
- [ ] Generates prioritized performance fixes

---

# Milestone 6 — Local Presence + Conversion Audit (Trades Layer) (P0)

## Issue 6.1 — NAP + service area extraction from site
**Labels:** `P0`, `area:local`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Detects phone + address patterns on site
- [ ] Detects service area mentions (cities/regions)
- [ ] Flags inconsistency across pages
- [ ] Outputs a “Site NAP summary” object

## Issue 6.2 — Conversion readiness checks (mobile-first)
**Labels:** `P0`, `area:local`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Detects tap-to-call presence on mobile layout heuristics
- [ ] Detects quote form existence + basic friction checks
- [ ] Detects emergency/after-hours visibility signals
- [ ] Produces top 5 conversion fixes

## Issue 6.3 — Trades trust blocks detector
**Labels:** `P0`, `area:local`, `area:worker`, `type:feature`, `size:S`  
**Acceptance criteria**
- [ ] Detects license/insurance/warranty mentions
- [ ] Detects certifications and brand badges mentions
- [ ] Outputs recommendations to add/clarify trust blocks

---

# Milestone 7 — Content + Coverage Audit (Service + City Strategy) (P1)

## Issue 7.1 — Service taxonomy builder (HVAC/plumbing/electrical/GC presets)
**Labels:** `P1`, `area:seo-content`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Supports base taxonomies per trade
- [ ] Allows custom service list per project
- [ ] Maps services to existing URLs

## Issue 7.2 — City/service area coverage mapping
**Labels:** `P1`, `area:seo-content`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Builds matrix: service × city
- [ ] Identifies missing “money pages”
- [ ] Suggests build order by impact

## Issue 7.3 — Cannibalization detection
**Labels:** `P1`, `area:seo-content`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Detects multiple pages targeting same service intent
- [ ] Flags overlapping titles/H1s
- [ ] Provides merge/redirect guidance

## Issue 7.4 — Internal linking plan generator (rule-based first)
**Labels:** `P1`, `area:seo-content`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Produces linking plan: service ↔ city ↔ projects
- [ ] Flags orphan pages and weak inlink pages
- [ ] Outputs anchor text guidance (non-spammy)

---

# Milestone 8 — AI Platform Layer (Gateway + Site Facts + Guardrails) (P0)

## Issue 8.1 — Build AI Gateway interface (provider-agnostic)
**Labels:** `P0`, `area:ai`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Single interface for structured generation
- [ ] Supports multiple providers by config
- [ ] Logs provider/model/version per call
- [ ] Captures token usage and cost events

## Issue 8.2 — Enforce structured outputs + schema validation
**Labels:** `P0`, `area:ai`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] JSON schema defined for each AI output type
- [ ] Server-side validation on every AI response
- [ ] Retry strategy for invalid JSON
- [ ] Safe fallback template when AI fails

## Issue 8.3 — Site Facts pipeline (`site_facts.json`)
**Labels:** `P0`, `area:ai`, `area:worker`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Deterministic extraction of business facts from site + schema
- [ ] Stored as normalized object in `audit_results`
- [ ] Includes: name, NAP, services, hours, service areas, key URLs, trust assets
- [ ] Diffable between audits (“what changed” support)

## Issue 8.4 — Trades prompt library + versioning
**Labels:** `P0`, `area:ai`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Prompt sets for HVAC/plumbing/electrical/GC
- [ ] Prompt intent groups: emergency, install, repair, cost, near-me
- [ ] `prompt_set_version` stored per audit
- [ ] Temperature and other params locked per prompt

## Issue 8.5 — AI evaluation harness (regression tests)
**Labels:** `P0`, `area:ai`, `type:test`, `size:M`  
**Acceptance criteria**
- [ ] Golden prompt cases stored in repo
- [ ] CI runs schema compliance tests
- [ ] CI flags output drift beyond thresholds
- [ ] Report produced for failed evals

---

# Milestone 9 — AI Modules: AI Readiness + AI Surface Visibility (ASV) (P1)

## Issue 9.1 — AI Readiness audit (deterministic)
**Labels:** `P1`, `area:ai`, `area:seo-tech`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Checks index/snippet readiness signals (robots/noindex/nosnippet controls)
- [ ] Checks “important content is in text HTML” signals
- [ ] Checks entity consistency between schema and visible facts
- [ ] Outputs “AI readiness fixes” list

## Issue 9.2 — AI Surface Visibility (ASV) scoring model
**Labels:** `P1`, `area:ai`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Measures mention/coverage/accuracy against `site_facts.json`
- [ ] Stores raw AI outputs and scoring breakdown
- [ ] Caching rules to avoid repeat spend
- [ ] Confidence scoring included

## Issue 9.3 — ASV prompt execution runner (tier limits)
**Labels:** `P1`, `area:ai`, `area:worker`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Per-tier caps on prompts per audit
- [ ] Backoff + retry handling for 429/timeouts
- [ ] Partial results supported without job failure

---

# Milestone 10 — Scoring System + Composite Grade (P0)

## Issue 10.1 — Add `scoring.yaml` + scoring versioning
**Labels:** `P0`, `area:reporting`, `type:feature`, `size:S`  
**Acceptance criteria**
- [ ] `scoring.yaml` contains weights + grade bands
- [ ] `score_version` stored per audit
- [ ] Default weights set for trades

## Issue 10.2 — Composite scorer with caps and rules
**Labels:** `P0`, `area:reporting`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Overall score 0–100 computed from module scores
- [ ] Grade computed from score bands
- [ ] Caps applied (e.g., indexing blocked caps grade)
- [ ] Outputs explanation of why score is what it is

---

# Milestone 11 — Report Generator (PDF/DOCX) + Tiered Templates (P0)

## Issue 11.1 — Report template v1 (trades-friendly)
**Labels:** `P0`, `area:reporting`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] 1-page executive summary template
- [ ] “Top 3 lead leaks” section with evidence
- [ ] “14-day fix plan” section
- [ ] Template is versioned

## Issue 11.2 — Report renderer in worker + artifact storage
**Labels:** `P0`, `area:worker`, `area:reporting`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Rendering runs only in worker (not request thread)
- [ ] Report files stored in storage bucket
- [ ] Build log stored per report
- [ ] Download link accessible via API

## Issue 11.3 — Tiered report depth (Free/Starter/Platinum/Diamond)
**Labels:** `P1`, `area:reporting`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Free: 1–2 pages
- [ ] Starter: full technical + local + fix plan
- [ ] Platinum: adds coverage plan + briefs
- [ ] Diamond: adds monitoring + “changes shipped”

---

# Milestone 12 — Web Dashboard MVP (P0)

## Issue 12.1 — Auth + tenant switch UI
**Labels:** `P0`, `area:web`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Login works
- [ ] Tenant scoping enforced
- [ ] Basic user settings page
- [ ] New audit intake flow

## Issue 12.2 — New audit intake flow
**Labels:** `P0`, `area:web`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Form includes URL, company name, trade type, service areas
- [ ] Submits to `POST /audits`
- [ ] Shows created audit in history

## Issue 12.3 — Audit status + progress UI
**Labels:** `P0`, `area:web`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Status screen updates without refresh loops (polling ok)
- [ ] Shows module-by-module progress
- [ ] Shows clean error message on failure/partial

## Issue 12.4 — Results viewer + report download
**Labels:** `P0`, `area:web`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Scorecards for each module
- [ ] Top fixes list
- [ ] Report download works via signed URL
- [ ] Audit history list works

---

# Milestone 13 — Observability + Cost Controls (P0)

## Issue 13.1 — Structured logging + correlation IDs
**Labels:** `P0`, `area:observability`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Every audit log includes `audit_id`
- [ ] Logs are JSON
- [ ] Errors include error code and friendly message

## Issue 13.2 — Cost tracking (`cost_events`)
**Labels:** `P0`, `area:observability`, `area:ai`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Records PageSpeed calls per audit
- [ ] Records AI tokens/cost per call
- [ ] Records crawl pages fetched
- [ ] Simple “cost per audit” summary available via API

## Issue 13.3 — Admin dashboard (internal)
**Labels:** `P1`, `area:web`, `area:observability`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] View failed audits and error reasons
- [ ] View queue depth and runtimes
- [ ] View cost trends by tenant

---

# Milestone 14 — Security + Abuse Controls (P0)

## Issue 14.1 — Rate limiting and per-tenant quotas
**Labels:** `P0`, `area:security`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] API rate limiting by token + IP
- [ ] Per-tier audit concurrency caps
- [ ] Per-audit max pages and max prompts enforced

## Issue 14.2 — Sensitive data redaction
**Labels:** `P0`, `area:security`, `type:feature`, `size:S`  
**Acceptance criteria**
- [ ] Logs redact tokens and auth headers
- [ ] Stored raw AI outputs do not include secrets
- [ ] Upload scanning rules documented (file types, max size)

---

# Milestone 15 — Testing + “Works 150%” Hardening (P0)

## Issue 15.1 — Golden path E2E test (submit → run → download)
**Labels:** `P0`, `area:ci-cd`, `type:test`, `size:M`  
**Acceptance criteria**
- [ ] E2E runs in CI against staging env
- [ ] Verifies audit finishes and report downloads
- [ ] Fails CI on regression

## Issue 15.2 — Fixture sites library + expected checks
**Labels:** `P0`, `area:seo-tech`, `type:test`, `size:M`  
**Acceptance criteria**
- [ ] 5–10 fixture sites defined (or internal test URLs)
- [ ] Expected results documented (e.g., should detect broken sitemap)
- [ ] Integration tests use these fixtures
- [ ] Chaos tests (partial)

## Issue 15.3 — Chaos tests (timeouts, 429s, robots blocks)
**Labels:** `P0`, `area:worker`, `type:test`, `size:M`  
**Acceptance criteria**
- [ ] Simulate PageSpeed timeout
- [ ] Simulate AI 429
- [ ] Simulate crawl denied by robots
- [ ] System returns partial results and does not deadlock

## Issue 15.4 — `verify_release.sh` script
**Labels:** `P0`, `area:ci-cd`, `type:chore`, `size:S`  
**Acceptance criteria**
- [ ] Runs lint + unit + integration tests
- [ ] Builds API/worker/web
- [ ] Runs minimal audit in mock mode
- [ ] Prints clear pass/fail summary

---

# Milestone 16 — CI/CD + Deploy (Staging → Production) (P0)

## Issue 16.1 — Build and push containers (API + Worker)
**Labels:** `P0`, `area:ci-cd`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] CI builds docker images
- [ ] Images pushed to registry
- [ ] Version tags include git SHA

## Issue 16.2 — Staging deploy pipeline
**Labels:** `P0`, `area:ci-cd`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Deploys API + worker to staging
- [ ] Runs migrations
- [ ] Runs golden path test

## Issue 16.3 — Production deploy pipeline + rollback plan
**Labels:** `P0`, `area:ci-cd`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Manual approval step for prod deploy
- [ ] Rollback documented
- [ ] Post-deploy smoke test runs

---

# Milestone 17 — Diamond Ops (Done-For-You Workflow) (P1)

## Issue 17.1 — Implementation backlog generator (“Next 10 fixes”)
**Labels:** `P1`, `area:ops`, `area:web`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Converts findings into a prioritized task list
- [ ] Includes effort estimate buckets (S/M/L)
- [ ] Exports to CSV or “copy to clipboard” format

## Issue 17.2 — “What changed since last audit” diff
**Labels:** `P1`, `area:ops`, `area:db`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Diffs `site_facts.json` across audits
- [ ] Diffs scores and top issues
- [ ] Outputs short monthly summary

## Issue 17.3 — Monthly Diamond report (leads-first)
**Labels:** `P1`, `area:reporting`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Highlights work shipped
- [ ] Shows progress trend
- [ ] Ties to leads metrics where available
- [ ] Includes next month plan

---

# Milestone 18 — Integrations (GA4/GSC/GBP) (P2)

## Issue 18.1 — GA4 connector (read-only)
**Labels:** `P2`, `area:ops`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] OAuth flow works
- [ ] Pulls key events (calls/forms if tracked)
- [ ] Stores metrics per audit/month

## Issue 18.2 — Google Search Console connector (read-only)
**Labels:** `P2`, `area:ops`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Connects via OAuth
- [ ] Pulls queries/pages/clicks/impressions by time range
- [ ] Adds “top queries to build pages for” output

## Issue 18.3 — GBP connector (optional, depends on access)
**Labels:** `P2`, `area:local`, `type:spike`, `size:L`  
**Acceptance criteria**
- [ ] Feasibility confirmed
- [ ] Minimal data pulled (categories, hours, reviews count)
- [ ] Stored in project profile

---

# Milestone 19 — Optional: Ralph Loop / Multi-Agent Dev Automation (P3)

## Issue 19.1 — Task queue for internal agents
**Labels:** `P3`, `area:ops`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Agents can pull tasks and post updates
- [ ] Progress tracker script works
- [ ] Tasks complete with explicit done markers

---

## Suggested GitHub Milestones order (shipping path)
1) Foundation + Repo Standards  
2) Multi-Tenant Platform Core  
3) Audit Job Framework  
4) Safe Fetching + Crawl Engine  
5) Technical SEO Audit  
6) Local + Conversion Audit  
10) Scoring System + Composite Grade  
11) Report Generator  
12) Web Dashboard MVP  
13) Observability + Cost Controls  
14) Security + Abuse Controls  
15) Testing + Hardening  
16) CI/CD + Deploy  
(Then) Content + Coverage, AI modules, Diamond ops, integrations

---

# Milestone 20 — Cost Tier System (Implemented Jan 2026)

**Status:** ✅ COMPLETED (Jan 19, 2026)

This milestone adds a configurable cost tier system for running reports at different quality/cost levels.

## Issue 20.1 — Create tier configuration files
**Labels:** `P0`, `area:ops`, `type:feature`, `size:S`  
**Status:** ✅ Complete
**Acceptance criteria**
- [x] `config/tier_low.env` — Budget Watchdog (~$0.023/report)
- [x] `config/tier_medium.env` — Smart Balance (~$0.051/report)
- [x] `config/tier_high.env` — Premium Agency (~$0.158/report)
- [x] Each tier defines optimal model selection per provider

## Issue 20.2 — Tier comparison generator
**Labels:** `P0`, `area:reporting`, `type:feature`, `size:M`  
**Status:** ✅ Complete
**Acceptance criteria**
- [x] `generate_tier_comparison.py` created
- [x] Can generate reports for all tiers: `python3 generate_tier_comparison.py <json> all`
- [x] Produces side-by-side comparison PDFs

## Issue 20.3 — Model cost optimization
**Labels:** `P0`, `area:ai`, `type:chore`, `size:M`  
**Status:** ✅ Complete
**Acceptance criteria**
- [x] OpenAI models updated to correct names: `gpt-5-nano`, `gpt-5-mini`, `gpt-5`
- [x] Image model updated: `gpt-image-1-mini` (fallback), `imagen-4.0-fast-generate-001` (primary)
- [x] Two-tier model strategy implemented (FAST vs QUALITY)

## Cost Breakdown

| Tier | Name | Cost/Report | Monthly @ 3K | Annual |
|------|------|-------------|--------------|--------|
| LOW | Budget Watchdog | $0.023 | $69 | $828 |
| MEDIUM | Smart Balance | $0.051 | $153 | $1,836 |
| HIGH | Premium Agency | $0.158 | $474 | $5,688 |

## Model Stack by Tier

### LOW Tier (Budget Watchdog)
- **OpenAI:** `gpt-5-nano` (all operations)
- **Google:** `gemini-3.0-flash`, `imagen-4.0-fast-generate-001`
- **xAI:** `grok-4-1-fast`
- **Perplexity:** `sonar`

### MEDIUM Tier (Smart Balance)
- **OpenAI:** `gpt-5-nano` → `gpt-5` (quality where needed)
- **Anthropic:** `claude-4-haiku` → `claude-sonnet-4-5` (for summaries)
- **Google:** `gemini-3.0-flash` / `gemini-3.0-pro`, `imagen-4.0-generate-001`
- **xAI:** `grok-4-1` (full quality for sentiment)
- **Perplexity:** `sonar-pro` (competitive analysis)

### HIGH Tier (Premium Agency)  
- **OpenAI:** `gpt-5` / `gpt-5.1`
- **Anthropic:** `claude-sonnet-4-5` (all analysis)
- **Google:** `gemini-3.0-pro`, `imagen-4.0-ultra-generate-001`
- **xAI:** `grok-4-1`
- **Perplexity:** `sonar-pro`

---

# Milestone 21 — Grok Integration for Social Sentiment (P1)

**Status:** 🔄 Planned

## Issue 21.1 — Integrate Grok for X/Twitter sentiment
**Labels:** `P1`, `area:ai`, `type:feature`, `size:M`  
**Acceptance criteria**
- [ ] Add social sentiment section to premium reports
- [ ] Use `grok-4-1-fast` for cost-effective sentiment analysis
- [ ] Pull real-time brand mentions and sentiment from X/Twitter
- [ ] Include sentiment score in overall AI visibility metrics

## Issue 21.2 — "Grokopedia" brand presence audit
**Labels:** `P1`, `area:ai`, `type:feature`, `size:L`  
**Acceptance criteria**
- [ ] Audit how brand appears in Grok's knowledge base
- [ ] Compare brand presence across AI platforms
- [ ] Generate recommendations for improving AI visibility

---
