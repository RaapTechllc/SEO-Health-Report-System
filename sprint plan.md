# Sprint Plan — SEO Health Report System (End-to-End)

Assumptions:

* **2-week sprints**
* Goal is a **deployable MVP** first (P0), then P1 upgrades (Platinum/Diamond)
* Each sprint ends with a **demo** and a **release candidate** build (even if not shipped)

---

## Sprint 1 (Weeks 1–2) — Platform Skeleton + Multi-Tenant Core

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
* Web can be minimal placeholder or skipped this sprint

**Exit criteria**

* [ ] Migrations + seed work in local + staging
* [ ] Tenant scoping enforced at API layer
* [ ] Audit record created and visible via `GET /audits/{id}`

---

## Sprint 2 (Weeks 3–4) — Job Framework + Worker Wiring + Safe Fetching

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

---

## Sprint 3 (Weeks 5–6) — Crawl Foundations (Robots + Sitemaps + Crawl Graph)

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

---

## Sprint 4 (Weeks 7–8) — Technical SEO Audit v1 + Trades Local/Conversion v1

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

---

## Sprint 5 (Weeks 9–10) — AI Layer (Future-Proof) + Reporting v1 + Cost Tracking

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

---

## Sprint 6 (Weeks 11–12) — Web Dashboard MVP + Security/Quotas + E2E “Works 150%”

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

## Sprint 7 (Weeks 13–14) — CI/CD + Staging→Prod + Chaos Hardening

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

---

# Post-MVP (P1) — Platinum + Diamond Value Sprints

## Sprint 8 (Weeks 15–16) — Content + Coverage (Platinum Core)

**Goal:** Generate the “coverage map” that sells Platinum in trades.

**Scope**

* 7.1 Service taxonomy builder (trade presets)
* 7.2 City/service area coverage mapping
* 7.3 Cannibalization detection
* 7.4 Internal linking plan generator

**Exit criteria**

* [ ] Service×City matrix output is usable and prioritized
* [ ] Briefs/plan output can be dropped into delivery workflow

---

## Sprint 9 (Weeks 17–18) — AI Readiness + ASV v1 (Measured, Not Hype)

**Goal:** AI features that are stable: readiness + accuracy vs Site Facts.

**Scope**

* 9.1 AI Readiness audit (deterministic)
* 9.2 ASV scoring model (accuracy/coverage against Site Facts)
* 9.3 ASV prompt runner (tier limits + caching)

**Exit criteria**

* [ ] ASV produces repeatable scoring and stores raw outputs
* [ ] AI Readiness recommendations are evidence-based and deterministic

---

## Sprint 10 (Weeks 19–20) — Diamond Ops (Done-For-You Engine)

**Goal:** Productized delivery: backlog, diffs, monthly reporting.

**Scope**

* 17.1 Implementation backlog generator (“Next 10 fixes”)
* 17.2 “What changed since last audit” diff
* 17.3 Monthly Diamond report (leads-first)

**Exit criteria**

* [ ] Diamond workflow is repeatable across 5 clients without custom chaos
* [ ] Monthly report clearly shows “work shipped + impact + next plan”

---

## Sprint 11+ (Optional) — Integrations for Proof and Retention (P2)

**Goal:** Tie work to leads and rankings (stickiness).

**Scope**

* 18.1 GA4 connector
* 18.2 GSC connector
* 18.3 GBP connector (spike → then build)

**Exit criteria**

* [ ] Leads-first reporting is automated where possible
* [ ] “Top queries to build pages for” becomes a Platinum upsell engine

---

## Notes on Parallel Work (How to go faster)

You can run these tracks in parallel if you have multiple devs:

* **Track A:** Platform/DB/API/CI
* **Track B:** Worker + crawl + audits
* **Track C:** Reporting + templates
* **Track D:** Web dashboard

---

END
