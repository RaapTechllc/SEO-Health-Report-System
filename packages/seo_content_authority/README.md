# SEO Content & Authority Audit

Comprehensive content quality and authority analysis including E-E-A-T signals, topical coverage, and link profile evaluation.

## Overview

Content quality and domain authority are crucial ranking factors. This audit evaluates:
- How well your content meets user intent
- Whether you demonstrate expertise and trustworthiness
- Your topical depth and coverage gaps
- Internal link structure and equity flow
- External link profile health

## Installation

```bash
cd seo-content-authority
pip install -r requirements.txt
```

### Optional API Keys

| Service | Environment Variable | Purpose |
|---------|---------------------|---------|
| Ahrefs | `AHREFS_API_KEY` | Backlink data |
| Moz | `MOZ_API_KEY` | Domain authority |
| Semrush | `SEMRUSH_API_KEY` | Keyword rankings |

The audit works without these but backlink/ranking data will be limited.

## Quick Start

```python
from seo_content_authority import run_audit

results = run_audit(
    target_url="https://example.com",
    primary_keywords=["widget", "gadget", "service"],
    competitor_urls=["https://competitor1.com"]
)

print(f"Authority Score: {results['score']}/100 ({results['grade']})")
```

## Scoring Breakdown (100 points)

### Content Quality (25 points)

Does your content meet quality standards?

| Score | Criteria |
|-------|----------|
| 25 | Comprehensive, well-written, multimedia-rich, fresh |
| 20 | Good quality, minor improvements needed |
| 15 | Average quality, some thin content |
| 10 | Below average, significant gaps |
| 5 | Poor quality content |

**Metrics evaluated:**
- Average word count (benchmark: 1500+ for pillar content)
- Readability score (Flesch-Kincaid)
- Media richness (images, videos, infographics)
- Content freshness (last updated dates)
- Unique vs duplicate content

### E-E-A-T Signals (20 points)

Do you demonstrate Experience, Expertise, Authoritativeness, Trust?

| Score | Criteria |
|-------|----------|
| 20 | Strong E-E-A-T across all dimensions |
| 16 | Good signals, minor gaps |
| 12 | Some E-E-A-T present |
| 8 | Weak E-E-A-T signals |
| 4 | Very limited E-E-A-T |

**Signals checked:**
- Author pages with credentials
- About page quality
- Contact information
- Privacy policy and terms
- Reviews and testimonials
- Awards and certifications
- External citations

### Keyword Position (15 points)

How visible are you for target keywords?

| Score | Criteria |
|-------|----------|
| 15 | Top 3 for most keywords, own SERP features |
| 12 | Top 10 for most keywords |
| 9 | Page 1 for some keywords |
| 6 | Page 2-3 rankings |
| 3 | Limited visibility |

**Note:** Without ranking API, this scores based on content optimization for keywords.

### Topical Authority (15 points)

How thoroughly do you cover your topics?

| Score | Criteria |
|-------|----------|
| 15 | Deep topic clusters, comprehensive coverage |
| 12 | Good coverage, some gaps |
| 9 | Basic coverage of main topics |
| 6 | Limited topical depth |
| 3 | Shallow topic coverage |

**Metrics:**
- Topic cluster identification
- Content depth per topic
- Semantic keyword coverage
- Pillar/cluster page structure

### Backlink Quality (15 points)

What's the quality of your link profile?

| Score | Criteria |
|-------|----------|
| 15 | High-quality, relevant, diverse links |
| 12 | Good profile, minor issues |
| 9 | Average profile |
| 6 | Some toxic or low-quality links |
| 3 | Poor link profile |

**Note:** Requires external API (Ahrefs, Moz, Semrush) for full analysis.

### Internal Linking (10 points)

How well does link equity flow through your site?

| Score | Criteria |
|-------|----------|
| 10 | Excellent internal linking, no orphans |
| 8 | Good structure, minor issues |
| 6 | Average linking |
| 4 | Poor internal linking |
| 2 | Many orphan pages |

**Metrics:**
- Orphan pages (no internal links pointing to them)
- Click depth (pages >3 clicks from home)
- Link equity distribution
- Anchor text diversity

## Directory Structure

```
seo-content-authority/
├── SKILL.md              # Claude Code skill definition
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── __init__.py          # Package init with run_audit()
├── scripts/
│   ├── __init__.py
│   ├── analyze_content.py   # Content quality analysis
│   ├── check_eeat.py        # E-E-A-T signal detection
│   ├── map_topics.py        # Topic cluster analysis
│   ├── analyze_links.py     # Internal link structure
│   └── score_backlinks.py   # External link profile
├── references/
│   ├── eeat_checklist.md    # E-E-A-T evaluation criteria
│   ├── scoring_rubric.md    # Point allocation details
│   ├── content_benchmarks.md # Industry benchmarks
│   └── topic_modeling.md    # Topic cluster methodology
└── assets/
    └── section_template.md  # Report section format
```

## E-E-A-T Framework

### Experience
- First-hand experience visible in content
- Case studies and real examples
- Author has practical experience in topic

### Expertise
- Author credentials and qualifications
- Technical depth appropriate for topic
- Accurate, well-researched information

### Authoritativeness
- Industry recognition and citations
- Backlinks from authoritative sources
- Mentioned by other experts

### Trustworthiness
- Clear contact information
- Transparent business practices
- Accurate, honest content
- User privacy protected

## Content Gap Analysis

The audit identifies:

1. **Missing topics** - Keywords competitors rank for that you don't
2. **Thin content** - Pages that need expansion
3. **Outdated content** - Pages needing refresh
4. **Missing formats** - Content types you're not using
5. **Cluster gaps** - Missing supporting content for pillars

## Integration

This skill integrates with the `seo-health-report` orchestrator:

```python
from seo_content_authority import run_audit

content_data = run_audit(
    target_url=inputs['target_url'],
    primary_keywords=inputs['primary_keywords']
)

# content_data contributes 35% to overall SEO Health Score
```

## Recommendations Output

```json
{
  "recommendations": [
    {
      "priority": "high",
      "category": "content_quality",
      "action": "Expand thin content pages",
      "pages": ["/product-a", "/service-b"],
      "details": "These pages have <500 words. Expand to 1500+ words.",
      "impact": "high",
      "effort": "medium"
    },
    {
      "priority": "high",
      "category": "eeat",
      "action": "Add author pages",
      "details": "Create detailed author bios with credentials",
      "impact": "high",
      "effort": "low"
    }
  ],
  "content_roadmap": [
    {
      "topic": "widget comparison",
      "type": "pillar",
      "target_keywords": ["best widgets", "widget comparison"],
      "suggested_length": 2500,
      "priority": "high"
    }
  ]
}
```
