---
name: premium-pdf-reports
description: Creates agency-quality PDF reports using ReportLab with professional layout, typography, and design patterns. Use when generating premium B2B reports, SEO audits, or professional documents that need to look like $10K+ deliverables.
---

# Premium PDF Report Generation

Creates professional, agency-quality PDF reports using ReportLab that rival $10K-$30K consulting deliverables.

## When to Use
- Generating SEO audit reports
- Creating B2B professional documents
- Building branded PDF reports with charts
- Any PDF that needs to look premium, not automated

## Core Principles

### 1. Typography Scale (Consistency is King)
```python
TYPOGRAPHY = {
    "h1": {"fontSize": 24, "leading": 28, "spaceAfter": 12},
    "h2": {"fontSize": 18, "leading": 22, "spaceAfter": 10},
    "h3": {"fontSize": 14, "leading": 18, "spaceAfter": 8},
    "body": {"fontSize": 11, "leading": 15, "spaceAfter": 6},
    "caption": {"fontSize": 9, "leading": 12, "spaceAfter": 4},
}
```

### 2. Use BaseDocTemplate (Not SimpleDocTemplate)
```python
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.pagesizes import letter

class PremiumReport(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, pagesize=letter, **kwargs)
        
        # Define frames for content area
        content_frame = Frame(
            0.75*inch, 0.75*inch,  # x, y from bottom-left
            7*inch, 9.5*inch,      # width, height
            id='content'
        )
        
        # Cover page template (no header/footer)
        cover_template = PageTemplate(
            id='cover',
            frames=[content_frame],
        )
        
        # Body template with header/footer
        body_template = PageTemplate(
            id='body',
            frames=[content_frame],
            onPage=self._add_header_footer,
        )
        
        self.addPageTemplates([cover_template, body_template])
    
    def _add_header_footer(self, canvas, doc):
        canvas.saveState()
        # Header line
        canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
        canvas.line(0.75*inch, 10.5*inch, 7.75*inch, 10.5*inch)
        
        # Footer with page number
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawString(0.75*inch, 0.5*inch, "Confidential")
        canvas.drawRightString(7.75*inch, 0.5*inch, f"Page {doc.page}")
        canvas.restoreState()
```

### 3. Reusable Components

#### Section Title
```python
def SectionTitle(text, number=None):
    """Premium section title with optional numbering."""
    prefix = f"{number}. " if number else ""
    return Paragraph(
        f'<font color="#1F2937" size="18"><b>{prefix}{text}</b></font>',
        ParagraphStyle('SectionTitle', spaceAfter=12, spaceBefore=20)
    )
```

#### KPI Card Row
```python
def KpiCardRow(kpis):
    """Row of KPI cards: [("Label", "Value", "trend"), ...]"""
    cards = []
    for label, value, trend in kpis:
        trend_color = "#10B981" if trend == "up" else "#EF4444" if trend == "down" else "#6B7280"
        cards.append([
            Paragraph(f'<font size="9" color="#6B7280">{label}</font>'),
            Paragraph(f'<font size="24" color="#1F2937"><b>{value}</b></font>'),
        ])
    
    table = Table([cards], colWidths=[1.5*inch] * len(kpis))
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    return table
```

#### Callout Box
```python
def CalloutBox(title, content, severity="info"):
    """Callout box with left accent bar."""
    colors_map = {
        "info": "#3B82F6",
        "warning": "#F59E0B",
        "success": "#10B981",
        "danger": "#EF4444",
    }
    accent_color = colors_map.get(severity, "#3B82F6")
    
    inner = Table([[
        Paragraph(f'<font color="{accent_color}"><b>{title}</b></font><br/>{content}')
    ]], colWidths=[6.5*inch])
    
    inner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEBEFORELEFT', (0, 0), (0, -1), 4, colors.HexColor(accent_color)),
    ]))
    return inner
```

#### Finding Block
```python
def FindingBlock(title, description, severity, evidence=None):
    """Issue/finding with severity indicator and optional evidence."""
    severity_colors = {
        "critical": "#DC2626",
        "high": "#EA580C",
        "medium": "#D97706",
        "low": "#65A30D",
    }
    color = severity_colors.get(severity, "#6B7280")
    
    elements = [
        Paragraph(f'<font color="{color}">●</font> <b>{title}</b>'),
        Paragraph(description, style=body_style),
    ]
    
    if evidence:
        evidence_text = "<br/>".join([f"• {e}" for e in evidence[:3]])
        elements.append(Paragraph(
            f'<font size="9" color="#6B7280">Evidence: {evidence_text}</font>'
        ))
    
    return elements
```

#### 30/60/90 Plan Table
```python
def PlanTable(tasks):
    """Professional action plan table.
    tasks: [{"task": str, "impact": str, "effort": str, "owner": str, "kpi": str, "timeline": str}]
    """
    data = [["Task", "Impact", "Effort", "Owner", "KPI", "Timeline"]]
    
    for task in tasks:
        data.append([
            Paragraph(task["task"], body_style),
            task["impact"],
            task["effort"],
            task["owner"],
            task["kpi"],
            task["timeline"],
        ])
    
    table = Table(data, colWidths=[2.2*inch, 0.7*inch, 0.7*inch, 0.8*inch, 1*inch, 0.8*inch])
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        # Body
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    return table
```

### 4. Chart Standards

```python
import matplotlib.pyplot as plt

def setup_chart_style():
    """Apply consistent chart styling."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.color': '#E5E7EB',
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    })

def save_chart(fig, path, dpi=200):
    """Save chart with consistent settings."""
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
```

### 5. Anti-Patterns to Avoid

❌ **DON'T:**
- Use emojis in B2B reports
- Use AI-generated header images (looks inconsistent)
- Scatter Spacer() calls throughout code
- Use default matplotlib styling
- Generate PDFs without page numbers
- Skip Table of Contents for 5+ page reports

✅ **DO:**
- Use deterministic, brand-safe headers
- Apply typography scale consistently
- Use reusable components
- Add narrative captions to charts
- Include evidence for findings
- Add methodology/data sources page

## Report Structure Template

```
1. Cover Page (1 page)
   - Company logo + name
   - Report title
   - Date + confidentiality notice

2. Executive Summary (1 page)
   - Verdict headline
   - 3 biggest issues (bullets)
   - 3 quick wins (bullets)
   - 90-day outcome projection

3. Scorecard (1 page)
   - KPI cards row
   - Score gauge or bar chart
   - Benchmark comparison

4. Top Findings (2-4 pages)
   - Prioritized by impact
   - Each with severity, description, evidence, recommendation

5. 30/60/90 Plan (1-2 pages)
   - Plan table with all columns
   - Top 5 priorities callout

6. Appendix (optional)
   - Methodology
   - Data sources
   - Raw tables
```

## Quick Start

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.lib import colors

# 1. Create document
doc = PremiumReport("output.pdf")

# 2. Build story
story = []

# Cover page
story.append(CoverPage(company_name, report_title, date))
story.append(PageBreak())

# Switch to body template
story.append(NextPageTemplate('body'))

# Executive summary
story.append(SectionTitle("Executive Summary", 1))
story.append(CalloutBox("Key Finding", "Your site is invisible to AI assistants.", "warning"))
story.append(Spacer(1, 12))

# Build rest of report...

# 3. Generate
doc.build(story)
```
