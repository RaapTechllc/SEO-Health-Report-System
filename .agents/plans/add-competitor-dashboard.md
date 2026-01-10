# Feature: Add Competitor Comparison Dashboard

The following plan should be complete, but validate documentation and codebase patterns before implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files.

## Feature Description

Add a dedicated competitor comparison section to reports showing side-by-side scores, strengths/weaknesses analysis, and competitive positioning insights. Currently competitor data is collected but not prominently displayed.

## User Story

As a **marketing manager**
I want to **see how my site compares to competitors**
So that **I can prioritize improvements that give competitive advantage**

## Problem Statement

The system accepts `competitor_urls` but only does minimal comparison in technical audit. There's no consolidated view showing:
- Side-by-side score comparison
- Relative strengths/weaknesses
- Competitive gap analysis
- Actionable competitive insights

## Solution Statement

Create a competitor analysis module that runs lightweight audits on competitors and generates comparison visualizations. Add a new "Competitive Analysis" section to reports with comparison tables and gap analysis.

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: High
**Primary Systems Affected**: `seo-health-report/scripts/`, report generation
**Dependencies**: None (uses existing audit infrastructure)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - READ BEFORE IMPLEMENTING

- `seo-health-report/scripts/orchestrate.py` (lines 1-80) - Why: `run_full_audit()` flow to extend
- `seo-technical-audit/__init__.py` (lines 150-180) - Why: `run_competitor_comparison()` existing pattern
- `seo-health-report/scripts/build_report.py` (lines 50-100) - Why: Section structure to add to
- `seo-health-report/scripts/calculate_scores.py` (lines 100-150) - Why: `calculate_benchmark_comparison()` pattern

### New Files to Create

- `seo-health-report/scripts/compare_competitors.py` - Competitor analysis logic

### Files to Update

- `seo-health-report/scripts/orchestrate.py` - Add competitor audit step
- `seo-health-report/scripts/build_report.py` - Add comparison section
- `seo-health-report/__init__.py` - Expose comparison in results

### Patterns to Follow

**Existing comparison pattern** (from `seo-technical-audit/__init__.py`):
```python
def run_competitor_comparison(
    target_url: str,
    target_score: int,
    competitor_urls: List[str],
    strategy: str = "mobile"
) -> Dict[str, Any]:
    comparison = {
        "your_score": target_score,
        "competitor_scores": {},
        "component_comparison": {}
    }
```

**Section structure** (from `build_report.py`):
```python
sections.append({
    "type": "competitor_analysis",
    "title": "Competitive Analysis",
    "content": build_competitor_section(comparison_data)
})
```

**Score color logic** (from `generate_summary.py`):
```python
if score >= 80: return "#34a853"  # Green
elif score >= 60: return "#fbbc04"  # Yellow
else: return "#ea4335"  # Red
```

---

## IMPLEMENTATION PLAN

### Prerequisites Gate

- [ ] Existing audit modules working
- [ ] At least one competitor URL available for testing

### Phase 1: Foundation

Create competitor comparison module with lightweight audit runner.

### Phase 2: Core Implementation

Implement comparison logic and gap analysis.

### Phase 3: Integration

Add comparison section to report generation.

### Phase 4: Testing

Validate with real competitor URLs.

---

## STEP-BY-STEP TASKS

### Task 1: CREATE `seo-health-report/scripts/compare_competitors.py`

- **IMPLEMENT**: Competitor analysis module
- **IMPORTS**:
  ```python
  from typing import Dict, Any, List, Optional
  from urllib.parse import urlparse
  ```
- **COMPONENTS**:
  ```python
  def run_competitor_audits(
      competitor_urls: List[str],
      primary_keywords: List[str],
      depth: int = 10  # Lighter crawl for competitors
  ) -> Dict[str, Dict[str, Any]]:
      """Run lightweight audits on competitors."""
      results = {}
      for url in competitor_urls[:3]:  # Max 3 competitors
          domain = extract_domain(url)
          try:
              # Run quick technical check
              from seo_technical_audit.scripts.analyze_speed import get_pagespeed_insights
              psi = get_pagespeed_insights(url)
              
              results[domain] = {
                  "url": url,
                  "psi_score": psi.get("score", 0),
                  "estimated_score": estimate_overall_score(psi),
                  "strengths": [],
                  "weaknesses": []
              }
          except Exception as e:
              results[domain] = {"url": url, "error": str(e)}
      return results
  
  def compare_scores(
      target_scores: Dict[str, Any],
      competitor_results: Dict[str, Dict[str, Any]]
  ) -> Dict[str, Any]:
      """Generate comparison analysis."""
      comparison = {
          "target": target_scores,
          "competitors": competitor_results,
          "ranking": [],  # Sorted by score
          "gaps": [],     # Where target is behind
          "advantages": [] # Where target is ahead
      }
      
      # Calculate ranking
      all_scores = [("You", target_scores.get("overall_score", 0))]
      for domain, data in competitor_results.items():
          all_scores.append((domain, data.get("estimated_score", 0)))
      
      comparison["ranking"] = sorted(all_scores, key=lambda x: x[1], reverse=True)
      comparison["position"] = next(i for i, (name, _) in enumerate(comparison["ranking"]) if name == "You") + 1
      
      # Identify gaps and advantages
      target_score = target_scores.get("overall_score", 0)
      for domain, data in competitor_results.items():
          comp_score = data.get("estimated_score", 0)
          if comp_score > target_score:
              comparison["gaps"].append({
                  "competitor": domain,
                  "gap": comp_score - target_score,
                  "insight": f"{domain} scores {comp_score - target_score} points higher"
              })
          elif comp_score < target_score:
              comparison["advantages"].append({
                  "competitor": domain,
                  "advantage": target_score - comp_score,
                  "insight": f"You lead {domain} by {target_score - comp_score} points"
              })
      
      return comparison
  
  def generate_competitive_insights(comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
      """Generate actionable competitive insights."""
      insights = []
      
      position = comparison.get("position", 1)
      total = len(comparison.get("ranking", []))
      
      if position == 1:
          insights.append({
              "type": "strength",
              "title": "Market Leader",
              "detail": "Your site leads all analyzed competitors"
          })
      elif position == total:
          insights.append({
              "type": "urgent",
              "title": "Competitive Gap",
              "detail": "Your site trails all analyzed competitors - prioritize improvements"
          })
      
      # Add gap-specific insights
      for gap in comparison.get("gaps", [])[:3]:
          insights.append({
              "type": "opportunity",
              "title": f"Close gap with {gap['competitor']}",
              "detail": gap["insight"]
          })
      
      return insights
  
  def extract_domain(url: str) -> str:
      """Extract clean domain from URL."""
      parsed = urlparse(url)
      domain = parsed.netloc
      if domain.startswith("www."):
          domain = domain[4:]
      return domain
  
  def estimate_overall_score(psi_data: Dict[str, Any]) -> int:
      """Estimate overall SEO score from PSI data."""
      psi_score = psi_data.get("score", 50)
      # Rough correlation: PSI accounts for ~30% of technical, which is 30% of overall
      # So PSI ≈ 9% of overall, but we extrapolate
      return min(100, int(psi_score * 0.8 + 20))  # Rough estimate
  ```
- **VALIDATE**: `python -c "from seo_health_report.scripts.compare_competitors import compare_scores"`

### Task 2: UPDATE `seo-health-report/scripts/orchestrate.py`

- **IMPLEMENT**: Add competitor audit step after main audits
- **CHANGES**:
  ```python
  # After Step 3 (AI Visibility Audit)
  
  # Step 4: Competitor Analysis (if competitors provided)
  if competitor_urls:
      print(f"[4/4] Running Competitor Analysis...")
      try:
          from .compare_competitors import run_competitor_audits, compare_scores
          competitor_results = run_competitor_audits(
              competitor_urls=competitor_urls,
              primary_keywords=primary_keywords
          )
          results["competitor_analysis"] = competitor_results
      except Exception as e:
          results["warnings"].append(f"Competitor analysis failed: {e}")
  ```
- **VALIDATE**: Run audit with competitors, check `competitor_analysis` in results

### Task 3: UPDATE `seo-health-report/scripts/build_report.py`

- **IMPLEMENT**: Add competitor comparison section
- **ADD** new section builder:
  ```python
  def build_competitor_section(comparison_data: Dict[str, Any]) -> Dict[str, Any]:
      """Build competitor comparison section content."""
      section = {
          "ranking_table": [],
          "gaps": [],
          "advantages": [],
          "insights": []
      }
      
      if not comparison_data:
          return section
      
      # Build ranking table
      for rank, (name, score) in enumerate(comparison_data.get("ranking", []), 1):
          section["ranking_table"].append({
              "rank": rank,
              "name": name,
              "score": score,
              "is_you": name == "You"
          })
      
      section["gaps"] = comparison_data.get("gaps", [])
      section["advantages"] = comparison_data.get("advantages", [])
      section["insights"] = comparison_data.get("insights", [])
      
      return section
  ```
- **ADD** section to `build_report_document()`:
  ```python
  # After AI Visibility section, before Action Plan
  if audit_results.get("competitor_analysis"):
      from .compare_competitors import compare_scores, generate_competitive_insights
      comparison = compare_scores(scores, audit_results["competitor_analysis"])
      comparison["insights"] = generate_competitive_insights(comparison)
      
      sections.append({
          "type": "competitor_analysis",
          "title": "Competitive Analysis",
          "content": build_competitor_section(comparison)
      })
  ```
- **VALIDATE**: Generate report with competitors, verify section appears

### Task 4: UPDATE report generators for new section

- **IMPLEMENT**: Add competitor section rendering to `generate_docx()` and `generate_markdown()`
- **PATTERN**: Follow existing section rendering
- **MARKDOWN OUTPUT**:
  ```markdown
  ## Competitive Analysis
  
  ### Ranking
  | Rank | Site | Score |
  |------|------|-------|
  | 1 | You | 75 |
  | 2 | competitor.com | 68 |
  
  ### Competitive Gaps
  - competitor2.com scores 5 points higher
  
  ### Your Advantages
  - You lead competitor.com by 7 points
  ```
- **VALIDATE**: Check markdown output includes comparison table

### Task 5: UPDATE `seo-health-report/__init__.py`

- **IMPLEMENT**: Expose competitor comparison in results
- **ADD** to `generate_report()` return:
  ```python
  result["competitor_comparison"] = audit_results.get("competitor_analysis")
  ```
- **VALIDATE**: `python -c "from seo_health_report import generate_report; help(generate_report)"`

---

## TESTING STRATEGY

### Manual Validation

1. Run audit with 2-3 competitor URLs
2. Verify competitor scores calculated
3. Verify ranking is correct
4. Verify gaps/advantages identified
5. Check report section renders properly

### Edge Cases

1. No competitors provided → section should not appear
2. Competitor URL unreachable → graceful error handling
3. All competitors score lower → "Market Leader" insight
4. All competitors score higher → "Competitive Gap" insight

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
python -m py_compile seo-health-report/scripts/compare_competitors.py
```

### Level 2: Import Tests

```bash
python -c "from seo_health_report.scripts.compare_competitors import run_competitor_audits, compare_scores"
```

### Level 3: Unit Test

```bash
python -c "
from seo_health_report.scripts.compare_competitors import compare_scores

target = {'overall_score': 75}
competitors = {
    'competitor1.com': {'estimated_score': 80},
    'competitor2.com': {'estimated_score': 65}
}

result = compare_scores(target, competitors)
print(f'Position: {result[\"position\"]} of {len(result[\"ranking\"])}')
print(f'Gaps: {len(result[\"gaps\"])}')
print(f'Advantages: {len(result[\"advantages\"])}')
"
```

### Level 4: Integration Test

```bash
python -c "
from seo_health_report import generate_report

result = generate_report(
    target_url='https://example.com',
    company_name='Test Corp',
    logo_file='',
    primary_keywords=['test'],
    competitor_urls=['https://competitor1.com', 'https://competitor2.com'],
    output_format='md',
    output_dir='/tmp'
)

print(f'Competitor data: {\"competitor_comparison\" in result}')
"
```

---

## ACCEPTANCE CRITERIA

- [ ] Competitor audits run for up to 3 competitors
- [ ] Ranking table shows all sites sorted by score
- [ ] Gaps identified where competitors lead
- [ ] Advantages identified where target leads
- [ ] Competitive insights generated
- [ ] Report section renders in DOCX and Markdown
- [ ] Graceful handling when competitor URL fails
- [ ] No section when no competitors provided

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each validation command passes
- [ ] Report includes competitor section
- [ ] Ranking is accurate
- [ ] No errors with unreachable competitors

---

## NOTES

**Design Decision**: Using lightweight PSI-only audit for competitors to keep runtime reasonable. Full audits would be too slow.

**Trade-off**: Estimated scores are rough approximations. Could add more audit components for accuracy at cost of speed.

**Limitation**: Max 3 competitors to prevent excessive API calls and report bloat.

**Future Enhancement**: Add historical tracking to show competitive position over time.
