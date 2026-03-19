---
inclusion: fileMatch
fileMatchPattern: "seo-content-authority/**"
---

# SEO Content & Authority Audit Guidelines

Evaluates content quality, E-E-A-T signals, topical authority, and link profile.

## Components (100 points total)

| Component | Points | Purpose |
|-----------|--------|---------|
| Content Quality | 25 | Word count, readability, media, freshness |
| E-E-A-T Signals | 20 | Author pages, credentials, about, contact |
| Keyword Position | 15 | Visibility, SERP features, intent alignment |
| Topical Authority | 15 | Topic clusters, semantic coverage, pillars |
| Backlink Quality | 15 | DA distribution, relevance, toxic links |
| Internal Linking | 10 | Orphan pages, link equity, anchor diversity |

## Key Scripts

- `analyze_content.py` - Content quality analysis
- `check_eeat.py` - E-E-A-T signal detection
- `map_topics.py` - Topical coverage mapping
- `analyze_links.py` - Internal link analysis
- `score_backlinks.py` - Link profile evaluation

## E-E-A-T Checklist

Experience, Expertise, Authoritativeness, Trustworthiness:
- Author bios with credentials
- About page with company history
- Contact information visible
- Trust signals (certifications, awards)
- Original research and data
- Expert citations and references

## Content Quality Benchmarks

- Minimum 300 words for informational pages
- Readability: Flesch-Kincaid grade 8-10
- Media: At least 1 image per 300 words
- Freshness: Updated within 12 months

## When Modifying

- Reference `references/eeat_checklist.md` for E-E-A-T criteria
- Keep scoring weights consistent with SKILL.md
