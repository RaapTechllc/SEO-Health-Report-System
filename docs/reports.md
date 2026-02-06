# Report Generation and Download

This document explains how SEO Health Reports are generated and retrieved.

## Report Types

### HTML Reports
- Interactive, browser-viewable format
- Responsive design for desktop and mobile
- Color-coded score indicators
- Generated automatically for all completed audits

### PDF Reports
- Printable, shareable format
- Professional branding
- Executive summary
- Available for Pro and Enterprise tiers

## Report Generation Process

### 1. Audit Completion Trigger

When an audit completes, the report generator is invoked:

```python
# In apps/worker/handlers/full_audit.py
await write_progress_event(
    db, audit_id, job_id,
    ProgressStage.GENERATING_REPORT, 80,
    "Generating audit report"
)

html_path = await generate_html_report_simple(audit_result, raw_result, tenant_id)
audit_result.report_path = html_path
```

### 2. HTML Report Structure

Reports include:
- **Header**: Company name, URL, generation date
- **Overall Score**: Large numeric display with letter grade
- **Component Scores**: Technical, Content, AI Visibility breakdown
- **Issues List**: Prioritized by severity (critical → low)
- **Recommendations**: Actionable improvement steps
- **Detailed Findings**: Per-component analysis

### 3. Scoring Display

```html
<div class="section">
    <h3>Overall Score</h3>
    <span class="score">74</span>
    <span class="grade grade-C">C</span>
</div>

<div class="section">
    <h3>Component Scores</h3>
    <div class="component">
        <strong>Technical</strong><br>85
    </div>
    <div class="component">
        <strong>Content</strong><br>72
    </div>
    <div class="component">
        <strong>AI Visibility</strong><br>68
    </div>
</div>
```

## Storage Location

Reports are stored in a tenant-organized directory structure:

```
reports/
├── {tenant_id}/
│   ├── {audit_id}.html
│   ├── {audit_id}.pdf
│   └── {audit_id}.json
└── default/
    └── ...
```

Example paths:
- `reports/tenant_abc123/aud_xyz789.html`
- `reports/default/aud_xyz789.html`

## API Endpoints

### Get HTML Report

```http
GET /audits/{audit_id}/report/html
```

**Response:** HTML file download

**Headers:**
```
Content-Type: text/html
Content-Disposition: attachment; filename="SEO_Report_{audit_id}.html"
```

### Get PDF Report

```http
GET /audits/{audit_id}/report/pdf
```

**Response:** PDF file download

**Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="SEO_Report_{audit_id}.pdf"
```

### Legacy PDF Endpoint

```http
GET /audit/{audit_id}/pdf
```

Generates PDF on-demand if not already cached.

### Get Full Audit Data

```http
GET /audit/{audit_id}/full
```

**Response includes report URLs:**
```json
{
  "audit_id": "aud_abc123",
  "status": "completed",
  "overall_score": 74,
  "grade": "C",
  "report_html_url": "/audits/aud_abc123/report/html",
  "report_pdf_url": "/audits/aud_abc123/report/pdf",
  "result": { ... }
}
```

## Report Content

### Overall Score Section
- Numeric score (0-100)
- Letter grade (A-F)
- Grade color coding:
  - A: Green (#22c55e)
  - B: Lime (#84cc16)
  - C: Yellow (#eab308)
  - D: Orange (#f97316)
  - F: Red (#ef4444)

### Component Scores
Each component displays:
- Score value
- Weight percentage
- Issues count
- Key findings

### Issues Section
Issues are sorted by severity:
```json
{
  "description": "Missing meta description on 15 pages",
  "severity": "high",
  "source": "technical",
  "category": "on-page-seo",
  "url": "https://example.com/page"
}
```

### Recommendations Section
Prioritized action items:
```json
{
  "action": "Add unique meta descriptions to all pages",
  "priority": "high",
  "impact": "high",
  "effort": "low",
  "category": "quick-win"
}
```

## Branding and Customization

### Default Branding
- RaapTech logo and colors
- Standard report template

### Enterprise Customization
Enterprise tier supports:
- Custom logo upload
- Brand color palette
- Custom footer text
- White-label option

### Template Structure
```
packages/seo_health_report/templates/
├── report_base.html
├── report_premium.html
└── components/
    ├── header.html
    ├── score_card.html
    └── recommendations.html
```

## Error Handling

### Report Not Found
```http
GET /audits/{audit_id}/report/html

Response: 404 Not Found
{
  "detail": "HTML report not available"
}
```

### Audit Not Completed
```http
GET /audit/{audit_id}/pdf

Response: 400 Bad Request
{
  "detail": "Audit status: running"
}
```

## Caching

- HTML reports are generated once and cached
- PDF reports may be generated on-demand (first request)
- Reports persist until audit is deleted
