---
name: seo-content-authority
description: Audit content quality and domain authority. Use when analyzing E-E-A-T signals, keyword gaps, topical coverage, backlink quality, or internal linking structure. Outputs Authority Score (0-100) with content roadmap.
---

# SEO Content & Authority Audit

Evaluate content quality, E-E-A-T signals, topical authority, and link profile.

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| target_url | Yes | Root domain to audit |
| primary_keywords | Yes | 5-10 target keywords/topics |
| competitor_urls | No | Up to 3 competitors |

## Workflow

```
1. Crawl and analyze content inventory
2. Evaluate content quality metrics
3. Assess E-E-A-T signals
4. Analyze topical coverage and gaps
5. Evaluate internal link structure
6. Assess external link profile (if data available)
7. Calculate composite score
8. Generate content roadmap
```

## Audit Components (100 points)

| Component | Weight | What's Checked |
|-----------|--------|----------------|
| Content Quality | 25 | Word count, readability, media richness, freshness |
| E-E-A-T Signals | 20 | Author pages, credentials, about page, contact info |
| Keyword Position | 15 | Current visibility, SERP features, intent alignment |
| Topical Authority | 15 | Topic cluster depth, semantic coverage, pillar structure |
| Backlink Quality | 15 | DA distribution, relevance, toxic links, velocity |
| Internal Linking | 10 | Orphan pages, link equity flow, anchor diversity |

## Running the Audit

### Step 1: Analyze Content
```python
from scripts.analyze_content import analyze_page_content, assess_content_quality

content = analyze_page_content(target_url)
quality_score = assess_content_quality(content)
```

### Step 2: Check E-E-A-T
```python
from scripts.check_eeat import analyze_eeat_signals

eeat_score = analyze_eeat_signals(target_url)
```

### Step 3: Map Topics
```python
from scripts.map_topics import analyze_topical_coverage

topic_score = analyze_topical_coverage(target_url, primary_keywords)
```

### Step 4: Analyze Links
```python
from scripts.analyze_links import analyze_internal_links

link_score = analyze_internal_links(target_url)
```

## Output Schema

```json
{
  "score": 68,
  "grade": "D",
  "components": {
    "content_quality": {"score": 20, "max": 25, "findings": []},
    "eeat": {"score": 14, "max": 20, "findings": []},
    "keyword_position": {"score": 10, "max": 15, "findings": []},
    "topical_authority": {"score": 9, "max": 15, "findings": []},
    "backlinks": {"score": 10, "max": 15, "findings": []},
    "internal_links": {"score": 5, "max": 10, "findings": []}
  },
  "content_gaps": [],
  "topic_opportunities": [],
  "recommendations": []
}
```

## Key Files

- `scripts/analyze_content.py` - Content quality analysis
- `scripts/check_eeat.py` - E-E-A-T signal detection
- `scripts/map_topics.py` - Topical coverage mapping
- `scripts/analyze_links.py` - Internal link analysis
- `scripts/score_backlinks.py` - Link profile evaluation
- `references/eeat_checklist.md` - E-E-A-T evaluation criteria
- `references/content_benchmarks.md` - Quality benchmarks
