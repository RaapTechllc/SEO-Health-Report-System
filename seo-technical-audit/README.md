# SEO Technical Audit

Comprehensive technical SEO analysis covering crawlability, page speed, mobile optimization, security, and structured data.

## Overview

This audit evaluates the technical foundation of a website's SEO health. Technical issues can prevent search engines from properly crawling, indexing, and ranking your content.

## Installation

```bash
cd seo-technical-audit
pip install -r requirements.txt
```

### API Keys (Optional)

| Service | Environment Variable | Purpose |
|---------|---------------------|---------|
| PageSpeed Insights | `PAGESPEED_API_KEY` | Faster rate limits, more data |
| SSL Labs | N/A | Free, no key needed |

The audit works without API keys but may be rate-limited.

## Quick Start

```python
from seo_technical_audit import run_audit

results = run_audit(
    target_url="https://example.com",
    depth=50,
    competitor_urls=["https://competitor1.com", "https://competitor2.com"]
)

print(f"Technical Score: {results['score']}/100 ({results['grade']})")
```

## Scoring Breakdown (100 points)

### Crawlability (20 points)

Can search engines access and navigate your site?

| Score | Criteria |
|-------|----------|
| 20 | Clean robots.txt, no blocked resources, proper canonicals |
| 15-19 | Minor issues (some blocked resources, redirect chains <3) |
| 10-14 | Moderate issues affecting crawl efficiency |
| 5-9 | Significant crawl barriers |
| 0-4 | Critical: Major content blocked or inaccessible |

**Checks performed:**
- robots.txt accessibility and syntax
- Disallow rules analysis
- Crawl-delay directives
- Meta robots tags
- X-Robots-Tag headers
- Canonical tag implementation
- Redirect chain length
- Internal link structure

### Indexing (15 points)

Are your pages properly indexed?

| Score | Criteria |
|-------|----------|
| 15 | Valid sitemap, all pages indexable, no duplicates |
| 12-14 | Minor indexing issues |
| 8-11 | Some pages blocked or duplicate |
| 4-7 | Significant indexing problems |
| 0-3 | Critical: Site not indexable |

**Checks performed:**
- XML sitemap presence and validity
- Sitemap URLs vs actual pages
- Noindex tag usage
- Duplicate content signals
- Hreflang implementation
- Pagination handling

### Speed (25 points)

How fast do your pages load?

| Score | Criteria |
|-------|----------|
| 25 | All Core Web Vitals pass |
| 20-24 | Good performance, minor issues |
| 15-19 | Needs improvement on some metrics |
| 10-14 | Poor performance |
| 0-9 | Critical: Very slow site |

**Core Web Vitals measured:**
- **LCP** (Largest Contentful Paint): <2.5s good, >4s poor
- **FID** (First Input Delay): <100ms good, >300ms poor
- **CLS** (Cumulative Layout Shift): <0.1 good, >0.25 poor
- **TTFB** (Time to First Byte): <800ms good, >1800ms poor

### Mobile (15 points)

Is your site mobile-friendly?

| Score | Criteria |
|-------|----------|
| 15 | Fully responsive, no mobile issues |
| 12-14 | Minor mobile issues |
| 8-11 | Some usability problems on mobile |
| 4-7 | Significant mobile issues |
| 0-3 | Not mobile-friendly |

**Checks performed:**
- Viewport meta tag
- Responsive design detection
- Touch target sizing
- Font sizing
- Content width vs viewport
- Mobile page speed

### Security (10 points)

Is your site secure?

| Score | Criteria |
|-------|----------|
| 10 | HTTPS everywhere, all security headers, no mixed content |
| 8-9 | HTTPS with minor header issues |
| 5-7 | HTTPS but missing important headers |
| 2-4 | HTTPS with significant security gaps |
| 0-1 | No HTTPS or critical security issues |

**Checks performed:**
- HTTPS implementation
- SSL certificate validity
- HSTS header
- Content-Security-Policy
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy
- Mixed content warnings

### Structured Data (15 points)

Do you have proper schema markup?

| Score | Criteria |
|-------|----------|
| 15 | Multiple valid schemas, rich result eligible |
| 12-14 | Valid schemas with minor issues |
| 8-11 | Some schemas, validation warnings |
| 4-7 | Minimal or invalid schemas |
| 0-3 | No structured data |

**Checks performed:**
- JSON-LD, Microdata, RDFa presence
- Schema validation
- Required property coverage
- Rich result eligibility
- Schema types coverage

## Issue Severity Levels

| Level | Definition | Point Deduction |
|-------|------------|-----------------|
| Critical | Blocks indexing or breaks site | -10 to -15 |
| High | Significant negative impact | -5 to -10 |
| Medium | Moderate impact, should fix | -2 to -5 |
| Low | Minor impact, nice to fix | -1 to -2 |

## Directory Structure

```
seo-technical-audit/
├── SKILL.md              # Claude Code skill definition
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── __init__.py          # Package init with run_audit()
├── scripts/
│   ├── __init__.py
│   ├── crawl_site.py        # Robots, sitemap, crawl analysis
│   ├── analyze_speed.py     # PageSpeed Insights wrapper
│   ├── check_security.py    # HTTPS, headers analysis
│   └── validate_schema.py   # Structured data validation
├── references/
│   ├── scoring_rubric.md    # Point allocation details
│   ├── issue_severity.md    # Severity definitions
│   └── fix_templates.md     # Standard recommendations
└── assets/
    └── section_template.md  # Report section format
```

## Output Format

```json
{
  "score": 73,
  "grade": "C",
  "url": "https://example.com",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "crawlability": {
      "score": 18,
      "max": 20,
      "status": "good",
      "issues": [
        {
          "severity": "low",
          "description": "Redirect chain of 2 hops on /old-page",
          "recommendation": "Update link to point directly to final URL"
        }
      ]
    },
    "indexing": { ... },
    "speed": { ... },
    "mobile": { ... },
    "security": { ... },
    "structured_data": { ... }
  },
  "critical_issues": [
    {
      "component": "security",
      "description": "Missing HTTPS",
      "impact": "Site marked as 'Not Secure' in browsers"
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "security",
      "action": "Implement HTTPS",
      "details": "Install SSL certificate and redirect HTTP to HTTPS",
      "impact": "high",
      "effort": "medium"
    }
  ]
}
```

## Integration

This skill integrates with the `seo-health-report` orchestrator:

```python
# Called by orchestrator
from seo_technical_audit import run_audit

technical_data = run_audit(
    target_url=inputs['target_url'],
    depth=50
)

# technical_data contributes 30% to overall SEO Health Score
```

## Competitor Comparison

When competitor URLs are provided:

```python
results = run_audit(
    target_url="https://yoursite.com",
    competitor_urls=[
        "https://competitor1.com",
        "https://competitor2.com"
    ]
)

# Results include comparison data
print(results['competitor_comparison'])
```

Comparison output:
```json
{
  "competitor_comparison": {
    "your_score": 73,
    "competitor_scores": {
      "competitor1.com": 81,
      "competitor2.com": 68
    },
    "component_comparison": {
      "speed": {
        "yoursite.com": 15,
        "competitor1.com": 22,
        "competitor2.com": 12
      }
    }
  }
}
```
