#!/usr/bin/env python3
"""
One-Pager Executive Summary Generator
Target: Sheet Metal Werks
"""

import json
import os
import sys
from datetime import datetime
from io import BytesIO

# Matplotlib for better charts
import matplotlib.pyplot as plt
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def create_one_pager(json_path, output_pdf, logo_path=None):
    # 1. Load Data
    with open(json_path) as f:
        data = json.load(f)

    company_name = data.get("company_name", "Company")

    # Extract Scores
    tech_score = data["audits"]["technical"]["score"]
    content_score = data["audits"]["content"]["score"]
    ai_score = data["audits"]["ai_visibility"]["score"]
    overall_score = int((tech_score + content_score + ai_score) / 3)

    # Extract Issues & Recommendations
    # Flatten issues from all sources
    all_issues = []

    # Technical Issues
    if data["audits"]["technical"].get("components"):
         for _comp_name, comp_data in data["audits"]["technical"]["components"].items():
             if "issues" in comp_data:
                 for issue in comp_data["issues"]:
                     if isinstance(issue, str): # Handle string issues
                         all_issues.append({"description": issue, "severity": "medium", "type": "Technical"})
                     else:
                         issue["type"] = "Technical"
                         all_issues.append(issue)

    # AI Issues
    if data["audits"]["ai_visibility"].get("recommendations"):
        for rec in data["audits"]["ai_visibility"]["recommendations"]:
             all_issues.append({"description": rec, "severity": "high", "type": "AI Visibility"})

    # Sort by severity (Critical > High > Medium)
    def severity_rank(i):
        sev = i.get("severity", "medium").lower()
        if sev == "critical": return 0
        if sev == "high": return 1
        return 2

    sorted_issues = sorted(all_issues, key=severity_rank)
    top_priorities = sorted_issues[:5]


    # 2. Setup PDF output
    doc = SimpleDocTemplate(output_pdf, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=HexColor("#102A43"))
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14, textColor=HexColor("#334E68"))
    score_style = ParagraphStyle('Score', fontSize=28, alignment=1, textColor=HexColor("#102A43"), fontName="Helvetica-Bold")
    label_style = ParagraphStyle('Label', fontSize=10, alignment=1, textColor=HexColor("#627D98"))
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=16, spaceBefore=15, spaceAfter=10, textColor=HexColor("#102A43"), borderPadding=5, borderColor=HexColor("#E1E8EF"), borderWidth=0, borderBottomWidth=1)

    item_style = ParagraphStyle('Item', fontSize=10, leading=14, spaceAfter=6)

    # Header Section
    header_data = []
    if os.path.exists(logo_path):
        img = Image(logo_path, width=1.5*inch, height=1.5*inch)
        img.hAlign = 'LEFT'
        header_text = [
            Paragraph(f"<b>{company_name}</b>", title_style),
            Paragraph("Executive Digital Health Scorecard", subtitle_style),
            Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal'])
        ]
        header_data = [[img, header_text]]
    else:
        header_text = [
            Paragraph(f"<b>{company_name}</b>", title_style),
            Paragraph("Executive Digital Health Scorecard", subtitle_style),
             Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal'])
        ]
        header_data = [[header_text]]

    story.append(Table(header_data, colWidths=[2*inch, 4.5*inch]))
    story.append(Spacer(1, 20))

    # Scorecard Section
    def get_color(score):
        if score >= 80: return HexColor("#38A169") # Green
        if score >= 60: return HexColor("#D69E2E") # Yellow
        return HexColor("#E53E3E") # Red

    score_data = [
        [
            Paragraph(f"<font color='{get_color(overall_score)}'>{overall_score}</font>", score_style),
            Paragraph(f"<font color='{get_color(tech_score)}'>{tech_score}</font>", score_style),
            Paragraph(f"<font color='{get_color(content_score)}'>{content_score}</font>", score_style),
            Paragraph(f"<font color='{get_color(ai_score)}'>{ai_score}</font>", score_style),
        ],
        [
            Paragraph("OVERALL HEALTH", label_style),
            Paragraph("TECHNICAL SEO", label_style),
            Paragraph("CONTENT DEPTH", label_style),
            Paragraph("AI VISIBILITY", label_style),
        ]
    ]

    t = Table(score_data, colWidths=[1.75*inch]*4)
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, HexColor("#E1E8EF")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, HexColor("#E1E8EF")),
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#F0F4F8")),
        ('PADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Chart Section (Client vs Competitors Context)
    # Since we might not have deep competitor data in this JSON run, we will visualize the 3 components breakdown

    story.append(Paragraph("Performance Breakdown", section_style))

    # Create a nice matplotlib chart
    plt.figure(figsize=(8, 3))
    categories = ['Technical SEO', 'Content Depth', 'AI Visibility']
    values = [tech_score, content_score, ai_score]
    colors_list = ['#3182CE', '#805AD5', '#D53F8C'] # Blue, Purple, Pink

    plt.barh(categories, values, color=colors_list, height=0.5)
    plt.xlim(0, 100)
    plt.axvline(x=60, color='orange', linestyle='--', alpha=0.5, label='Warning Line')
    plt.axvline(x=80, color='green', linestyle='--', alpha=0.5, label='Excellence Line')

    # Add values to bars
    for i, v in enumerate(values):
        plt.text(v + 1, i, str(v), color='black', fontweight='bold', va='center')

    plt.title('Component Performance Analysis', pad=10)
    plt.tight_layout()

    # Save chart to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=300)
    plt.close()
    buf.seek(0)
    story.append(Image(buf, width=7*inch, height=3*inch))
    story.append(Spacer(1, 10))

    # Priority Items Section
    story.append(Paragraph("🚨 Top Priority Actions", section_style))

    action_data = []
    for item in top_priorities:
        desc = item.get("description")
        rec = item.get("recommendation", "Review and fix immediately.")
        # Clean up text
        if isinstance(desc, str):
            clean_desc = desc
        else:
            clean_desc = str(desc)

        action_data.append([
            Paragraph("🔴", styles['Normal']),
            Paragraph(f"<b>{item.get('type', 'General')}:</b> {clean_desc}<br/><font color='#555'><i>Recommendation: {rec}</i></font>", item_style)
        ])

    if not action_data:
        action_data.append([Paragraph("✅", styles['Normal']), Paragraph("No critical issues found. Great job!", item_style)])

    t_actions = Table(action_data, colWidths=[0.4*inch, 6.6*inch])
    t_actions.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_actions)

    story.append(Spacer(1, 15))

    # Business Impact / Commercial Focus Note
    story.append(Paragraph("💼 Commercial & Data Center Impact", section_style))
    impact_text = """
    This audit specifically targeted high-value commercial keywords (e.g., 'Data Center cooling ductwork').
    <b>AI Visibility Score ({ai_score}/100)</b> indicates how well you show up when engineers ask AI about these topics.
    """
    if ai_score < 60:
        impact_text += "Currently, AI engines (Claude, ChatGPT, Perplexity) do NOT strongly associate your brand with these terms. Increasing technical content and schema around 'Data Center' capabilities is critical."
    else:
        impact_text += "You have a solid foundation. Continue publishing technical case studies to maintain this lead."

    story.append(Paragraph(impact_text, item_style))

    # Build PDF
    doc.build(story)
    print(f"✅ One-Pager generated: {output_pdf}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_one_pager.py <json_file>")
        sys.exit(1)

    json_input = sys.argv[1]
    pdf_output = json_input.replace(".json", "_ONE_PAGER.pdf")

    create_one_pager(json_input, pdf_output)
