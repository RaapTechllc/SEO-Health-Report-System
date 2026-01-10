---
name: seo-technical-audit
description: Audit website technical SEO health. Use when checking crawlability, Core Web Vitals, structured data, mobile optimization, security headers, or indexing issues. Outputs Technical Health Score (0-100) with prioritized fixes.
---

# SEO Technical Audit

Evaluate crawlability, speed, security, mobile-readiness, and structured data.

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| target_url | Yes | Root domain to audit |
| competitor_urls | No | Up to 3 competitors for comparison |
| depth | No | Pages to crawl (default: 50) |

## Workflow

```
1. Validate target URL and check accessibility
2. Crawl site structure (robots.txt, sitemap)
3. Analyze crawlability issues
4. Check page speed (Core Web Vitals)
5. Verify mobile optimization
6. Audit security configuration
7. Validate structured data
8. Calculate composite score
9. Generate prioritized recommendations
```

## Audit Components (100 points)

| Component | Weight | What's Checked |
|-----------|--------|----------------|
| Crawlability | 20 | robots.txt, meta robots, canonical tags, redirect chains |
| Indexing | 15 | Sitemap validity, noindex tags, duplicate content signals |
| Speed | 25 | LCP, FID, CLS, TTFB, resource optimization |
| Mobile | 15 | Viewport config, touch targets, font sizing, responsive |
| Security | 10 | HTTPS, HSTS, security headers, mixed content |
| Structured Data | 15 | Schema coverage, validation errors, rich result eligibility |

## Running the Audit

### Step 1: Check Crawlability
```python
from scripts.crawl_site import check_robots, check_sitemaps, analyze_crawlability

robots = check_robots(target_url)
sitemaps = check_sitemaps(target_url)
crawl_score = analyze_crawlability(target_url, depth=50)
```

### Step 2: Analyze Speed
```python
from scripts.analyze_speed import get_pagespeed_insights, analyze_core_web_vitals

psi_data = get_pagespeed_insights(target_url)
cwv_score = analyze_core_web_vitals(psi_data)
```

### Step 3: Check Security
```python
from scripts.check_security import analyze_security

security_score = analyze_security(target_url)
```

### Step 4: Validate Structured Data
```python
from scripts.validate_schema import validate_structured_data

schema_score = validate_structured_data(target_url)
```

## Output Schema

```json
{
  "score": 73,
  "grade": "C",
  "components": {
    "crawlability": {"score": 18, "max": 20, "issues": []},
    "indexing": {"score": 12, "max": 15, "issues": []},
    "speed": {"score": 15, "max": 25, "issues": []},
    "mobile": {"score": 14, "max": 15, "issues": []},
    "security": {"score": 8, "max": 10, "issues": []},
    "structured_data": {"score": 6, "max": 15, "issues": []}
  },
  "critical_issues": [],
  "recommendations": []
}
```

## Key Files

- `scripts/crawl_site.py` - Site crawling and robots/sitemap analysis
- `scripts/analyze_speed.py` - PageSpeed Insights and Core Web Vitals
- `scripts/check_security.py` - HTTPS, headers, and security analysis
- `scripts/validate_schema.py` - Structured data validation
- `references/scoring_rubric.md` - Detailed scoring criteria
- `references/issue_severity.md` - Issue classification guide
- `references/fix_templates.md` - Standard fix recommendations
