#!/usr/bin/env python3
"""
Generate FREE Tier Report (1-Page Lead Magnet)

Quick wins report to generate leads and show value.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "seo-health-report"))

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_free_tier_report(
    audit_data: Dict[str, Any],
    company_name: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Generate 1-page FREE tier report.
    
    Args:
        audit_data: Full audit results
        company_name: Company name
        output_path: Where to save PDF
    
    Returns:
        Dict with success status and path
    """
    
    # Extract key data
    score = audit_data.get('overall_score', 0)
    grade = audit_data.get('grade', 'F')
    quick_wins = audit_data.get('quick_wins', [])[:3]
    critical_issues = audit_data.get('critical_issues', [])[:2]
    
    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    score_style = ParagraphStyle(
        'ScoreStyle',
        parent=styles['Normal'],
        fontSize=48,
        textColor=colors.HexColor('#34a853') if score >= 70 else colors.HexColor('#ea4335'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    # Title
    story.append(Paragraph(f"SEO Health Report: {company_name}", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Score card
    story.append(Paragraph(f"Grade: {grade}", score_style))
    story.append(Paragraph(f"{score}/100", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Quick wins
    story.append(Paragraph("<b>Top 3 Quick Wins</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    for i, win in enumerate(quick_wins, 1):
        action = win.get('action', 'Improve SEO')
        story.append(Paragraph(f"{i}. {action}", styles['Normal']))
        story.append(Spacer(1, 0.05*inch))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Critical issues
    if critical_issues:
        story.append(Paragraph("<b>Critical Issues</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        for issue in critical_issues:
            desc = issue.get('description', 'Issue found')
            story.append(Paragraph(f"• {desc}", styles['Normal']))
            story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    # CTA
    cta_style = ParagraphStyle(
        'CTA',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#1a73e8'),
        alignment=TA_CENTER,
        spaceAfter=10,
        borderWidth=2,
        borderColor=colors.HexColor('#1a73e8'),
        borderPadding=10
    )
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "<b>Want the Full 30-Page Audit?</b><br/>"
        "Upgrade to BASIC for $800<br/>"
        "Includes: Technical audit, AI visibility, and implementation roadmap",
        cta_style
    ))
    
    # Build PDF
    doc.build(story)
    
    return {
        "success": True,
        "output_path": output_path,
        "tier": "FREE",
        "pages": 1
    }


def main():
    """CLI for generating FREE tier reports."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Generate FREE tier 1-page report")
    parser.add_argument("--audit-json", required=True, help="Path to audit JSON file")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--output", default="free_report.pdf", help="Output PDF path")
    
    args = parser.parse_args()
    
    # Load audit data
    with open(args.audit_json) as f:
        audit_data = json.load(f)
    
    # Generate report
    result = generate_free_tier_report(
        audit_data=audit_data,
        company_name=args.company,
        output_path=args.output
    )
    
    if result['success']:
        print(f"✅ FREE tier report generated: {result['output_path']}")
    else:
        print(f"❌ Failed to generate report")
        sys.exit(1)


if __name__ == "__main__":
    main()
