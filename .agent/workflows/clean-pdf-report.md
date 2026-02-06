---
description: Generate clean, professional PDF reports with proper formatting and no overlapping text
---

# Clean PDF Report Generation Workflow

This workflow ensures all reports are generated with proper formatting, consistent scores, and professional layout.

## Report Types Covered

| Report Type | Generator | Output |
|------------|-----------|--------|
| **Premium PDF** | `generate_premium_report.py` | Full SEO health report with branding |
| **Tier Comparison** | `generate_tier_comparison.py` | Low/Medium/High tier reports |
| **One-Pager** | `generate_one_pager.py` | Executive summary one-page |
| **DOCX Report** | `premium_report_template.py` | Word format report |

## Pre-Flight Checks

1. **Verify audit data is complete**
   ```bash
   python3 -c "import json; d = json.load(open('YOUR_AUDIT.json')); print(f'Score: {d.get(\"overall_score\")}, Grade: {d.get(\"grade\")}')"
   ```

2. **Clear cached charts** (prevents stale/mismatched visuals)
   ```bash
   rm -rf ./charts/* ./reports/charts/*
   ```

## Generate Reports

// turbo
3. **Generate Premium PDF Report**
   ```bash
   python3 generate_premium_report.py YOUR_AUDIT.json reports/OUTPUT_REPORT.pdf
   ```

// turbo
4. **Generate Tier Comparison Reports** (optional)
   ```bash
   python3 generate_tier_comparison.py YOUR_AUDIT.json high
   ```

## Quality Checks

5. **Review cover page** - Check for:
   - [ ] Consistent score display (same number everywhere)
   - [ ] No overlapping text between title/subtitle/company
   - [ ] Proper spacing between elements
   - [ ] Score badge clearly visible and centered

6. **Review executive summary** - Check for:
   - [ ] Same score as cover page
   - [ ] Percentile shows proper ordinal (1st, 2nd, 3rd, not 1th)
   - [ ] Payback period months pluralized correctly (1 month, 3 months)

7. **Review market position section** - Check for:
   - [ ] Consistent rank display
   - [ ] Proper ordinal formatting for percentiles

## Formatting Utilities

All reports use centralized formatting from `packages/core/formatting.py`:

```python
from packages.core.formatting import ordinal, pluralize, format_months

ordinal(1)        # → "1st"
ordinal(2)        # → "2nd"
ordinal(11)       # → "11th"
ordinal(21)       # → "21st"

pluralize(1, 'month')  # → "month"
pluralize(3, 'month')  # → "months"

format_months(1)   # → "1 month"
format_months(3)   # → "3 months"
```

## Troubleshooting

### Overlapping Text
If text still overlaps:
- Check that logo aspect ratio is reasonable (not too wide/tall)
- Reduce company name length if very long
- Clear charts dir and regenerate

### Score Inconsistencies
If scores differ between pages:
- Ensure using centralized `self.overall_score` and `self.grade` properties
- Check that audit JSON has single source of truth for score
- Clear cached badge images (they include score in filename)

### Grammar Errors
If you see "1 months" or "1th":
- Use `pluralize(value, 'month')` for singular/plural
- Use `ordinal(value)` for 1st/2nd/3rd formatting
- Import from `packages.core.formatting`

## Key Files

- `generate_premium_report.py` - Main PDF report generator
- `generate_tier_comparison.py` - Tier-based report wrapper
- `generate_one_pager.py` - Executive summary generator
- `packages/core/formatting.py` - Centralized formatting utilities
- `competitive_intel/roi_calculator.py` - ROI projections
- `competitive_intel/market_intelligence.py` - Market analysis
- `.claude/skills/pdf/SKILL.md` - PDF generation skill documentation
