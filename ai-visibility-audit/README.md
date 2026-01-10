# AI Visibility Audit

**Your competitive moat.** This audit evaluates how AI systems (ChatGPT, Claude, Perplexity, Google AI Overviews) perceive, represent, and cite a brand. Most SEO agencies don't offer this—you're first to market.

## Why This Matters

As AI-powered search grows, traditional SEO metrics become insufficient. Brands need to understand:

- **Do AI systems know about them?** When users ask "What's the best X?", does the brand appear?
- **Is the information accurate?** AI can hallucinate or use outdated data
- **Can AI parse their content?** LLMs need clean, semantic HTML to understand sites
- **Are they in knowledge graphs?** Google KG, Wikipedia, Wikidata feed AI systems
- **Will AI cite them?** Original research and quotable content drives citations

## Installation

```bash
cd ai-visibility-audit
pip install -r requirements.txt
```

### API Keys Required

| Service | Required | Environment Variable |
|---------|----------|---------------------|
| Claude (Anthropic) | Yes | `ANTHROPIC_API_KEY` |
| OpenAI (ChatGPT) | Optional | `OPENAI_API_KEY` |
| Google Knowledge Graph | Optional | `GOOGLE_KG_API_KEY` |

The audit degrades gracefully when optional APIs are unavailable.

## Quick Start

```python
from ai_visibility_audit import run_audit

results = run_audit(
    brand_name="Acme Corp",
    target_url="https://acme.com",
    products_services=["widgets", "gadgets", "consulting"],
    competitor_names=["CompetitorA", "CompetitorB"]
)

print(f"AI Visibility Score: {results['score']}/100 ({results['grade']})")
```

## Scoring Breakdown (100 points)

### AI Search Presence (25 points)
Does the brand appear when AI systems answer relevant queries?

| Score | Criteria |
|-------|----------|
| 25 | Brand mentioned prominently in 80%+ of relevant queries |
| 20 | Brand mentioned in 60-80% of queries |
| 15 | Brand mentioned in 40-60% of queries |
| 10 | Brand mentioned in 20-40% of queries |
| 5 | Brand rarely mentioned (<20% of queries) |
| 0 | Brand never appears in AI responses |

### Response Accuracy (20 points)
When AI mentions the brand, is the information correct?

| Score | Criteria |
|-------|----------|
| 20 | All information accurate and current |
| 15 | Minor inaccuracies (dates, small details) |
| 10 | Some outdated information |
| 5 | Significant inaccuracies present |
| 0 | Major hallucinations or wrong information |

### LLM Parseability (15 points)
Can AI systems easily extract information from the website?

| Score | Criteria |
|-------|----------|
| 15 | Semantic HTML, structured data, clear hierarchy |
| 12 | Good structure with minor issues |
| 9 | Adequate but could improve |
| 6 | Significant structural problems |
| 3 | Poor structure, hard to parse |
| 0 | Completely unparseable (heavy JS, no semantic markup) |

### Knowledge Graph Presence (15 points)
Is the brand in authoritative knowledge sources?

| Score | Criteria |
|-------|----------|
| 15 | Wikipedia + Google KG + Wikidata + industry DBs |
| 12 | Wikipedia + Google KG |
| 9 | Google KG only |
| 6 | Wikidata or industry databases only |
| 3 | Minimal presence |
| 0 | Not in any knowledge graphs |

### Citation Likelihood (15 points)
Does the site have content AI would want to cite?

| Score | Criteria |
|-------|----------|
| 15 | Original research, studies, unique data |
| 12 | Comprehensive guides, definitive resources |
| 9 | Quality content, some quotable material |
| 6 | Standard content, rarely citation-worthy |
| 3 | Thin content |
| 0 | No citable content |

### Sentiment (10 points)
How positively does AI represent the brand?

| Score | Criteria |
|-------|----------|
| 10 | Consistently positive framing |
| 7 | Mostly positive, some neutral |
| 5 | Neutral |
| 3 | Mixed positive/negative |
| 0 | Predominantly negative |

## Test Query Framework

The audit generates queries across these categories:

### Brand Queries
- "What is [brand]?"
- "Tell me about [brand]"
- "[brand] overview"

### Product/Service Queries
- "Best [product category]"
- "Compare [brand] vs [competitor]"
- "[product] recommendations"

### Problem Queries
- "[Problem brand solves]"
- "How to [task brand helps with]"
- "[Pain point] solutions"

### Reputation Queries
- "[brand] reviews"
- "[brand] complaints"
- "Is [brand] good?"

## Directory Structure

```
ai-visibility-audit/
├── SKILL.md              # Claude Code skill definition
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── __init__.py          # Package init
├── scripts/
│   ├── __init__.py
│   ├── query_ai_systems.py    # Query generation + AI interaction
│   ├── analyze_responses.py   # Score accuracy, sentiment
│   ├── check_parseability.py  # HTML structure analysis
│   ├── check_knowledge.py     # Knowledge graph presence
│   └── score_citability.py    # Original content analysis
├── references/
│   ├── query_templates.md     # Test query patterns
│   ├── scoring_rubric.md      # Point allocation details
│   ├── ai_optimization.md     # How to optimize for AI
│   ├── parseability_guide.md  # Semantic HTML for LLMs
│   └── knowledge_graph.md     # How to get into KG
└── assets/
    └── section_template.md    # Report section format
```

## Output Format

The audit produces a structured JSON report:

```json
{
  "score": 52,
  "grade": "D",
  "components": {
    "ai_presence": {
      "score": 12,
      "max": 25,
      "findings": [
        "Brand mentioned in 3/10 test queries",
        "Competitors mentioned more frequently",
        "Not appearing for product category queries"
      ]
    },
    "accuracy": {
      "score": 14,
      "max": 20,
      "findings": [
        "Founding year incorrect in ChatGPT response",
        "Product pricing outdated"
      ]
    }
  },
  "ai_responses": [
    {
      "query": "What is Acme Corp?",
      "system": "claude",
      "response": "...",
      "brand_mentioned": true,
      "sentiment": "positive"
    }
  ],
  "accuracy_issues": [
    {
      "claim": "Founded in 2015",
      "actual": "Founded in 2012",
      "source": "chatgpt",
      "severity": "medium"
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "knowledge_graph",
      "action": "Create Wikipedia article",
      "impact": "Would significantly improve AI awareness",
      "effort": "high"
    }
  ]
}
```

## Integration with SEO Health Report

This skill is designed to integrate with the `seo-health-report` orchestrator:

```python
# Called by orchestrator
from ai_visibility_audit import run_audit

ai_data = run_audit(
    brand_name=inputs['company_name'],
    target_url=inputs['target_url'],
    products_services=inputs['primary_keywords']
)

# ai_data feeds into composite score calculation
# AI Visibility weighted at 35% of overall SEO Health Score
```

## Competitive Advantage

This audit provides insights no traditional SEO tool offers:

1. **First-mover advantage** - Agencies aren't doing this yet
2. **Future-proof** - AI search is growing rapidly
3. **Actionable** - Clear steps to improve AI visibility
4. **Measurable** - Track improvements over time
5. **Differentiated** - Sets your reports apart from competitors
