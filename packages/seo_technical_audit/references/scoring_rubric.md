# Technical SEO Scoring Rubric

## Total Score: 100 points

| Component | Max Points | Weight |
|-----------|------------|--------|
| Crawlability | 20 | 20% |
| Indexing | 15 | 15% |
| Speed | 25 | 25% |
| Mobile | 15 | 15% |
| Security | 10 | 10% |
| Structured Data | 15 | 15% |

---

## Crawlability (20 points)

### robots.txt (8 points)

| Score | Criteria |
|-------|----------|
| 8 | Valid robots.txt, proper Allow/Disallow, sitemap declared |
| 6 | Minor issues (missing sitemap declaration) |
| 4 | Moderate issues (blocking important resources) |
| 2 | Major issues (overly restrictive rules) |
| 0 | Critical: Entire site blocked or no robots.txt |

### Redirect Analysis (6 points)

| Score | Criteria |
|-------|----------|
| 6 | No redirect chains, all 301s |
| 4 | Chains ≤2 hops, occasional 302s |
| 2 | Chains 3-4 hops |
| 0 | Redirect loops or chains >4 hops |

### Meta Robots & Canonicals (6 points)

| Score | Criteria |
|-------|----------|
| 6 | Proper meta robots, self-referencing canonicals |
| 4 | Minor canonical issues |
| 2 | Missing canonicals, some noindex issues |
| 0 | Widespread noindex or conflicting signals |

---

## Indexing (15 points)

### XML Sitemap (8 points)

| Score | Criteria |
|-------|----------|
| 8 | Valid sitemap, all URLs accessible, <50k URLs per file |
| 6 | Valid sitemap with minor issues |
| 4 | Sitemap exists but has errors |
| 2 | Sitemap missing but indexing works |
| 0 | No sitemap and indexing issues |

### Page Indexability (7 points)

| Score | Criteria |
|-------|----------|
| 7 | All important pages indexable |
| 5 | Minor noindex issues on low-priority pages |
| 3 | Some important pages blocked |
| 0 | Critical content not indexable |

---

## Speed (25 points)

### Core Web Vitals (15 points)

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | <2.5s (+5) | 2.5-4s (+3) | >4s (+0) |
| FID | <100ms (+5) | 100-300ms (+3) | >300ms (+0) |
| CLS | <0.1 (+5) | 0.1-0.25 (+3) | >0.25 (+0) |

### PageSpeed Score (10 points)

| Score | PSI Score |
|-------|-----------|
| 10 | 90-100 |
| 8 | 75-89 |
| 6 | 50-74 |
| 4 | 25-49 |
| 2 | 0-24 |

---

## Mobile (15 points)

### Mobile PageSpeed (8 points)

| Score | Mobile PSI |
|-------|------------|
| 8 | 90-100 |
| 6 | 75-89 |
| 4 | 50-74 |
| 2 | 25-49 |
| 0 | 0-24 |

### Mobile Usability (7 points)

| Score | Criteria |
|-------|----------|
| 7 | Fully responsive, no usability errors |
| 5 | Minor issues (small touch targets) |
| 3 | Moderate issues (horizontal scroll, small text) |
| 1 | Major mobile usability problems |
| 0 | Not mobile-friendly |

---

## Security (10 points)

### HTTPS (5 points)

| Score | Criteria |
|-------|----------|
| 5 | HTTPS everywhere, valid cert, HTTP redirects |
| 3 | HTTPS but missing redirects |
| 1 | HTTPS with certificate issues |
| 0 | No HTTPS |

### Security Headers (5 points)

| Score | Headers Present |
|-------|-----------------|
| 5 | HSTS + CSP + X-Frame-Options + X-Content-Type |
| 4 | HSTS + 2 others |
| 3 | HSTS + 1 other |
| 2 | HSTS only |
| 1 | Any security header |
| 0 | No security headers |

---

## Structured Data (15 points)

### Schema Presence (7 points)

| Score | Criteria |
|-------|----------|
| 7 | JSON-LD with multiple valid schemas |
| 5 | JSON-LD with basic schemas |
| 3 | Microdata or RDFa present |
| 1 | Minimal structured data |
| 0 | No structured data |

### Rich Results Eligibility (8 points)

| Score | Criteria |
|-------|----------|
| 8 | Eligible for 3+ rich result types |
| 6 | Eligible for 2 rich result types |
| 4 | Eligible for 1 rich result type |
| 2 | Potential eligibility with fixes |
| 0 | Not eligible for any rich results |

---

## Grade Mapping

| Score | Grade | Status |
|-------|-------|--------|
| 90-100 | A | Excellent technical health |
| 80-89 | B | Good, minor improvements needed |
| 70-79 | C | Fair, several issues to address |
| 60-69 | D | Poor, significant issues |
| <60 | F | Critical, requires immediate attention |

---

## Issue Severity Classification

### Critical (Immediate action required)
- Entire site blocked in robots.txt
- No HTTPS
- Site completely not indexable
- Redirect loops
- SSL certificate expired

### High (Fix within 1 week)
- Major content blocked
- Mixed content issues
- Missing sitemap
- Poor Core Web Vitals (all fail)
- Noindex on important pages

### Medium (Fix within 1 month)
- Minor crawl issues
- Missing security headers
- Some CWV need improvement
- Incomplete structured data

### Low (Nice to have)
- Optimization opportunities
- Missing recommended schema properties
- Minor redirect chains
- Crawl-delay directives
