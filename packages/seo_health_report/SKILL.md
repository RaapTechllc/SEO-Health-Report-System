---
name: seo-health-report
description: Generate comprehensive SEO health report with branded PDF/DOCX output. Use when creating full website audit reports, producing client-ready SEO deliverables, or running complete technical + content + AI visibility analysis. Orchestrates sub-audits and assembles professional report with company branding.
---

# SEO Health Report

Master orchestrator that runs all three audits and produces a branded executive report.

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| target_url | Yes | Root domain to audit |
| company_name | Yes | Client company name |
| logo_file | Yes | Company logo (PNG/SVG path) |
| brand_colors | No | Primary/secondary hex codes |
| primary_keywords | Yes | 5-10 target keywords |
| competitor_urls | No | Up to 3 competitors |
| output_format | No | PDF (default) or DOCX |

## Workflow

```
Step 1: Validate Inputs
        ↓
Step 2: Run seo-technical-audit
        → Store results as technical_data
        ↓
Step 3: Run seo-content-authority
        → Store results as content_data
        ↓
Step 4: Run ai-visibility-audit
        → Store results as ai_data
        ↓
Step 5: Calculate Composite Score
        → Technical (30%) + Content (35%) + AI (35%)
        ↓
Step 6: Generate Executive Summary
        → Top-line scores, critical issues, quick wins
        ↓
Step 7: Assemble Report Sections
        → Cover + Summary + 3 Audits + Action Plan
        ↓
Step 8: Apply Branding
        → Logo, colors, fonts, styling
        ↓
Step 9: Output Final Document
```

## Running the Report

```python
from seo_health_report import generate_report

report = generate_report(
    target_url="https://acme.com",
    company_name="Acme Corporation",
    logo_file="/path/to/logo.png",
    primary_keywords=["widgets", "gadgets", "solutions"],
    brand_colors={"primary": "#1a73e8", "secondary": "#34a853"},
    output_format="pdf"
)

print(f"Report saved to: {report['output_path']}")
print(f"Overall Score: {report['score']}/100 ({report['grade']})")
```

## Composite Scoring

```
Overall Score = (Technical × 0.30) + (Content × 0.35) + (AI × 0.35)
```

AI weighted higher—it's your differentiator.

### Grade Mapping

| Score | Grade | Status |
|-------|-------|--------|
| 90-100 | A | Excellent |
| 80-89 | B | Good |
| 70-79 | C | Needs Work |
| 60-69 | D | Poor |
| <60 | F | Critical |

## Output Schema

```json
{
  "overall_score": 72,
  "grade": "C",
  "component_scores": {
    "technical": {"score": 73, "weight": 0.30, "weighted": 21.9},
    "content": {"score": 68, "weight": 0.35, "weighted": 23.8},
    "ai_visibility": {"score": 52, "weight": 0.35, "weighted": 18.2}
  },
  "critical_issues": [],
  "quick_wins": [],
  "output_path": "/path/to/report.pdf"
}
```

## Report Structure

1. **Cover Page** - Logo, title, date, prepared by
2. **Executive Summary** - Overall score gauge, 3 sub-scores, top 5 actions
3. **Technical Health** - 4-5 pages with detailed findings
4. **Content & Authority** - 4-5 pages with content roadmap
5. **AI Visibility** - 4-5 pages with AI response analysis
6. **Action Plan** - Prioritized recommendations with timeline

## Key Files

- `scripts/orchestrate.py` - Main workflow controller
- `scripts/calculate_scores.py` - Composite scoring logic
- `scripts/generate_summary.py` - Executive summary generation
- `scripts/build_report.py` - Document assembly
- `scripts/apply_branding.py` - Logo/color injection
- `assets/report_template.docx` - Base template
