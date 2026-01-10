# SEO Health Report - Master Orchestrator

Generate comprehensive, branded SEO health reports by orchestrating technical, content, and AI visibility audits.

## Overview

This is the master skill that:
1. Runs all three specialized audits
2. Calculates composite scores
3. Generates prioritized recommendations
4. Produces branded professional reports

## Installation

```bash
cd seo-health-report
pip install -r requirements.txt
```

### Dependencies

This skill requires the three audit packages:
- `seo-technical-audit`
- `seo-content-authority`
- `ai-visibility-audit`

### Optional

For PDF/DOCX generation:
```bash
pip install python-docx  # DOCX generation
pip install reportlab    # PDF generation (alternative)
pip install weasyprint   # PDF from HTML
```

## Quick Start

```python
from seo_health_report import generate_report

report = generate_report(
    target_url="https://acme.com",
    company_name="Acme Corporation",
    logo_file="./logo.png",
    primary_keywords=["widgets", "gadgets", "enterprise solutions"],
    competitor_urls=["https://competitor1.com"],
    output_format="docx"
)

print(f"Overall Score: {report['overall_score']}/100 ({report['grade']})")
print(f"Report saved: {report['output_path']}")
```

## Scoring System

### Composite Score Calculation

```
Overall Score = (Technical × 30%) + (Content × 35%) + (AI × 35%)
```

**Why this weighting?**
- **AI Visibility (35%)**: Your competitive differentiator
- **Content & Authority (35%)**: Most impactful for rankings
- **Technical (30%)**: Important foundation

### Grade Mapping

| Score | Grade | Meaning |
|-------|-------|---------|
| 90-100 | A | Excellent - minor optimizations only |
| 80-89 | B | Good - some improvements recommended |
| 70-79 | C | Needs Work - significant gaps identified |
| 60-69 | D | Poor - major issues to address |
| <60 | F | Critical - urgent attention required |

## Report Structure

### 1. Cover Page
- Company logo (centered)
- "SEO Health Report"
- Company name
- Report date
- "Prepared by [Your Brand]"

### 2. Executive Summary (1 page)
- Overall Health Score gauge (0-100)
- Three component scores with traffic lights
- "What This Means" interpretation
- Top 5 Critical Actions

### 3. Technical Health (4-5 pages)
- Component score breakdown
- Crawlability analysis
- Page speed metrics (Core Web Vitals)
- Mobile optimization status
- Security audit results
- Structured data validation
- Priority recommendations

### 4. Content & Authority (4-5 pages)
- E-E-A-T assessment
- Content quality metrics
- Topic cluster analysis
- Content gap identification
- Internal linking structure
- Backlink profile summary
- Content roadmap

### 5. AI Visibility (4-5 pages)
- "How AI Sees Your Brand"
- Sample AI response quotes
- Accuracy assessment
- Knowledge graph status
- Citation likelihood
- AI optimization opportunities

### 6. Action Plan (2-3 pages)
- Quick Wins (high impact, low effort)
- Strategic Initiatives (high impact, high effort)
- Prioritized task checklist
- Resource estimates

### 7. Appendix
- Full technical data
- Complete issue list
- Methodology notes

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_url` | string | Yes | Root domain to audit |
| `company_name` | string | Yes | Client company name |
| `logo_file` | string | Yes | Path to logo file (PNG/SVG) |
| `primary_keywords` | list | Yes | 5-10 target keywords |
| `brand_colors` | dict | No | `{"primary": "#hex", "secondary": "#hex"}` |
| `competitor_urls` | list | No | Up to 3 competitor URLs |
| `output_format` | string | No | "docx" (default) or "pdf" |
| `output_dir` | string | No | Output directory path |

## Output

```json
{
  "overall_score": 72,
  "grade": "C",
  "component_scores": {
    "technical": {
      "score": 73,
      "max": 100,
      "weight": 0.30,
      "weighted_score": 21.9
    },
    "content": {
      "score": 68,
      "max": 100,
      "weight": 0.35,
      "weighted_score": 23.8
    },
    "ai_visibility": {
      "score": 52,
      "max": 100,
      "weight": 0.35,
      "weighted_score": 18.2
    }
  },
  "critical_issues": [
    {
      "component": "security",
      "description": "Missing HTTPS",
      "impact": "Site marked as insecure"
    }
  ],
  "quick_wins": [
    {
      "action": "Add Organization schema",
      "impact": "medium",
      "effort": "low"
    }
  ],
  "report": {
    "format": "docx",
    "output_path": "/path/to/Acme-SEO-Health-Report-2024-01-15.docx",
    "pages": 18
  },
  "audit_data": {
    "technical": { /* full technical audit results */ },
    "content": { /* full content audit results */ },
    "ai_visibility": { /* full AI audit results */ }
  }
}
```

## Customization

### Brand Colors

```python
report = generate_report(
    # ... other params ...
    brand_colors={
        "primary": "#1a73e8",    # Headers, highlights
        "secondary": "#34a853",  # Accents
        "text": "#202124",       # Body text
        "background": "#ffffff"  # Page background
    }
)
```

### Custom Template

```python
report = generate_report(
    # ... other params ...
    template_path="./custom_template.docx"
)
```

## Directory Structure

```
seo-health-report/
├── SKILL.md              # Claude Code skill definition
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── __init__.py          # Package init with generate_report()
├── scripts/
│   ├── __init__.py
│   ├── orchestrate.py       # Main workflow controller
│   ├── calculate_scores.py  # Composite scoring
│   ├── generate_summary.py  # Executive summary
│   ├── build_report.py      # Document assembly
│   └── apply_branding.py    # Branding application
├── references/
│   ├── report_structure.md  # Section specifications
│   ├── scoring_weights.md   # Weight rationale
│   └── writing_guide.md     # Tone guidelines
└── assets/
    ├── report_template.docx # Base template
    ├── cover_template.docx  # Cover page
    └── chart_styles.json    # Visualization specs
```

## Value Proposition

### What Makes This Different

| Component | Traditional SEO Audit | This System |
|-----------|----------------------|-------------|
| Technical | ✅ Standard | ✅ Comprehensive |
| Content | ✅ Basic | ✅ E-E-A-T focused |
| AI Visibility | ❌ Not offered | ✅ **Your differentiator** |
| Branded Output | Sometimes | ✅ Always professional |
| Actionable Plan | Variable | ✅ Prioritized |

### Typical Agency Pricing

| Component | Agency Cost |
|-----------|-------------|
| Technical SEO Audit | $2,000-5,000 |
| Content Strategy Audit | $2,000-4,000 |
| AI Visibility Analysis | **Not offered** |
| Branded Report | $1,000-2,000 |
| **Total** | $5,000-11,000 |

You're offering something agencies can't match.

## Error Handling

The report gracefully handles partial failures:

```python
# If one audit fails, others still run
report = generate_report(...)

if report.get("warnings"):
    for warning in report["warnings"]:
        print(f"Warning: {warning}")
```

## Command Line Usage

```bash
python -m seo_health_report \
    --url https://acme.com \
    --company "Acme Corporation" \
    --logo ./logo.png \
    --keywords "widgets,gadgets,solutions" \
    --output report.docx
```
