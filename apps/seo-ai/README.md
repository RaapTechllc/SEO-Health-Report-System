# Rankwise — AI-Age SEO Audit

A self-contained web app that audits any website for **AI-age search visibility**: it scores
traditional technical SEO and content quality alongside how well a page is positioned to be
surfaced and cited by AI answer engines (ChatGPT, Claude, Perplexity, Gemini).

Enter a URL → the app fetches and analyzes the page server-side → you get a weighted score, a
per-pillar breakdown with individual checks, an executive summary, and prioritized,
actionable recommendations.

## Scoring model

```
Overall = Technical × 0.30  +  Content & Authority × 0.35  +  AI Visibility × 0.35
```

| Pillar | Weight | What it measures |
|--------|--------|------------------|
| **Technical SEO** | 30% | HTTPS, status, title/meta, single H1, canonical, robots, sitemap, viewport, structured data |
| **Content & Authority** | 35% | Content depth, heading structure, readability, keyword/title alignment, internal links, image alt coverage, metadata richness |
| **AI Visibility** | 35% | Structured-data/entity clarity, answer-friendly formatting, citability signals — graded by Claude when configured, or a deterministic heuristic otherwise |

## Tech stack

- **Next.js 15** (App Router) + **React 19** + **TypeScript** (strict)
- **Tailwind CSS** for the UI
- **@anthropic-ai/sdk** for AI-visibility analysis (optional)
- Dependency-free HTML parsing; server-side fetch with a hostname SSRF guard and optional egress-proxy support

## Architecture

```
apps/seo-ai/
├── app/
│   ├── page.tsx              # landing + audit form
│   ├── layout.tsx
│   └── api/audit/route.ts    # POST /api/audit { url } -> AuditResult
├── components/               # AuditForm, ReportView, ScoreGauge, PillarCard, Recommendations
├── lib/
│   ├── types.ts              # shared contracts (the single source of truth)
│   ├── utils.ts              # grading + scoring helpers
│   ├── ai/anthropic.ts       # Claude client (JSON mode) with graceful absence
│   └── audit/
│       ├── fetchPage.ts      # SSRF-guarded fetch + HTML → PageData parser
│       ├── technical.ts      # analyzeTechnical(page) -> PillarScore
│       ├── content.ts        # analyzeContent(page) -> PillarScore
│       ├── aiVisibility.ts   # analyzeAiVisibility(page) -> AiVisibilityResult
│       └── runAudit.ts       # orchestrates the full pipeline
└── scripts/smoke.ts          # offline pipeline check (no network needed)
```

## Run it

```bash
cd apps/seo-ai
npm install
cp .env.example .env        # optional — see below
npm run dev                 # http://localhost:3000
```

Production build:

```bash
npm run build && npm start
```

### Optional: live AI analysis

The app runs fully **without any API key** — AI-visibility analysis falls back to a deterministic
heuristic over the page's structure. To use live Claude analysis, set:

```bash
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6   # default
```

## Verify

```bash
npm run typecheck   # tsc --noEmit
npm run build       # full production build
npm run smoke       # offline analysis check against HTML fixtures (no network)
```

`npm run smoke` exercises the parser, all three analyzers, the heuristic AI-visibility path, and
the weighted scoring against an optimized fixture and a thin one, demonstrating that scores
discriminate correctly without needing outbound network access.

## API

`POST /api/audit` with `{ "url": "https://example.com" }` returns an `AuditResult` (see
`lib/types.ts`): overall score + grade, three `PillarScore` objects with individual checks, a
ranked `Recommendation[]`, and an executive `aiSummary`.

## Notes

- **Egress:** auditing arbitrary external URLs requires outbound network access. In environments
  behind an HTTP egress proxy, set `HTTPS_PROXY` (and `NODE_EXTRA_CA_CERTS` if the proxy
  re-terminates TLS) — `fetchPage` wires up an undici proxy dispatcher automatically.
- **SSRF:** requests to localhost / private (RFC1918) / link-local hosts are refused.
