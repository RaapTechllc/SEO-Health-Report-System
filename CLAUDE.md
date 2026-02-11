# SEO Health Report System - Claude Code Instructions

## Project Overview

A production-grade SEO audit platform that generates branded health reports by orchestrating three audit pillars: technical SEO, content/authority, and AI visibility. Built as a Python monorepo with a FastAPI backend, async job worker, Jinja2 dashboard, and multi-provider AI integrations.

**Version:** 1.0.0
**License:** MIT
**Python:** 3.9+
**Status:** MVP complete (~90%), post-MVP enhancements in progress

## Repository Structure

```
SEO-Health-Report-System/
├── packages/                        # Core Python packages (monorepo)
│   ├── seo_health_report/           # Master orchestrator + report generation
│   │   ├── config.py                # Configuration management
│   │   ├── premium_report.py        # Premium PDF report generation
│   │   ├── tier_config.py           # LOW/MEDIUM/HIGH tier definitions
│   │   ├── charts.py                # Chart generation
│   │   ├── human_copy.py            # Natural language copy
│   │   ├── branding/                # Brand customization
│   │   ├── metrics/                 # Metric calculations
│   │   ├── pdf_components/          # PDF generation components
│   │   ├── providers/               # External provider integrations
│   │   ├── quotas/                  # Quota management
│   │   └── scripts/                 # Orchestration scripts (orchestrate.py, calculate_scores.py)
│   ├── seo_technical_audit/         # Technical SEO analysis (30% weight)
│   ├── ai_visibility_audit/         # AI system presence analysis (35% weight)
│   ├── seo_content_authority/       # Content & authority analysis (35% weight)
│   ├── config/                      # Shared config (settings, environments, RBAC, secrets)
│   ├── core/                        # Core utilities (env, formatting, safe_fetch, cost_tracker)
│   ├── schemas/                     # Pydantic data models (models.py)
│   ├── storage/                     # Cloud storage abstraction (local + S3)
│   ├── ai_image_generator/          # Image generation (OpenAI DALL-E, Google Gemini)
│   ├── seo_health_sdk/              # SDK for external consumers
│   └── design-tokens/               # Design system tokens
├── apps/                            # Application layer
│   ├── api/                         # FastAPI REST API (main.py, routers/, middleware/)
│   ├── worker/                      # Async job worker (executor.py, handlers/)
│   ├── dashboard/                   # Jinja2 dashboard (routes.py, templates/, static/)
│   ├── admin/                       # Admin interface
│   ├── cli/                         # CLI tools (run_audit.py, verify_sheetmetal.py)
│   └── web/                         # Static web assets
├── infrastructure/                  # DevOps & deployment
│   ├── docker/                      # Dockerfiles (api.Dockerfile, worker.Dockerfile)
│   ├── k8s/                         # Kubernetes manifests
│   ├── migrations/                  # Alembic DB migrations (v001-v007)
│   ├── monitoring/                  # Prometheus + Grafana configs
│   └── nginx/                       # Nginx configs
├── tests/                           # Test suites
│   ├── e2e/                         # End-to-end tests
│   ├── chaos/                       # Chaos engineering tests
│   ├── integration/                 # Integration tests
│   └── fixtures/                    # Test fixtures & mock data
├── docs/                            # Documentation
├── config/                          # Tier environment files (tier_low.env, etc.)
├── competitive_intel/               # Competitive intelligence module
├── competitive_monitor/             # Competitive monitoring module
├── .github/workflows/               # CI/CD pipelines
├── .kiro/                           # Agent framework (specs, steering, workflows)
└── [root scripts]                   # Entry points (run_audit.py, database.py, auth.py, etc.)
```

## Architecture

### Three-Pillar Scoring

```
Overall Score = (Technical x 0.30) + (Content x 0.35) + (AI x 0.35)
```

| Pillar | Weight | Package | Focus |
|--------|--------|---------|-------|
| Technical SEO | 30% | `packages/seo_technical_audit/` | Crawlability, speed, security, mobile, structured data |
| Content & Authority | 35% | `packages/seo_content_authority/` | Content quality, backlinks, domain authority |
| AI Visibility | 35% | `packages/ai_visibility_audit/` | Brand presence in Claude, ChatGPT, Perplexity, Grok |

### Three-Tier Cost System

| Tier | Cost/Report | Config | Use Case |
|------|-------------|--------|----------|
| LOW | ~$0.023 | `config/tier_low.env` | Budget "Watchdog" |
| MEDIUM | ~$0.051 | `config/tier_medium.env` | Smart "Balance" |
| HIGH | ~$0.158 | `config/tier_high.env` | Premium "Agency" |

### Service Architecture

- **API** (`apps/api/main.py`): FastAPI server with rate limiting, RBAC, audit endpoints
- **Worker** (`apps/worker/main.py`): Async job executor with lease-based processing
- **Dashboard** (`apps/dashboard/routes.py`): Jinja2 web dashboard with auth
- **CLI** (`apps/cli/run_audit.py`): Command-line audit runner

### AI Provider Strategy

| Provider | Use Case |
|----------|----------|
| Anthropic Claude | SEO analysis, content recommendations, executive summaries |
| OpenAI | Cross-source synthesis, narrative summaries, image generation (DALL-E) |
| Perplexity | "Does brand appear in AI search?" with citations |
| xAI Grok | Real-time reputation, X/Twitter sentiment, trends |
| Google Gemini | Large-context analysis, image generation (Imagen) |

Each provider uses a two-tier model strategy: `*_MODEL_FAST` for high-volume presence checks, `*_MODEL_QUALITY` for analysis and report generation.

## Commands

```bash
# Run an SEO audit
python run_audit.py --url https://example.com --company "Example Co"

# Run premium audit
python run_premium_audit.py --url https://example.com

# Run tests
pytest tests/                          # All tests
pytest tests/ -m unit                  # Unit tests only
pytest tests/ -m integration           # Integration tests only
pytest tests/e2e/                      # End-to-end tests
pytest tests/chaos/                    # Chaos engineering tests

# Linting and formatting
ruff check .                           # Lint (line-length=100, target py39)
ruff check . --fix                     # Auto-fix lint issues
black .                                # Format code (line-length=100)
mypy .                                 # Type checking

# Start API server
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

# Start worker
python -m apps.worker.main

# Database migrations
alembic upgrade head                   # Apply all migrations
alembic revision --autogenerate -m "description"  # Create migration

# Docker
docker compose up                      # Start dev environment (API + Worker + PostgreSQL)
docker compose -f docker-compose.production.yml up  # Production
```

## Development Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"                # Install with dev dependencies
pip install -e ".[ai]"                 # Install AI provider SDKs
cp .env.example .env                   # Configure environment
pytest tests/ -v                       # Verify setup
```

### Required Environment Variables

- `DATABASE_URL` - SQLite (dev) or PostgreSQL (prod)
- `JWT_SECRET_KEY` - Auth token signing (must change in prod)

### Optional API Keys

- `ANTHROPIC_API_KEY` - Required for SEO analysis
- `OPENAI_API_KEY` - For synthesis and image generation
- `GOOGLE_API_KEY` - For Gemini and PageSpeed API
- `PERPLEXITY_API_KEY` - For AI search presence checks
- `XAI_API_KEY` - For Grok real-time reputation

## Coding Standards

- **Python 3.9+** with type hints on all public functions
- **Line length:** 100 characters (enforced by ruff and black)
- **Linter:** Ruff with rules E, F, W, I, N, UP, B, C4 (see `pyproject.toml [tool.ruff]` for per-file ignores)
- **Formatter:** Black (line-length=100, target py39-py312)
- **Type checker:** mypy (python_version=3.9, ignore_missing_imports=true)
- **Data validation:** Pydantic v2 models in `packages/schemas/models.py`
- **Database:** SQLAlchemy 2.0 ORM; Alembic for migrations
- **Async:** aiohttp/httpx for HTTP; pytest-asyncio for async tests
- **Security:** SSRF protection via `packages/core/safe_fetch.py`; OWASP Top 10 awareness

### Import Conventions

Packages are mapped in `pyproject.toml [tool.setuptools.package-dir]`:
```python
from config import Settings              # packages/config/
from core.safe_fetch import safe_fetch    # packages/core/
from schemas.models import AuditResult   # packages/schemas/
from seo_health_report import ...        # packages/seo_health_report/
```

### Test Conventions

- **Framework:** pytest with pytest-asyncio (asyncio_mode=auto)
- **Structure:** `tests/{e2e,chaos,integration,fixtures}/` + root-level test files
- **Markers:** `unit`, `integration`, `slow`, `async`, `email`, `scheduler`, `performance`
- **Strict mode:** `--strict-markers --strict-config` enforced
- **CI environment:** `TESTING=true`, `DATABASE_URL=sqlite:///./test.db`, `JWT_SECRET_KEY=test-secret-key-for-ci`

## CI/CD Pipeline

GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `ci.yml` | push/PR to main | lint, test, e2e, chaos, smoke, verify-release, frontend |
| `test.yml` | push/PR | Test execution |
| `lint.yml` | push/PR | Ruff, Black, MyPy |
| `deploy-staging.yml` | manual/merge | Staging deployment |
| `deploy-production.yml` | manual/tag | Production deployment |
| `docker-build.yml` | push/PR | Docker image build |
| `rollback.yml` | manual | Rollback procedures |

CI runs on Python 3.11 with a matrix for 3.10-3.12. Frontend builds with Node 20.

## Key Files Reference

| File | Purpose |
|------|---------|
| `run_audit.py` | Main CLI entry point |
| `packages/seo_health_report/scripts/orchestrate.py` | Core audit orchestration |
| `packages/seo_health_report/scripts/calculate_scores.py` | Score computation |
| `packages/seo_health_report/premium_report.py` | Premium PDF report generation |
| `packages/seo_health_report/tier_config.py` | Tier configuration (LOW/MEDIUM/HIGH) |
| `packages/config/settings.py` | Application settings (Pydantic) |
| `packages/schemas/models.py` | Shared Pydantic data models |
| `packages/core/safe_fetch.py` | SSRF-protected HTTP client |
| `apps/api/main.py` | FastAPI application |
| `apps/worker/executor.py` | Job execution engine |
| `database.py` | SQLAlchemy ORM models |
| `auth.py` | JWT authentication |
| `payments.py` | Stripe payment integration |
| `alembic.ini` | Database migration config |
| `pyproject.toml` | Build config, dependencies, tool settings |
| `pytest.ini` | Test configuration and markers |

## Docker Architecture

Multi-stage Dockerfile with four stages:
1. **builder** - Compiles wheels from pyproject.toml
2. **production** - Base image with runtime deps, non-root user
3. **api** - API service (`uvicorn apps.api.main:app`)
4. **worker** - Worker service (`python -m apps.worker.main`)

Docker Compose services: `api` (port 8000), `worker`, `db` (PostgreSQL 15).

## Agent Framework (.kiro/)

### Available Agents

| Agent | Role |
|-------|------|
| orchestrator | Spec-driven workflow: Requirements -> Design -> Tasks -> Implementation |
| code-surgeon | Security review (OWASP), refactoring, performance optimization |
| test-architect | Unit/integration tests, coverage analysis, test data generation |
| db-wizard | Schema design, query optimization, migration strategies |
| frontend-designer | React components, Tailwind CSS, accessibility (WCAG 2.1 AA) |
| devops-automator | CI/CD, Docker, deployment automation |
| doc-smith | Documentation, README files, API docs |

### Spec-Driven Development

Feature specs live in `.kiro/specs/[feature-name]/` with three files:
- `requirements.md` - What to build and acceptance criteria
- `design.md` - Technical design and architecture decisions
- `tasks.md` - Implementation task breakdown

### Steering Documents

Project context and guidelines in `.kiro/steering/`:
- `project-overview.md`, `coding-standards.md`, `tech.md`
- Per-package guides: `seo-health-report.md`, `seo-technical-audit.md`, `ai-visibility-audit.md`, `seo-content-authority.md`
- Process guides: `github-workflow.md`, `planning.md`, `validation.md`

## Progress Tracking

- `docs/PROGRESS.md` - Current project status and sprint tracking
- `docs/PLAN.md` - Development roadmap
- `DEVLOG.md` - Development history log
- `HANDOFF.md` - Project transition notes
