# Project Alignment & Strategy Audit Report

**Role:** Senior Product Engineer and Strategic Lead  
**Date:** February 2026  
**Scope:** SEO Health Report system (repository deep-dive)

---

## Phase 1: Deep Understanding

### Primary Objective

**What problem does this solve?**

The system solves the gap between traditional SEO audits and AI-era visibility. It generates **branded SEO health reports** by orchestrating three audits:

1. **Technical SEO** (30% weight) – crawlability, speed, security, mobile, structured data  
2. **Content & Authority** (35% weight) – E-E-A-T, topic clusters, link profile  
3. **AI Visibility** (35% weight) – how brands appear in ChatGPT, Claude, Perplexity

The **differentiator** is AI Visibility: most agencies do not evaluate how brands show up in AI-generated answers. The product positions itself as delivering **$8K–$10K agency value** through automation (typical agency pricing $5K–11K for comparable scope) with **5–20x cost advantage** ($500–2K/month vs $8K–10K/month) and **300–1600% ROI** vs traditional agencies.

**Composite scoring:**  
`Overall Score = (Technical × 0.30) + (Content × 0.35) + (AI × 0.35)`  
Grades A–F (90–100 = A, &lt;60 = F). Outputs include DOCX/PDF reports, executive summaries, and prioritized recommendations.

---

### Technical Stack

**Backend**

- **Language:** Python 3.9+  
- **API:** FastAPI, Uvicorn (ASGI)  
- **Validation:** Pydantic v2.5  
- **HTTP:** `requests`, `httpx` (async), `beautifulsoup4`, `lxml`  
- **Report generation:** `python-docx`, `reportlab`, Pillow, matplotlib  
- **AI:** Anthropic (required), optional OpenAI, Perplexity, xAI, Google Gemini  
- **Caching:** diskcache; infra assumes Redis (not yet wired in app)  
- **Entry points:** `run_audit.py`, `api_server.py`, `generate_premium_report.py`, `generate_free_report.py`

**Frontend**

- **Framework:** React 18.2, Vite 5  
- **Styling:** Tailwind CSS 3.4  
- **State:** React Redux 9.1  
- **UI:** Framer Motion, Lucide React, Recharts, clsx, tailwind-merge  
- **Dev:** ESLint, PostCSS, Autoprefixer  
- **Dev server:** Vite (e.g. port 5173); docs reference port 3000 for “complete system”

**Supporting systems**

- **Testing:** pytest, pytest-asyncio, pytest-cov, pytest-mock  
- **Quality:** ruff, mypy, black  
- **CI:** GitHub Actions (Python 3.10–3.12 matrix, unit + integration, frontend build, ruff, mypy)  
- **Infra:** Terraform (AWS VPC, ECS, RDS Postgres, ElastiCache Redis, CloudWatch, SNS), Kubernetes (HPA 3–10 replicas), Docker Compose (app, Postgres, Redis, Prometheus, Grafana, nginx), deploy script

**Key config files:** `pyproject.toml`, `seo-health-report/requirements.txt`, `ai-visibility-audit/requirements.txt`, `seo-technical-audit/requirements.txt`, `seo-content-authority/requirements.txt`, `competitive-monitor/requirements.txt`, `frontend/package.json`, `.env.example`.

---

### User Persona

**Primary (Priority 1)**  
- **C-suite executives** – Daily intelligence briefs with ROI projections for SEO investment decisions.  
- **Business owners** – Track brand visibility in AI answer engines (ChatGPT, Claude, Perplexity) and optimize for citations.

**Secondary (Priority 2)**  
- **Marketing managers** – Continuous monitoring of 50+ competitors with alerts (e.g. within 1 hour) and trend analysis.

**Target market**  
- SEO agencies, consultants, and businesses seeking comprehensive audits as an alternative to traditional $5K–11K agency engagements.  
- RaapTech branding skill targets MEP contractors separately; core product is the SEO audit platform.

---

## Phase 2: Project Health Rating

| Pillar | Rating (1–10) | Justification |
|--------|----------------|---------------|
| **Feasibility** | **7** | Logic is sound: three audit modules exist, composite scoring is defined, report generation (DOCX/PDF) and API are implemented. **237 tests passing**, CI runs unit + integration. Feasibility is reduced by: (1) **unresolved merge conflict in `api_server.py`** (lines 72–112) between rate-limiting middleware and `ErrorResponse` model, which can prevent the API from running; (2) optional `start_complete_system.py` referenced in docs is absent; (3) API currently uses in-memory `audit_results = {}` and in-memory rate limiting, so behavior is correct for single process but not production-grade. |
| **Scalability** | **5** | Architecture is modular (orchestrator + three audit packages) and infra is built for growth (K8s HPA, Terraform RDS/Redis). **Blockers:** (1) No shared state – `api_server.py` uses an in-memory dict for audit results and rate limits; multi-instance or restart loses state. (2) Background audit runs via FastAPI `BackgroundTasks` – no persistence or retry. (3) Infra expects Postgres/Redis (`DATABASE_URL`, `REDIS_URL`) but the app does not use them yet. (4) K8s/Terraform assume a single app image on port 3000, while `api_server.py` runs on **port 8000** and there is no Dockerfile in the repo. Scaling is designed in infra but app is not wired for it. |
| **Deployment Readiness** | **4** | Pre-deployment checklist is partially done (tests, no hardcoded secrets, frontend builds, env documented). **Blockers:** (1) **Merge conflict in `api_server.py`** must be resolved or the server may not start. (2) **No Dockerfile** – `docker-compose.prod.yml` and K8s reference `seo-health-report:latest`; image cannot be built as specified. (3) **Port mismatch:** Compose/K8s/nginx expect app on **3000**, API runs on **8000** – health checks and routing would fail. (4) **No `/ready` endpoint** – K8s readinessProbe uses `/ready`; only `/health` exists. (5) **Env validation** – no startup check for required vars (e.g. `API_KEY`, `ANTHROPIC_API_KEY`). (6) **CORS in nginx** – `infrastructure/nginx/mobile.conf` uses `Access-Control-Allow-Origin "*"` for mobile API. (7) Deployment checklist (environment, monitoring, go-live) is largely unchecked. Rating reflects “not yet production-grade” without the above fixes. |

---

## Phase 3: Road to Deployment

### Critical Path to Launch

**P0 – Unblock runnable application**

1. **Resolve merge conflict in `api_server.py` (lines 72–112)**  
   Keep rate-limiting middleware and add `ErrorResponse` (or equivalent) so the file is valid and the server starts.

2. **Add a Dockerfile** at repo root (or documented path) that installs Python deps, sets `CMD` to run the API (e.g. `uvicorn api_server:app --host 0.0.0.0 --port 8000`), and aligns with the image name used in Compose/K8s.

3. **Align port and health checks**  
   - Either: change app to listen on **3000** (if infra must stay as-is), or  
   - Change `docker-compose.prod.yml`, K8s `containerPort`/probes, and nginx upstream to **8000**.  
   Then ensure health checks hit the actual port (e.g. `http://localhost:8000/health` in Compose).

4. **Implement `/ready`**  
   Add a readiness endpoint (e.g. dependency checks optional) and point K8s readinessProbe at it so orchestration works as intended.

**P1 – Production-grade behavior**

5. **Replace in-memory audit state**  
   Persist audit results and status in Redis or Postgres so multiple instances and restarts do not lose data.

6. **Redis-backed rate limiting**  
   Move rate-limit state to Redis so it works across replicas and restarts.

7. **Environment validation**  
   On startup, validate required env (e.g. `API_KEY`, `ANTHROPIC_API_KEY`) and fail fast with a clear message if missing.

8. **Background jobs**  
   For long-running audits, consider a task queue (e.g. Celery) or at least durable job state so runs survive restarts and can be retried.

**P2 – Security and ops**

9. **CORS in nginx**  
   Replace `Access-Control-Allow-Origin "*"` in `infrastructure/nginx/mobile.conf` with an explicit allowlist or env-driven origin.

10. **Complete deployment checklist**  
    Execute and tick off items in `docs/DEPLOYMENT_CHECKLIST.md` (environment, monitoring, security, testing, go-live, post-deployment).

---

### Immediate Next Steps (in order)

1. Resolve the merge conflict in `api_server.py`.  
2. Create a Dockerfile and verify `docker build` / `docker run` with the API.  
3. Fix port (8000 vs 3000) and health/readiness probes in Compose and K8s.  
4. Add `/ready` and wire K8s readinessProbe to it.  
5. Add startup validation for required environment variables.  
6. Document in README or deploy guide: image name, port, and how to run the API in production.

---

### Bottlenecks

- **Single-process assumption** – In-memory state and rate limiting prevent horizontal scaling until Redis/DB are used.  
- **No container build path** – Missing Dockerfile blocks any container-based deploy.  
- **Conflicting docs** – COMPLETE_SYSTEM_README references `start_complete_system.py` (missing) and port 3000 for backend; actual API is `api_server.py` on 8000.  
- **Terraform** – References `aws_ecs_service.app` in CloudWatch alarm dimensions but ECS service definition is not present in the excerpt; need to confirm ECS task definition and service exist.  
- **Heavy audits** – Long-running AI and crawl workloads may need higher resource limits (current K8s 256Mi–512Mi, 250m–500m CPU) and timeouts.

---

### Security Risks

- **Merge conflict** – Left unresolved, can cause runtime errors or inconsistent behavior.  
- **CORS wildcard** in nginx (`Access-Control-Allow-Origin "*"`) – Increases risk of misuse from arbitrary origins; restrict to known frontends.  
- **API_KEY required** – Bearer auth is implemented; ensure `API_KEY` is never defaulted or committed.  
- **Rate limiting** – Implemented but in-memory; under multi-instance or bypass, limits are not global.  
- **Secrets** – K8s uses `secretKeyRef` for DB and Anthropic key; ensure secrets are created and not logged.  
- **Input validation** – Audit request body is validated by Pydantic; continue to validate URL/inputs to avoid SSRF or abuse of crawler/AI calls.

---

## Key Risks Validation

The following three areas are explicitly validated against documentation, infrastructure configs, and the current API server.

### 1. Conflicting readiness signals (docs vs. runtime blockers)

| Doc / artifact | Signal | Runtime reality | Validation |
|----------------|--------|-----------------|------------|
| **PROGRESS.md** | “~90% complete”, “237 tests passing”, “Infrastructure configs (Docker, K8s, Terraform)” | API has unresolved merge conflict in `api_server.py` (lines 72–112); server may not start | **Conflict:** Docs imply runnable app; runtime is blocked by conflict |
| **DEPLOYMENT_CHECKLIST.md** | Pre-deployment ✅ (modules tested, no hardcoded secrets, frontend builds) | No Dockerfile; app listens on 8000; infra expects 3000; no `/ready` | **Conflict:** Checklist suggests “ready to configure env”; deploy path is incomplete |
| **COMPLETE_SYSTEM_README.md** | “Backend API: http://localhost:8000”, “Start: python3 start_complete_system.py” | `start_complete_system.py` is absent; only `api_server.py` and `start_app.sh` exist | **Conflict:** Documented launcher and “complete system” do not match repo |
| **README.md** | “Production Readiness … Maturity Score 90/100” | Merge conflict, in-memory state, port mismatch, no container image | **Conflict:** Maturity score does not reflect current deploy blockers |

**Conclusion:** Readiness signals in docs are optimistic relative to runtime. Resolve merge conflict, add Dockerfile, and align ports/health checks so docs and deploy path match.

---

### 2. Infra assumptions vs. current API server

| Assumption (infra) | Current API server | Validation |
|--------------------|--------------------|------------|
| **Port** | Compose: `3000:3000`; K8s: `containerPort: 3000`; nginx: `server app:3000` | `api_server.py`: `uvicorn.run(app, host="0.0.0.0", port=8000)` | **Mismatch:** Infra assumes 3000; app uses 8000. Health checks and routing would fail. |
| **Health** | Compose: `http://localhost:3000/health`; K8s liveness: `path: /health`, `port: 3000` | `/health` exists and returns `{"status": "healthy"}` | **Match** only if app is exposed on 3000; otherwise probe target is wrong. |
| **Readiness** | K8s readinessProbe: `path: /ready`, `port: 3000` | No `/ready` endpoint | **Mismatch:** Probe will 404; pods may be marked not ready or fail. |
| **Container image** | Compose: `image: seo-health-report:latest`; K8s: `image: seo-health-report:latest` | No Dockerfile in repo | **Mismatch:** Image cannot be built as specified; deploy fails at build/pull. |
| **Env** | Compose/K8s: `DATABASE_URL`, `REDIS_URL`, `ANTHROPIC_API_KEY` | App uses `audit_results = {}`, in-memory rate limit; no DB/Redis usage; no startup env validation | **Mismatch:** Infra assumes persisted state and Redis; app does not use them yet. |

**Conclusion:** Align port (either change app to 3000 or change all infra to 8000), add `/ready`, add a Dockerfile that runs the API, and either wire app to DATABASE_URL/REDIS_URL or adjust infra to match current in-memory design.

---

### 3. Security posture (auth, rate limiting, CORS) vs. production defaults

| Control | Current implementation | Production default / expectation | Validation |
|---------|------------------------|----------------------------------|------------|
| **Auth** | `HTTPBearer` in `api_server.py`; `API_KEY` from env; 401 on invalid key; 500 if `API_KEY` unset | Production: require auth on all sensitive routes; no default or fallback key | **Partial:** Auth is implemented. **Gap:** No startup check for `API_KEY`; server can start without it and fail at request time. |
| **Rate limiting** | In-memory `defaultdict(list)` per IP; 100 req/hour; middleware sets `X-RateLimit-*` headers | Production: global limit across replicas; state in Redis or similar | **Gap:** In-memory limits are per-process; multi-instance or restart resets limits. Not suitable for production at scale. |
| **CORS (API)** | FastAPI: `allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")` | Production: explicit allowlist, no wildcard in production | **OK:** Default is single origin; configurable via env. |
| **CORS (nginx)** | `infrastructure/nginx/mobile.conf`: `add_header Access-Control-Allow-Origin "*"` | Production: restrict to known frontend/origin | **Gap:** Wildcard allows any origin; should be allowlist or env-driven. |
| **Secrets** | K8s: `secretKeyRef` for `database-url`, `anthropic-api-key`; `.env.example` documents vars | Production: secrets in vault or K8s secrets; never logged or in images | **OK** if secrets are created and not committed; no validation that app avoids logging them. |

**Conclusion:** Auth and API CORS are acceptable with the addition of startup validation for `API_KEY`. Rate limiting and nginx CORS need hardening (Redis-backed limits, CORS allowlist) before production.

---

## Summary

| Phase | Finding |
|-------|--------|
| **Objective** | Branded SEO health reports (Technical + Content + AI Visibility) with composite scoring; AI visibility is the differentiator vs agencies. |
| **Stack** | Python/FastAPI backend, React/Vite frontend, pytest/CI, Terraform/K8s/Docker Compose for infra. |
| **Persona** | C-suite, business owners, marketing managers; agencies and businesses replacing high-cost audits. |
| **Feasibility** | 7/10 – Logic and tests support the product; merge conflict and in-memory design hold it back. |
| **Scalability** | 5/10 – Infra is ready; app state and jobs are not yet shared across instances. |
| **Deployment** | 4/10 – Image build, port, health/ready, and state must be fixed before production. |
| **Critical path** | Resolve conflict → Dockerfile → port/probes → `/ready` → env validation → then persistent state and rate limiting → then CORS and checklist. |

Once P0 and P1 are done, the project is in a position to move toward a first production deployment with clear follow-up work for scaling and hardening.
