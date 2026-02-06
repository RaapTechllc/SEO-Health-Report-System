---
name: ai-visibility-audit
description: Audit brand visibility in AI systems (ChatGPT, Claude, Perplexity, Google AI). Use when checking how AI represents a brand, analyzing LLM parseability, knowledge graph presence, citation likelihood, or answer engine optimization. Outputs AI Visibility Score (0-100) with optimization playbook.
---

# AI Visibility Audit

Evaluate how AI systems perceive, represent, and cite your brand. This is the differentiator—most SEO agencies don't offer this.

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| brand_name | Yes | Company/brand name |
| target_url | Yes | Primary website |
| products_services | Yes | Key offerings (5-10) |
| competitor_names | No | Competitor brands to compare |
| test_queries | No | Specific queries to test |

## Workflow

```
1. Generate test queries across categories
2. Query AI systems (Claude, ChatGPT, Perplexity)
3. Analyze responses for brand presence
4. Check response accuracy against website
5. Evaluate LLM parseability of website
6. Check knowledge graph presence
7. Assess citation likelihood
8. Calculate composite score
9. Generate recommendations
```

## Audit Components (100 points)

| Component | Weight | What's Checked |
|-----------|--------|----------------|
| AI Search Presence | 25 | Does brand appear in AI responses? How prominent? |
| Response Accuracy | 20 | Are facts correct? Outdated info? Hallucinations? |
| LLM Parseability | 15 | Clean HTML, semantic structure, machine-readable data |
| Knowledge Graph | 15 | Google KG, Wikipedia, Wikidata, Crunchbase presence |
| Citation Likelihood | 15 | Original research, quotable content, reference-worthy assets |
| Sentiment | 10 | Positive/negative/neutral in AI responses |

## Running the Audit

### Step 1: Gather Inputs
```python
from scripts.query_ai_systems import generate_test_queries

queries = generate_test_queries(
    brand_name="Acme Corp",
    products_services=["widget", "gadget", "service"],
    competitors=["CompetitorA", "CompetitorB"]
)
```

### Step 2: Query AI Systems
```python
from scripts.query_ai_systems import query_all_systems

responses = query_all_systems(queries)
# Returns responses from Claude, ChatGPT (if API key), Perplexity
```

### Step 3: Analyze Responses
```python
from scripts.analyze_responses import analyze_brand_presence, check_accuracy

presence_score = analyze_brand_presence(responses, brand_name)
accuracy_score = check_accuracy(responses, ground_truth_from_website)
```

### Step 4: Check Parseability
```python
from scripts.check_parseability import analyze_site_structure

parseability_score = analyze_site_structure(target_url)
```

### Step 5: Check Knowledge Graph
```python
from scripts.check_knowledge import check_all_sources

kg_score = check_all_sources(brand_name, target_url)
```

### Step 6: Score Citability
```python
from scripts.score_citability import analyze_content_citability

citation_score = analyze_content_citability(target_url)
```

### Step 7: Generate Report
```python
from scripts.generate_report import create_ai_visibility_report

report = create_ai_visibility_report(
    presence_score,
    accuracy_score,
    parseability_score,
    kg_score,
    citation_score,
    sentiment_score
)
```

## Output Schema

```json
{
  "score": 52,
  "grade": "D",
  "components": {
    "ai_presence": {"score": 12, "max": 25, "findings": []},
    "accuracy": {"score": 14, "max": 20, "findings": []},
    "parseability": {"score": 10, "max": 15, "findings": []},
    "knowledge_graph": {"score": 8, "max": 15, "findings": []},
    "citation_likelihood": {"score": 5, "max": 15, "findings": []},
    "sentiment": {"score": 3, "max": 10, "findings": []}
  },
  "ai_responses": [],
  "accuracy_issues": [],
  "optimization_opportunities": [],
  "recommendations": []
}
```

## Key Files

- `scripts/query_ai_systems.py` - Query generation and AI system interaction
- `scripts/analyze_responses.py` - Response analysis and scoring
- `scripts/check_parseability.py` - Website structure analysis for LLM consumption
- `scripts/check_knowledge.py` - Knowledge graph presence checking
- `scripts/score_citability.py` - Citation likelihood analysis
- `references/query_templates.md` - Test query patterns by category
- `references/scoring_rubric.md` - Detailed point allocation
- `references/ai_optimization.md` - How to optimize for AI (your moat content)
