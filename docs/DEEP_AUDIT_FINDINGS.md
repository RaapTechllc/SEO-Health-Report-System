# Deep Audit: Mock Data & Production Readiness Findings

**Date:** 2026-02-11
**Scope:** Full data-path trace across all three audit pillars + orchestration layer
**Goal:** Verify every score comes from real data; identify all mock/stub/placeholder paths

---

## Executive Summary

The system's scoring pipeline is **partially real**. Technical SEO and AI Visibility pillars
make genuine external API calls and produce authentic scores. However, the Content & Authority
pillar has **two critical placeholder scores** that inflate or mask true results, and the
executive summary generation is template-based rather than LLM-powered. Additionally, the
technical crawl ignores its `depth` parameter (homepage-only), limiting the value of the
technical audit.

### Severity Matrix

| Issue | Pillar | Impact | Severity |
|-------|--------|--------|----------|
| Backlink score hardcoded to 7/15 | Content | 15% of pillar score is fiction | **CRITICAL** |
| Keyword position hardcoded to 7/15 | Content | 15% of pillar score is fiction | **CRITICAL** |
| Crunchbase check is stub | AI Visibility | Minor (1pt of 15pt component) | LOW |
| Crawl depth ignored (homepage only) | Technical | Misses multi-page issues | HIGH |
| Mobile check viewport-only | Technical | Misses tap targets, responsive issues | MEDIUM |
| Executive summary template-based | Reporting | Generic, not personalized by LLM | MEDIUM |

---

## Pillar-by-Pillar Findings

### 1. Technical SEO (30% weight) — MOSTLY REAL

**Real data sources:**
- `crawl_site.py`: HTTP GET for robots.txt, sitemaps, page HTML (real requests)
- `analyze_speed.py`: Google PageSpeed API (real, requires GOOGLE_API_KEY)
- `check_security.py`: Real header analysis (HSTS, CSP, X-Frame-Options)
- `check_mobile.py`: Real HTML parsing for viewport meta tag

**Issues found:**
- **`crawl_site.py` depth parameter IGNORED** — The function accepts `depth=50` but only
  fetches the homepage. A full site crawl (checking robots.txt compliance across pages,
  finding broken links, detecting duplicate content) is not implemented. The `broken_links`
  field is always `[]` with comment `# Would need actual checking`.
- **`check_mobile.py` only checks viewport meta tag** — Does not verify tap target sizes,
  responsive breakpoints, font scaling, or horizontal scrolling. A comment in the code
  acknowledges: "Tap targets are usually best checked via dynamic analysis (Lighthouse)."

**What competitors check that we don't:**
- Full multi-page crawl (site-wide broken links, redirect chains, canonical conflicts)
- HTTP/2 and HTTP/3 support detection
- Image optimization (compression, lazy loading, WebP/AVIF)
- Core Web Vitals history (CLS, LCP, FID/INP over time)
- Structured data validation (JSON-LD schema errors)
- Accessibility basics (alt text, ARIA labels)
- CDN detection and cache header analysis
- International SEO (hreflang, language alternates)

### 2. Content & Authority (35% weight) — PARTIALLY MOCK

**Real data sources (4 of 6 components):**
- Content Quality (25pts): Fetches real pages, analyzes word count, readability, media
- E-E-A-T Signals (20pts): Real pattern matching (author pages, about pages, credentials)
- Topical Authority (15pts): Real crawl of up to 30 pages for topic coverage analysis
- Internal Links (10pts): Real crawl analyzing link structure

**MOCK data sources (2 of 6 components):**

#### Backlink Quality — ENTIRELY STUB (15pts max)
- `score_backlinks.py` has three API integration functions that are **stubs**:
  - `analyze_with_ahrefs()` → returns error "Contact RaapTech for setup"
  - `analyze_with_moz()` → returns error "Contact RaapTech for setup"
  - `analyze_with_semrush()` → returns error "Contact RaapTech for setup"
- Without API key: returns hardcoded `score = 7` (neutral)
- Fallback `estimate_backlink_health()` fetches the page and looks for text signals
  like "featured in", "award", "partner" → adjusts score to 5-10 range
- **Net effect:** Every audit gets backlink score of 5-10 regardless of actual link profile.
  A site with 10,000 quality backlinks scores the same as a brand-new site.

#### Keyword Position — HARDCODED (15pts max)
- `__init__.py` line 129: `keyword_score = 7` with comment `# Requires ranking API`
- No external ranking API is integrated (no Google Search Console, no Ahrefs, no SEMrush)
- **Net effect:** Every audit gets keyword score of 7/15 regardless of actual rankings.
  A #1-ranking site scores the same as a site on page 50.

**Quantified impact:** These two stubs represent **30 of 100 points** in the Content &
Authority pillar, which itself carries **35% weight** in the overall score. That means
**10.5% of the final score is fabricated data**.

### 3. AI Visibility (35% weight) — REAL (with one minor stub)

**Real data sources:**
- `query_ai_systems.py`: Makes real API calls to Claude, ChatGPT, Perplexity, Grok, Gemini
- `analyze_responses.py`: Real NLP analysis of AI responses for brand mentions
- `check_knowledge.py`:
  - Google Knowledge Graph API (real, with GOOGLE_API_KEY)
  - Wikipedia API (real, always available)
  - Wikidata API (real, always available)
  - LinkedIn company check (real HTTP request)
- `aeo_engine.py`: Real scoring based on actual AI system responses

**One stub:**
- Crunchbase check in `check_knowledge.py` returns "not yet implemented" — but this is
  only 1 point of a 15-point component, so impact is minimal.

**Graceful degradation:** When API keys are missing, providers return empty responses with
error messages. Scores reflect the absence (typically 0 for that provider) rather than
fabricating success.

### 4. Orchestration & Reporting

**Real:**
- Score calculation in `calculate_scores.py`: Proper weighted aggregation with normalization
- Three-pillar parallel execution via `asyncio.gather()`
- Component failure isolation (one pillar failing doesn't crash the others)
- Tier-based model selection (LOW/MEDIUM/HIGH config files)

**Template-based (not mock, but not LLM-powered):**
- `generate_summary.py`: Executive summaries use string templates keyed to grade (A-F)
- No AI-generated personalized analysis of specific findings
- Headlines, interpretations, and recommendations are generic fill-in-the-blank

---

## API Integration Status

| API | Module | Status | Effort to Integrate |
|-----|--------|--------|---------------------|
| Google PageSpeed | analyze_speed.py | REAL | — |
| Google Knowledge Graph | check_knowledge.py | REAL | — |
| Wikipedia | check_knowledge.py | REAL | — |
| Wikidata | check_knowledge.py | REAL | — |
| LinkedIn | check_knowledge.py | REAL | — |
| Anthropic Claude | query_ai_systems.py | REAL | — |
| OpenAI ChatGPT | query_ai_systems.py | REAL | — |
| Perplexity | query_ai_systems.py | REAL | — |
| xAI Grok | query_ai_systems.py | REAL | — |
| Google Gemini | query_ai_systems.py | REAL | — |
| **Ahrefs** | score_backlinks.py | **STUB** | Medium (API docs available) |
| **Moz** | score_backlinks.py | **STUB** | Medium (API docs available) |
| **SEMrush** | score_backlinks.py | **STUB** | Medium (API docs available) |
| **Google Search Console** | (not implemented) | **MISSING** | Medium |
| **Crunchbase** | check_knowledge.py | **STUB** | Low |

---

## Recommendations

### Priority 1 — Eliminate Fake Scores (CRITICAL)
1. Replace backlink stub with real API integration (Moz Link API is most cost-effective)
2. Replace keyword position hardcode with Google Search Console or DataForSEO API
3. Mark unavailable components as "N/A — API key required" rather than returning neutral scores

### Priority 2 — Expand Audit Depth (HIGH)
4. Implement multi-page crawl using the existing `depth` parameter
5. Add broken link detection during crawl
6. Expand mobile testing with Lighthouse/PageSpeed mobile data

### Priority 3 — LLM-Powered Reporting (MEDIUM)
7. Replace template-based executive summary with LLM-generated analysis
8. Generate personalized recommendations using AI analysis of specific findings
9. Create DFY/DWY/DIY action classification for every recommendation

### Priority 4 — Industry Feature Parity (ENHANCEMENT)
10. Core Web Vitals tracking
11. Structured data validation
12. International SEO checks
13. Image optimization analysis
14. Accessibility basics
