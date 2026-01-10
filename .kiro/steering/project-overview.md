# SEO Health Report System - Project Overview

This is a comprehensive SEO audit system that generates branded health reports by orchestrating technical, content, and AI visibility audits.

## Key Differentiator

The **AI Visibility Audit** evaluates how brands appear in AI-generated responses (ChatGPT, Claude, Perplexity). This is the competitive moat—most SEO agencies don't offer this.

## Architecture

```
seo-health-report/           # Master orchestrator (30% weight)
├── ai-visibility-audit/     # AI system presence analysis (35% weight)
├── seo-technical-audit/     # Technical SEO analysis (30% weight)
└── seo-content-authority/   # Content & authority analysis (35% weight)
```

## Scoring Formula

```
Overall Score = (Technical × 0.30) + (Content × 0.35) + (AI × 0.35)
```

AI visibility is weighted higher because it's the differentiator.

## Grade Mapping

| Grade | Score | Status |
|-------|-------|--------|
| A | 90-100 | Excellent |
| B | 80-89 | Good |
| C | 70-79 | Needs Work |
| D | 60-69 | Poor |
| F | <60 | Critical |

## Required API Keys

- `ANTHROPIC_API_KEY` - Required for Claude queries
- `OPENAI_API_KEY` - Optional, expands ChatGPT coverage
- `PERPLEXITY_API_KEY` - Optional, expands Perplexity coverage
- `GOOGLE_API_KEY` - Optional, for PageSpeed Insights
