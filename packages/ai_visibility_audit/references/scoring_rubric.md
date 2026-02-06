# AI Visibility Audit Scoring Rubric

## Total Score: 100 points

| Component | Max Points | Weight |
|-----------|------------|--------|
| AI Search Presence | 25 | 25% |
| Response Accuracy | 20 | 20% |
| LLM Parseability | 15 | 15% |
| Knowledge Graph | 15 | 15% |
| Citation Likelihood | 15 | 15% |
| Sentiment | 10 | 10% |

---

## AI Search Presence (25 points)

**What it measures:** Does the brand appear when AI systems answer relevant queries?

### Scoring Criteria

| Score | Mention Rate | Position | Description |
|-------|-------------|----------|-------------|
| 25 | 80%+ | Often first | Brand is a go-to reference for AI |
| 20-24 | 60-80% | Sometimes first | Strong presence, room for improvement |
| 15-19 | 40-60% | Rarely first | Moderate presence |
| 10-14 | 20-40% | Never first | Weak presence |
| 5-9 | <20% | N/A | Rarely mentioned |
| 0-4 | 0% | N/A | Unknown to AI systems |

### Bonus Points
- +2 if brand is mentioned in first 25% of response in >50% of cases

### Query Categories Tested
1. **Brand queries** (direct): "What is [brand]?"
2. **Product queries** (category): "Best [product type]"
3. **Problem queries** (intent): "How to solve [problem]"
4. **Comparison queries** (competitive): "[brand] vs [competitor]"
5. **Reputation queries** (sentiment): "[brand] reviews"

---

## Response Accuracy (20 points)

**What it measures:** When AI mentions the brand, is the information correct?

### Scoring Criteria

| Score | Accuracy | Description |
|-------|----------|-------------|
| 20 | 100% | All verifiable claims accurate |
| 15-19 | 90-99% | Minor inaccuracies (dates, details) |
| 10-14 | 75-90% | Some outdated information |
| 5-9 | 50-75% | Significant inaccuracies |
| 0-4 | <50% | Major errors or hallucinations |

### Severity Deductions

| Severity | Deduction | Examples |
|----------|-----------|----------|
| Critical | -5 | Wrong company identity, major hallucination |
| High | -3 | Wrong founder, incorrect founding year |
| Medium | -1 | Outdated pricing, old product names |
| Low | -0.5 | Minor date discrepancies |

### Facts Verified
- Company name and description
- Founding year and founders
- Headquarters location
- Key products/services
- Recent news or changes

---

## LLM Parseability (15 points)

**What it measures:** Can AI systems easily extract information from the website?

### Scoring Components

| Component | Max | Criteria |
|-----------|-----|----------|
| Semantic HTML | 6 | Uses <main>, <article>, <section>, etc. |
| Content Extraction | 5 | Text/HTML ratio, meta tags, alt text |
| JS Independence | 4 | Content renders without JavaScript |

### Semantic HTML Scoring

| Score | Criteria |
|-------|----------|
| 6 | 5+ semantic elements, proper heading hierarchy |
| 4-5 | 3-4 semantic elements, single H1 |
| 2-3 | 1-2 semantic elements |
| 0-1 | No semantic HTML, div soup |

### Structured Data Bonus
- +2 for JSON-LD schema
- +1 for microdata or RDFa
- +2 for key schemas (Organization, Product, FAQ)

### JS Dependency Penalties
- -3 for JS-only rendering (no SSR)
- -1 for limited server-rendered content

---

## Knowledge Graph Presence (15 points)

**What it measures:** Is the brand in authoritative knowledge sources?

### Scoring by Source

| Source | Points | Importance |
|--------|--------|------------|
| Wikipedia | 6 | Critical - feeds multiple AI systems |
| Google Knowledge Graph | 6 | Critical - powers Google AI |
| Wikidata | 2 | Important - structured data source |
| Crunchbase | 1 | Useful - business context |

### Total Score Calculation

| Score | Presence |
|-------|----------|
| 15 | Wikipedia + Google KG + Wikidata + others |
| 12 | Wikipedia + Google KG |
| 9 | Wikipedia OR Google KG only |
| 6 | Wikidata or industry databases |
| 3 | Minimal presence |
| 0 | Not in any knowledge graphs |

---

## Citation Likelihood (15 points)

**What it measures:** Does the site have content AI would want to cite?

### Content Type Scoring

| Content Type | Points | Examples |
|--------------|--------|----------|
| Original Research | 4-5 | Surveys, studies, proprietary data |
| Statistics | 3-4 | Industry stats, trend data |
| Comprehensive Guide | 3 | 3000+ word definitive guides |
| Interactive Tool | 4 | Calculators, checkers, generators |
| Case Study | 4 | Real-world success stories |
| Expert Content | 3 | Credentialed author content |
| Unique Perspective | 3 | Contrarian or original viewpoints |

### Score Calculation
- Sum points for all content types found
- Cap at 15 points
- Minimum 2 points for having a website

### High-Value Content Indicators
- Original data or research findings
- Specific statistics with sources
- Proprietary methodologies
- First-hand case studies
- Expert credentials visible

---

## Sentiment (10 points)

**What it measures:** How positively does AI represent the brand?

### Scoring Criteria

| Score | Sentiment Distribution |
|-------|----------------------|
| 10 | 70%+ positive responses |
| 7-9 | 50-70% positive |
| 5-6 | Mostly neutral |
| 3-4 | Mixed positive/negative |
| 0-2 | Predominantly negative |

### Sentiment Indicators

**Positive Keywords:**
excellent, great, leading, innovative, trusted, reliable, recommended, top, outstanding

**Negative Keywords:**
poor, complaints, issues, problems, controversial, struggling, unreliable, avoid

### Red Flags
- Negative > Positive mentions
- >30% negative sentiment
- Specific complaints or controversies mentioned

---

## Grade Mapping

| Score | Grade | Status |
|-------|-------|--------|
| 90-100 | A | Excellent AI visibility |
| 80-89 | B | Good visibility, minor gaps |
| 70-79 | C | Needs improvement |
| 60-69 | D | Poor visibility |
| <60 | F | Critical - unknown to AI |

---

## Issue Severity Definitions

| Level | Definition | Action Required |
|-------|------------|-----------------|
| Critical | Prevents AI discovery or causes major harm | Immediate fix |
| High | Significantly impacts AI representation | Fix within 2 weeks |
| Medium | Noticeable impact on AI visibility | Fix within 1 month |
| Low | Minor impact, nice to have | Fix when convenient |
