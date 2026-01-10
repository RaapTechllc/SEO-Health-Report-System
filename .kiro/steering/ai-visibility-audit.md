---
inclusion: fileMatch
fileMatchPattern: "ai-visibility-audit/**"
---

# AI Visibility Audit Guidelines

This is the differentiator skill—most SEO agencies don't offer AI visibility analysis.

## Components (100 points total)

| Component | Points | Purpose |
|-----------|--------|---------|
| AI Search Presence | 25 | Does brand appear in AI responses? |
| Response Accuracy | 20 | Are facts correct? Any hallucinations? |
| LLM Parseability | 15 | Clean HTML, semantic structure |
| Knowledge Graph | 15 | Google KG, Wikipedia, Wikidata presence |
| Citation Likelihood | 15 | Original research, quotable content |
| Sentiment | 10 | Positive/negative/neutral tone |

## Key Scripts

- `query_ai_systems.py` - Generate queries and call AI APIs
- `analyze_responses.py` - Parse and score AI responses
- `check_parseability.py` - Analyze site structure for LLM consumption
- `check_knowledge.py` - Check knowledge graph presence
- `score_citability.py` - Evaluate citation-worthy content

## Query Categories

Generate test queries across these categories:
1. Brand awareness ("What is [brand]?")
2. Product/service queries ("Best [product category]")
3. Comparison queries ("[brand] vs [competitor]")
4. Problem-solution queries ("How to solve [problem brand solves]")

## Parseability Checks

- Clean, semantic HTML structure
- Proper heading hierarchy
- Schema.org markup
- Machine-readable data formats
- Accessible content structure

## When Modifying

- Maintain API key fallback behavior (graceful degradation)
- Keep scoring weights consistent with SKILL.md
- Update references/scoring_rubric.md if changing point allocations
