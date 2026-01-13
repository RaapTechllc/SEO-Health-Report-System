---
inclusion: fileMatch
fileMatchPattern: "seo-health-report/**"
---

# SEO Health Report Guidelines

Master orchestrator that runs all audits and produces branded reports.

## Orchestration Flow

```
1. Validate inputs
2. Run seo-technical-audit → technical_data
3. Run seo-content-authority → content_data
4. Run ai-visibility-audit → ai_data
5. Calculate composite score
6. Generate executive summary
7. Assemble report sections
8. Apply branding (logo, colors)
9. Output final document
```

## Composite Scoring

```python
overall = (technical * 0.30) + (content * 0.35) + (ai * 0.35)
```

AI visibility weighted higher—it's the differentiator.

## Report Structure

1. Cover Page - Logo, title, date
2. Executive Summary - Scores, top 5 actions
3. Technical Health - 4-5 pages
4. Content & Authority - 4-5 pages
5. AI Visibility - 4-5 pages
6. Action Plan - Prioritized recommendations

## Key Scripts

- `orchestrate.py` - Main workflow controller
- `calculate_scores.py` - Composite scoring logic
- `generate_summary.py` - Executive summary
- `build_report.py` - Document assembly
- `apply_branding.py` - Logo/color injection

## Output Formats

- PDF (default) - Professional delivery
- DOCX - Editable for customization

## When Modifying

- Maintain weight ratios (30/35/35)
- Keep report template in `assets/report_template.docx`
- Test with sample logos of various sizes
