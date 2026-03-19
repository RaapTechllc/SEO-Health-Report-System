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

## Milestone 2: Eliminate Mock Data — Real Scores Only

The deep audit (see `docs/DEEP_AUDIT_FINDINGS.md`) found that **10.5% of the final score is fabricated**: backlink score hardcoded to 7/15, keyword position hardcoded to 7/15. This milestone replaces every placeholder with either real data or an honest "N/A — requires API key" marker. No customer should ever see a score computed from fake data.

### Deliverables

1. **`packages/seo_content_authority/scripts/score_backlinks.py`** — Replace the three API stubs (`analyze_with_ahrefs`, `analyze_with_moz`, `analyze_with_semrush`) with a real implementation using the Moz Link API (free tier: 10 rows/month, paid for volume). When no API key is configured, return `score: None` with a clear `"data_source": "unavailable"` marker instead of a neutral 7.

2. **`packages/seo_content_authority/__init__.py`** — Replace hardcoded `keyword_score = 7` with a real keyword ranking check using the DataForSEO SERP API (or Google Search Console API when credentials are available). When no ranking API key is present, return `score: None` with `"data_source": "unavailable"` instead of a neutral 7.

3. **`packages/seo_health_report/scripts/calculate_scores.py`** — Update composite score calculation to handle `None` sub-component scores within a pillar. When backlinks or keyword position returns `None`, redistribute their weight to the remaining real components within the Content & Authority pillar, and annotate the report with which components were unavailable.

4. **`packages/ai_visibility_audit/scripts/check_knowledge.py`** — Replace the Crunchbase stub with a real Crunchbase Basic API call. When no API key is present, return `score: None` instead of "not yet implemented" error.

5. **`packages/seo_technical_audit/scripts/crawl_site.py`** — Implement actual multi-page crawl using the `depth` parameter. Crawl up to `min(depth, 100)` pages following internal links from the homepage. Detect broken links (4xx/5xx responses), redirect chains, and duplicate content (same title/meta across different URLs).

6. **`packages/seo_technical_audit/scripts/check_mobile.py`** — Extend mobile checks to use Google PageSpeed API's mobile strategy (already available via `analyze_speed.py`) for tap target analysis, font size validation, and content-wider-than-screen detection. Add these as supplementary checks alongside the existing viewport meta tag check.

7. **Data source transparency** — Every component score dict must include a `"data_source"` field: `"real_api"`, `"heuristic"`, or `"unavailable"`. The report renderer uses this to show confidence indicators (solid bar vs hatched bar vs grayed out).

### Acceptance Criteria

- [ ] With Moz API key set: `score_backlinks.py` returns real domain authority, referring domains, and backlink count
- [ ] Without any backlink API key: backlinks component returns `score: None`, NOT 7
- [ ] With DataForSEO/GSC key: keyword position returns real SERP position data
- [ ] Without ranking API key: keyword position returns `score: None`, NOT 7
- [ ] `calculate_scores.py` correctly weights available components when some are `None`
- [ ] Crawl with `depth=10` visits at least 5 internal pages (when they exist)
- [ ] Broken links detected during crawl appear in issues list
- [ ] Every component score dict includes `data_source` field
- [ ] No hardcoded neutral scores (7, 5, etc.) remain in production paths
- [ ] `ruff check .` and `pytest tests/` pass with zero new failures

### Risks & Dependencies

- Moz Link API free tier is rate-limited (10 requests/month) — may need paid key for production volume.
- DataForSEO costs ~$0.002/SERP query — adds to per-audit cost (fits within tier pricing).
- Multi-page crawl increases audit time — need configurable page limit per tier (LOW: 10 pages, MEDIUM: 30, HIGH: 100).
- Sites with many 404s could slow crawl — need per-page timeout and max-errors-before-abort.

## Milestone 3: DFY/DWY/DIY Action Engine

Transform the report from a passive score card into an **action engine**. Every finding gets classified into one of three delivery tiers, each with concrete steps, effort estimates, and (for DFY) automated implementation capabilities.

### Action Tier Definitions

| Tier | Name | Description | Example |
|------|------|-------------|---------|
| **DFY** | Done-For-You | Automated fixes the system can apply or generate ready-to-deploy artifacts | Generate robots.txt, create meta tags, produce schema.org JSON-LD, generate optimized alt text |
| **DWY** | Done-With-You | Guided fixes with step-by-step instructions, code snippets, and validation criteria | "Add this exact `<link rel='canonical'>` tag to your homepage header" with before/after HTML |
| **DIY** | Do-It-Yourself | Strategic recommendations requiring human judgment or business decisions | "Develop 3 pillar content pieces targeting [keyword cluster]" with topic suggestions |

### Deliverables

1. **Action classification module** (`packages/seo_health_report/actions/classifier.py`) — Takes raw issues and recommendations from all three pillars and classifies each into DFY/DWY/DIY based on:
   - Can the fix be expressed as a code/config artifact? → DFY
   - Can the fix be expressed as exact instructions with copy-paste code? → DWY
   - Does the fix require content creation, business decisions, or external services? → DIY

2. **DFY artifact generators** (`packages/seo_health_report/actions/generators/`):
   - `robots_txt.py` — Generate optimized robots.txt based on crawl findings
   - `meta_tags.py` — Generate missing/improved meta title, description, og:tags
   - `schema_markup.py` — Generate JSON-LD structured data (Organization, LocalBusiness, FAQ, HowTo)
   - `htaccess_redirects.py` — Generate redirect rules for broken links and redirect chains
   - `sitemap.py` — Generate XML sitemap from crawl data
   - `alt_text.py` — Use AI to generate descriptive alt text for images missing it

3. **DWY instruction generator** (`packages/seo_health_report/actions/instructions.py`) — For each DWY item, produce:
   - Step-by-step instructions (numbered, with screenshots/code blocks)
   - Exact code snippets to copy-paste
   - "Before" and "After" comparison showing expected change
   - Validation check the user can run to confirm the fix worked
   - Estimated time to implement (in minutes)

4. **DIY strategy generator** (`packages/seo_health_report/actions/strategy.py`) — For each DIY item, use LLM to produce:
   - Why this matters (business impact explanation)
   - Recommended approach with 2-3 options
   - Resources and tools to help
   - Success criteria and KPIs to track
   - Priority relative to other DIY items

5. **Action summary in report** — Extend `generate_summary.py` to include action tier breakdown:
   - Count of DFY/DWY/DIY items
   - Estimated total time savings from DFY automation
   - "Quick start" section: top 3 DFY items that can be applied immediately
   - Download links for DFY artifacts (robots.txt, schema JSON, etc.)

6. **Action data model** (`packages/schemas/models.py`) — Add Pydantic models:
   ```python
   class ActionItem(BaseModel):
       id: str
       title: str
       tier: Literal["dfy", "dwy", "diy"]
       pillar: Literal["technical", "content", "ai_visibility"]
       severity: Literal["critical", "high", "medium", "low"]
       effort_minutes: Optional[int]
       impact: Literal["high", "medium", "low"]
       description: str
       artifact: Optional[str]  # For DFY: the generated fix
       instructions: Optional[list[str]]  # For DWY: step-by-step
       strategy: Optional[str]  # For DIY: strategic guidance
       validation: Optional[str]  # How to verify the fix worked
   ```

### Acceptance Criteria

- [ ] Every issue/recommendation from all 3 pillars gets classified as DFY, DWY, or DIY
- [ ] DFY items include downloadable/copy-pasteable artifacts (robots.txt, meta tags, schema JSON, etc.)
- [ ] DWY items include numbered step-by-step instructions with code snippets
- [ ] DIY items include LLM-generated strategic guidance with business impact context
- [ ] Report summary includes DFY/DWY/DIY breakdown with counts and effort estimates
- [ ] At least 5 DFY generators implemented (robots.txt, meta tags, schema, redirects, sitemap)
- [ ] Action items are ordered by impact-to-effort ratio (highest ROI first)
- [ ] `ActionItem` Pydantic model validates all action data
- [ ] Generated artifacts are syntactically valid (robots.txt parseable, JSON-LD validates against schema.org)

### Risks & Dependencies

- DFY artifact generation requires LLM calls for alt text and some schema markup — adds to per-audit cost.
- Generated artifacts must be clearly labeled as "suggested" — users need to review before deploying.
- Schema.org JSON-LD generation needs validation against Google's Rich Results Test expectations.
- DWY instructions must be CMS-agnostic (WordPress, Shopify, custom) or detect the CMS and customize.

## Milestone 4: LLM-Powered Reporting & Intelligence

Replace template-based summaries with AI-generated personalized analysis. Add competitive intelligence layer.

### Deliverables

1. **LLM executive summary** (`packages/seo_health_report/scripts/generate_summary.py`) — Replace the static grade-to-text mapping with a real LLM call that receives the full audit findings and generates:
   - Personalized narrative analyzing the specific strengths and weaknesses found
   - Industry-specific context (e.g., "For an e-commerce site, your product schema coverage is below average")
   - Competitive positioning insights when competitor data is available
   - Forward-looking strategy recommendations tied to the specific scores

2. **Competitive benchmark intelligence** — When competitor URLs are provided, generate a comparative analysis section showing where the prospect leads, trails, and has opportunity vs. each competitor across all three pillars.

3. **AI-powered content gap analysis** — Use LLM to analyze the topical authority findings and generate specific content recommendations: titles, outlines, target keywords, and estimated traffic potential.

4. **Trend analysis** — When historical audit data exists, generate trend narratives explaining what improved, what declined, and what caused the changes.

### Acceptance Criteria

- [ ] Executive summary is unique per audit (not template fill-in)
- [ ] LLM summary references specific findings by name (not generic advice)
- [ ] Competitive analysis shows per-pillar comparison when competitor data available
- [ ] Content gap analysis produces actionable topic/title suggestions
- [ ] LLM costs stay within tier budget (LOW: <$0.01/summary, HIGH: <$0.05/summary)
- [ ] Fallback to template-based summary if LLM call fails

### Risks & Dependencies

- LLM-generated summaries add latency (2-5s) and cost to each audit.
- Quality depends on prompt engineering — needs iteration and evaluation.
- Must not leak competitor data between different customers' audits.

## Milestone 5: Core Resilience & Production Readiness

Combines the original Milestones 2 and 3 into a single hardening pass. Circuit breakers, security, testing, deployment.

### Deliverables

1. **Input validation module** (`packages/core/validators.py`) — URL schema validation, company name sanitization, keyword normalization. Used by orchestrator, API, and CLI entry points.
2. **Circuit breaker for AI providers** (`packages/core/circuit_breaker.py`) — Per-provider circuit breaker (closed/open/half-open states) so a failing provider doesn't block the entire audit. Fallback to degraded scoring when a provider is unavailable.
3. **Configuration externalization** — Extract all hardcoded scoring weights, page limits, query counts, and sentiment keywords into `packages/config/audit_defaults.py` loaded from tier env files.
4. **Security audit fixes** — Address the 12 critical + 8 high vulnerabilities identified in `docs/PROGRESS.md` security review.
5. **Composite health endpoint** (`/health/deep`) — Checks DB connectivity, storage backend, and probes each AI provider with a lightweight ping.
6. **Test coverage improvement** — Target: 80% line coverage on `packages/` code.
7. **Production deployment verification** — Docker Compose smoke test that boots API + Worker + PostgreSQL, runs a hello audit, and validates report output.

### Acceptance Criteria

- [ ] Circuit breaker trips after 3 consecutive failures; recovers after 60s half-open probe
- [ ] Invalid URLs rejected at API and CLI layers with clear error messages
- [ ] Zero known SQL injection or path traversal vulnerabilities
- [ ] `/health/deep` returns structured JSON with per-dependency status
- [ ] `pytest --cov` reports >=80% line coverage on `packages/`
- [ ] `docker compose up && curl /health` returns 200 within 30s of container start
- [ ] All CI workflows pass on a clean checkout

### Risks & Dependencies

- Circuit breaker adds complexity to audit scoring — need clear degraded-mode scoring rules.
- Coverage target may require refactoring untestable code paths.
- Docker smoke test requires PostgreSQL to be healthy before API starts.
