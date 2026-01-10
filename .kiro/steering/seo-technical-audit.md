---
inclusion: fileMatch
fileMatchPattern: "seo-technical-audit/**"
---

# SEO Technical Audit Guidelines

Foundation audit for crawlability, speed, security, and structured data.

## Components (100 points total)

| Component | Points | Purpose |
|-----------|--------|---------|
| Crawlability | 20 | robots.txt, meta robots, canonicals, redirects |
| Indexing | 15 | Sitemap validity, noindex tags, duplicates |
| Speed | 25 | LCP, FID, CLS, TTFB, resource optimization |
| Mobile | 15 | Viewport, touch targets, font sizing, responsive |
| Security | 10 | HTTPS, HSTS, security headers, mixed content |
| Structured Data | 15 | Schema coverage, validation, rich results |

## Key Scripts

- `crawl_site.py` - Site crawling, robots/sitemap analysis
- `analyze_speed.py` - PageSpeed Insights, Core Web Vitals
- `check_security.py` - HTTPS, headers, security analysis
- `validate_schema.py` - Structured data validation

## Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | ≤2.5s | 2.5-4s | >4s |
| FID | ≤100ms | 100-300ms | >300ms |
| CLS | ≤0.1 | 0.1-0.25 | >0.25 |

## When Modifying

- Use Google PageSpeed API when `GOOGLE_API_KEY` is available
- Fall back to basic checks when API unavailable
- Keep scoring weights consistent with SKILL.md
