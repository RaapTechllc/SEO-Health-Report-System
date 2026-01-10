# Feature: Add PDF Export Support

The following plan should be complete, but validate documentation and codebase patterns before implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files.

## Feature Description

Implement native PDF export for SEO health reports using ReportLab. Currently `generate_pdf()` in `build_report.py` falls back to markdown. This feature adds proper PDF generation with branded styling, charts, and professional formatting.

## User Story

As a **SEO consultant**
I want to **export reports as PDF files**
So that **I can deliver professional, print-ready documents to clients**

## Problem Statement

The current `generate_pdf()` function is a stub that falls back to markdown output. Clients expect professional PDF reports with proper branding, visual score gauges, and formatted sections.

## Solution Statement

Implement PDF generation using ReportLab's Platypus framework for document flow. Create reusable components for cover pages, score gauges, section headers, and tables that match the existing DOCX structure.

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Medium
**Primary Systems Affected**: `seo-health-report/scripts/build_report.py`
**Dependencies**: `reportlab>=4.0.0`

---

## CONTEXT REFERENCES

### Relevant Codebase Files - READ BEFORE IMPLEMENTING

- `seo-health-report/scripts/build_report.py` (lines 1-350) - Why: Contains `generate_pdf()` stub and section structure to mirror
- `seo-health-report/scripts/apply_branding.py` (lines 1-50) - Why: `DEFAULT_COLORS` dict and `parse_hex_color()` pattern
- `seo-health-report/scripts/generate_summary.py` (lines 100-130) - Why: `generate_score_gauge_data()` for chart data structure
- `seo-health-report/__init__.py` (lines 60-90) - Why: Report generation flow and branding application

### New Files to Create

- `seo-health-report/scripts/pdf_components.py` - Reusable PDF components (cover, gauge, tables)

### Files to Update

- `seo-health-report/scripts/build_report.py` - Replace `generate_pdf()` stub
- `seo-health-report/requirements.txt` - Add reportlab dependency

### Relevant Documentation

- [ReportLab Platypus Guide](https://docs.reportlab.com/reportlab/userguide/ch5_platypus/)
  - Section: Flowables and document templates
  - Why: Core pattern for building multi-page documents
- [ReportLab Graphics](https://docs.reportlab.com/reportlab/userguide/ch11_graphics/)
  - Section: Drawing shapes and charts
  - Why: Needed for score gauge visualization

### Patterns to Follow

**Color Handling** (from `apply_branding.py`):
```python
DEFAULT_COLORS = {
    "primary": "#1a73e8",
    "secondary": "#34a853",
    "warning": "#fbbc04",
    "danger": "#ea4335",
}
```

**Section Structure** (from `build_report.py`):
```python
sections.append({
    "type": "cover",
    "content": {"title": "...", "company_name": "...", "logo": logo_file}
})
```

**Score Color Logic** (from `generate_summary.py`):
```python
if score >= 80: color = "#34a853"  # Green
elif score >= 60: color = "#fbbc04"  # Yellow
else: color = "#ea4335"  # Red
```

---

## IMPLEMENTATION PLAN

### Prerequisites Gate

- [ ] `pip install reportlab>=4.0.0`
- [ ] Verify Pillow installed (for logo handling)
- [ ] Test imports: `from reportlab.platypus import SimpleDocTemplate`

### Phase 1: Foundation

Create PDF component library with reusable flowables.

### Phase 2: Core Implementation

Implement `generate_pdf()` using Platypus document template.

### Phase 3: Integration

Wire into existing `build_report_document()` flow.

### Phase 4: Testing

Manual validation with sample reports.

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `seo-health-report/requirements.txt`

- **IMPLEMENT**: Add reportlab dependency
- **ADD**: `reportlab>=4.0.0` after Pillow line
- **VALIDATE**: `pip install -r seo-health-report/requirements.txt`

### Task 2: CREATE `seo-health-report/scripts/pdf_components.py`

- **IMPLEMENT**: Reusable PDF components
- **PATTERN**: Follow `apply_branding.py` color handling
- **IMPORTS**:
  ```python
  from reportlab.lib import colors
  from reportlab.lib.pagesizes import letter, A4
  from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
  from reportlab.lib.units import inch
  from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, PageBreak
  from reportlab.graphics.shapes import Drawing, Rect, String
  from reportlab.graphics.charts.piecharts import Pie
  ```
- **COMPONENTS TO CREATE**:
  1. `create_cover_page(title, company_name, date, logo_path, colors)` → List[Flowable]
  2. `create_score_gauge(score, label, colors)` → Drawing
  3. `create_section_header(title, score, colors)` → List[Flowable]
  4. `create_findings_table(findings, colors)` → Table
  5. `create_recommendations_list(recommendations, colors)` → List[Flowable]
  6. `hex_to_reportlab_color(hex_str)` → colors.Color
- **GOTCHA**: ReportLab uses RGB 0-1 scale, not 0-255
- **VALIDATE**: `python -c "from seo_health_report.scripts.pdf_components import create_cover_page"`

### Task 3: UPDATE `seo-health-report/scripts/build_report.py`

- **IMPLEMENT**: Replace `generate_pdf()` stub with real implementation
- **PATTERN**: Mirror `generate_docx()` section iteration
- **IMPORTS**: Add `from .pdf_components import *`
- **STRUCTURE**:
  ```python
  def generate_pdf(sections, output_path, brand_colors=None):
      from reportlab.platypus import SimpleDocTemplate
      from .pdf_components import (
          create_cover_page, create_section_header,
          create_findings_table, create_score_gauge
      )
      
      doc = SimpleDocTemplate(output_path, pagesize=letter)
      story = []
      
      for section in sections:
          # Build flowables per section type
          ...
      
      doc.build(story)
      return True
  ```
- **GOTCHA**: Handle missing logo gracefully (check `os.path.exists`)
- **VALIDATE**: `python -c "from seo_health_report.scripts.build_report import generate_pdf"`

### Task 4: UPDATE `__all__` exports

- **IMPLEMENT**: Add pdf_components exports to `scripts/__init__.py`
- **VALIDATE**: `python -c "from seo_health_report.scripts import create_cover_page"`

---

## TESTING STRATEGY

### Unit Tests

Not required per project standards (no existing test suite).

### Manual Validation

1. Generate a test report with PDF format
2. Verify cover page renders with logo
3. Verify score gauges display correctly
4. Verify all sections present
5. Check color branding applied

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style

```bash
cd "/mnt/e/claude code projects/seo-health-report"
python -m py_compile seo-health-report/scripts/pdf_components.py
python -m py_compile seo-health-report/scripts/build_report.py
```

### Level 2: Import Tests

```bash
python -c "from seo_health_report.scripts.pdf_components import create_cover_page, create_score_gauge"
python -c "from seo_health_report.scripts.build_report import generate_pdf"
```

### Level 3: Integration Test

```bash
python -c "
from seo_health_report import generate_report
result = generate_report(
    target_url='https://example.com',
    company_name='Test Corp',
    logo_file='',
    primary_keywords=['test'],
    output_format='pdf',
    output_dir='/tmp'
)
print(f'PDF generated: {result[\"report\"][\"output_path\"]}')
"
```

### Level 4: Manual Validation

1. Open generated PDF in viewer
2. Verify all 7 sections present
3. Check branding colors applied
4. Verify no rendering errors

---

## ACCEPTANCE CRITERIA

- [ ] `generate_pdf()` produces valid PDF file (not markdown fallback)
- [ ] Cover page includes logo (when provided) and company name
- [ ] Score gauges render with correct colors (green/yellow/red)
- [ ] All 7 report sections present in PDF
- [ ] Brand colors applied to headers
- [ ] PDF opens without errors in standard viewers
- [ ] Graceful handling when logo file missing

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each validation command passes
- [ ] PDF renders correctly in viewer
- [ ] No import errors
- [ ] Existing DOCX/MD generation still works

---

## NOTES

**Design Decision**: Using Platypus (high-level) over Canvas (low-level) for maintainability and automatic page breaks.

**Trade-off**: ReportLab produces larger files than some alternatives but offers best Python-native control.

**Future Enhancement**: Could add chart.js-style visualizations using reportlab.graphics.
