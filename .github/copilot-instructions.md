# GitHub Copilot / AI Agent Instructions

Goal: help an AI coding agent become productive quickly in this repo by highlighting project structure, conventions, workflows, and concrete examples to act on.

---

## Quick orientation
- This repo contains three *self-contained audit skills*: `ai-visibility-audit/`, `seo-content-authority/`, and `seo-technical-audit/`. Each exposes a public entrypoint `run_audit(...)` from the package `__init__.py` (e.g., `from ai_visibility_audit import run_audit`). See each package `README.md` and `SKILL.md` for workflow and expected inputs/outputs.
- There is no top-level orchestrator included in this workspace; packages are designed to be called by an external orchestrator (`seo-health-report` is mentioned in READMEs). Do not assume orchestration logic exists unless added.

## How to run code during development
- Most code is intended to be imported and executed in Python, e.g.:
  ```py
  from ai_visibility_audit import run_audit
  results = run_audit(brand_name="Acme", target_url="https://acme.com", products_services=["widgets"])
  ```
- There are no CLI entrypoints or test harnesses present. For quick checks, create small ad-hoc scripts or a REPL session that imports `run_audit` and inspects returned dicts.
- Development dependencies (formatters, linters, pytest) are listed but commented in `requirements.txt` in each package. Use them if you add tests.

## Important environment variables & external services
- AI/API keys and other optional integration keys are read from environment variables. Key names used in the codebase include:
  - `ANTHROPIC_API_KEY` (required for Claude usage; `ai-visibility-audit` uses `anthropic` package)
  - `OPENAI_API_KEY` (optional; OpenAI integration is stubbed in places)
  - `PERPLEXITY_API_KEY` (stubbed/not implemented)
  - `PAGESPEED_API_KEY`, `AHREFS_API_KEY`, `MOZ_API_KEY`, `SEMRUSH_API_KEY` (optional for specific analyses)
- Note: many API integrations are unimplemented or partial (OpenAI/Perplexity are deliberately left as TODO stubs). Check `scripts/*` for `error` messages indicating missing integrations.

## Common patterns & conventions
- Entrypoints return structured dicts with consistent fields: `score`, `grade`, `components`, and `recommendations`. Example: `ai_visibility_audit.run_audit` returns keys `score`, `grade`, `components`, `ai_responses`, `accuracy_issues`, `recommendations`.
- Components use small integer weights (sum to 100). See each package README for exact weights (e.g., AI Presence=25, Accuracy=20, Parseability=15 in `ai-visibility-audit`).
- Recommendations are objects with a small, consistent schema: `{priority: "high|medium|low", category: string, action: string, details: string, impact: string, effort: string}`. Use and preserve this schema when adding automated recommendations.
- HTTP requests use a standardized User-Agent: `SEO-Health-Report-Bot/1.0` (scripts set this header in `requests.get`). Keep this header or update it consistently across scripts when changing.
- Error handling: when an external API or dependency is missing, many helper functions return structured error objects (e.g., `AIResponse.error` set). Code frequently checks `if response.error: continue`. Follow this pattern to avoid raising on missing optional integrations.
- Rate limiting: AI query runner uses a default `rate_limit_ms=1000` in `query_all_systems` — respect or make this configurable if adding parallelization.

## Files to consult first (high priority)
- `*/SKILL.md` (each package) — quick description, inputs, workflow. Start here to understand intended behavior.
- `*/README.md` — details on scoring rubrics, install, examples, and output schema.
- `*/__init__.py` — canonical `run_audit` definition and how components are composed.
- `*/scripts/*.py` — functional code (crawl, analyze, query). Use these for implementation details.
- `*/references/*.md` — scoring rubrics and templates (useful when extending scoring logic).

## Implementation guidance for contributors (AI agents)
- Follow existing return structures and field names exactly (tests and orchestrators expect consistent keys). Add new keys only with explicit justification and update `README.md` + `SKILL.md` accordingly.
- When implementing new integrations: return the same structured objects used by peers (e.g., for AI responses return `AIResponse` dataclass or equivalent dict with `error` field when failing). Add graceful fallbacks for absent API keys.
- Prefer small, well-scoped PRs that include updates to `SKILL.md` and package `README.md` when changing semantics or adding outputs.
- Add unit tests under a `tests/` folder if adding logic complexity — the project currently does not contain tests, but dev requirements list `pytest` as optional.

## Prominent code examples to reference
- Querying Claude: `ai-visibility-audit/scripts/query_ai_systems.py` — uses `anthropic` and model `claude-sonnet-4-20250514` and returns `AIResponse` dataclass. Missing key -> `error: "ANTHROPIC_API_KEY not set"`.
- Fetching pages: `seo-technical-audit/scripts/crawl_site.py` -> `fetch_url` sets header `User-Agent: SEO-Health-Report-Bot/1.0` and returns text or None on error.
- Scoring & recommendations: each `__init__.py` builds `components` dicts with `score`/`max` and uses `generate_recommendations` functions; prefer modifying those to change thresholds or add rules.

## What not to assume
- Do not assume an orchestrator or CI/test infra exists in the repo — both are referenced but not included.
- Do not assume all external APIs are implemented; check for `TODO` and `error` returns in scripts before invoking them.

---

If you'd like, I can:
1. Add a minimal `scripts/run_example.py` demonstrating how to import and run each `run_audit` and write results to `./reports/` (handy for manual testing).
2. Add a basic `tests/` skeleton with a few unit tests for pure functions (scoring, parsing) and a GitHub Actions workflow to run them.

Please tell me which of the two (example runner or test skeleton) you'd like me to add first, or suggest changes to this instruction draft.