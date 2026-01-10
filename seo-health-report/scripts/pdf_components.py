"""
PDF Components

Reusable PDF components for report generation using ReportLab.
"""

import os
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def hex_to_reportlab_color(hex_str: str) -> colors.Color:
    """Convert hex color string to ReportLab Color (0-1 scale)."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        return colors.black
    try:
        r = int(hex_str[0:2], 16) / 255
        g = int(hex_str[2:4], 16) / 255
        b = int(hex_str[4:6], 16) / 255
        return colors.Color(r, g, b)
    except ValueError:
        return colors.black


def get_score_color(score: float, brand_colors: Dict[str, str] = None) -> colors.Color:
    """Get color for score value."""
    if score >= 80:
        hex_color = (brand_colors or {}).get("secondary", "#34a853")
    elif score >= 60:
        hex_color = (brand_colors or {}).get("warning", "#fbbc04")
    else:
        hex_color = (brand_colors or {}).get("danger", "#ea4335")
    return hex_to_reportlab_color(hex_color)


def create_cover_page(
    title: str,
    company_name: str,
    date: str,
    logo_path: Optional[str] = None,
    brand_colors: Optional[Dict[str, str]] = None
) -> List:
    """Create cover page flowables."""
    elements = []
    styles = getSampleStyleSheet()
    primary = hex_to_reportlab_color((brand_colors or {}).get("primary", "#1a73e8"))
    
    elements.append(Spacer(1, 1.5 * inch))
    
    # Logo
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=2 * inch, height=2 * inch)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.5 * inch))
        except (IOError, OSError) as e:
            print(f"Warning: Could not load logo '{logo_path}': {e}")
    
    # Title
    title_style = ParagraphStyle(
        'CoverTitle', parent=styles['Title'],
        fontSize=28, textColor=primary, alignment=TA_CENTER
    )
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Company name
    company_style = ParagraphStyle(
        'CompanyName', parent=styles['Heading1'],
        fontSize=20, alignment=TA_CENTER
    )
    elements.append(Paragraph(company_name, company_style))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Date
    date_style = ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER)
    elements.append(Paragraph(date, date_style))
    elements.append(PageBreak())
    
    return elements


def create_score_gauge(score: int, label: str, brand_colors: Optional[Dict[str, str]] = None) -> Drawing:
    """Create a score gauge visualization."""
    d = Drawing(200, 100)
    
    # Clamp score to valid range
    clamped_score = min(max(score, 0), 100)
    
    # Background arc (gray)
    d.add(Rect(10, 40, 180, 30, fillColor=colors.lightgrey, strokeColor=None))
    
    # Score bar (colored by score)
    score_color = get_score_color(clamped_score, brand_colors)
    bar_width = int(180 * clamped_score / 100)
    d.add(Rect(10, 40, bar_width, 30, fillColor=score_color, strokeColor=None))
    
    # Score text
    d.add(String(100, 80, f"{score}/100", fontSize=14, textAnchor='middle'))
    d.add(String(100, 20, label, fontSize=10, textAnchor='middle'))
    
    return d


def create_section_header(
    title: str,
    score: Optional[int] = None,
    brand_colors: Optional[Dict[str, str]] = None
) -> List:
    """Create section header with optional score."""
    elements = []
    styles = getSampleStyleSheet()
    primary = hex_to_reportlab_color((brand_colors or {}).get("primary", "#1a73e8"))
    
    header_style = ParagraphStyle(
        'SectionHeader', parent=styles['Heading1'],
        fontSize=16, textColor=primary, spaceAfter=12
    )
    
    if score is not None:
        title_text = f"{title} - Score: {score}/100"
    else:
        title_text = title
    
    elements.append(Paragraph(title_text, header_style))
    
    if score is not None:
        elements.append(create_score_gauge(score, title, brand_colors))
        elements.append(Spacer(1, 0.2 * inch))
    
    return elements


def create_findings_table(findings: List[str], brand_colors: Optional[Dict[str, str]] = None) -> Table:
    """Create a table of findings."""
    if not findings:
        findings = ["No findings to report"]
    
    data = [["Findings"]]
    for finding in findings[:10]:
        data.append([f"• {finding}"])
    
    primary = hex_to_reportlab_color((brand_colors or {}).get("primary", "#1a73e8"))
    
    table = Table(data, colWidths=[6 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    return table


def create_recommendations_list(
    recommendations: List[Dict[str, Any]],
    brand_colors: Optional[Dict[str, str]] = None
) -> List:
    """Create formatted recommendations list."""
    elements = []
    styles = getSampleStyleSheet()
    
    if not recommendations:
        elements.append(Paragraph("No recommendations at this time.", styles['Normal']))
        return elements
    
    for i, rec in enumerate(recommendations[:10], 1):
        priority = rec.get("priority", "medium").upper()
        action = rec.get("action", "")
        details = rec.get("details", "")
        
        rec_style = ParagraphStyle(
            f'Rec{i}', parent=styles['Normal'],
            fontSize=10, leftIndent=20, spaceAfter=8
        )
        
        text = f"<b>[{priority}]</b> {action}"
        if details:
            text += f"<br/><i>{details}</i>"
        
        elements.append(Paragraph(text, rec_style))
    
    return elements


def create_issues_table(issues: List[Dict[str, Any]], brand_colors: Optional[Dict[str, str]] = None) -> Table:
    """Create a table of issues with severity."""
    if not issues:
        return create_findings_table(["No critical issues found"], brand_colors)
    
    data = [["Severity", "Issue", "Recommendation"]]
    for issue in issues[:10]:
        severity = issue.get("severity", "medium").upper()
        desc = issue.get("description", "")[:50]
        rec = issue.get("recommendation", "")[:50]
        data.append([severity, desc, rec])
    
    primary = hex_to_reportlab_color((brand_colors or {}).get("primary", "#1a73e8"))
    
    table = Table(data, colWidths=[1 * inch, 2.5 * inch, 2.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    return table


__all__ = [
    'hex_to_reportlab_color',
    'get_score_color',
    'create_cover_page',
    'create_score_gauge',
    'create_section_header',
    'create_findings_table',
    'create_recommendations_list',
    'create_issues_table'
]
