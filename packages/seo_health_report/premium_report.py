#!/usr/bin/env python3
"""
Premium PDF Report Generator (Refactored)

Agency-quality SEO health reports using modular components.
NO emojis - professional B2B output.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from . import charts
from .human_copy import clean_ai_copy
from .pdf_components import (
    CalloutBox,
    FindingBlock,
    KpiCardRow,
    PlanTable,
    PriorityCallout,
    ReportColors,
    SectionTitle,
    get_report_styles,
)
from .pdf_layout import PremiumReportDoc, switch_to_body_template

# Unified table header color for consistency
TABLE_HEADER_COLOR = colors.HexColor("#1F2937")


def markdown_to_reportlab(text: str) -> str:
    """Convert markdown bold/lists to ReportLab XML tags."""
    if not text:
        return ""
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # Convert numbered lists like "1. **Item**" to proper format
    text = re.sub(r'^\d+\.\s+', '• ', text, flags=re.MULTILINE)
    return text


class PremiumReportGenerator:
    """Generates agency-quality PDF reports."""

    def __init__(self, data: dict, output_path: str):
        """Initialize report generator."""
        self.data = data
        self.output_path = output_path
        self.company_name = data.get("company_name", "Company")
        self.url = data.get("url", "")

        # Setup output directories
        self.charts_dir = Path(output_path).parent / "charts"
        self.charts_dir.mkdir(exist_ok=True)

        # Initialize styles
        self.styles = get_report_styles()

        # Story (list of flowables)
        self.story = []

    def _add_cover_page(self):
        """Add professional cover page."""
        company = self.company_name
        url = self.url
        date = datetime.now().strftime("%B %d, %Y")
        score = self.data.get("overall_score", 0) or 0
        grade = self.data.get("grade", "F")

        self.story.append(Spacer(1, 1.5*inch))

        # Title with proper spacing
        title_style = ParagraphStyle(
            "CoverTitle",
            fontSize=36,
            leading=42,
            textColor=ReportColors.info,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=12,
        )
        self.story.append(Paragraph("SEO Health Report", title_style))

        # Subtitle
        subtitle_style = ParagraphStyle(
            "Subtitle",
            fontSize=14,
            leading=18,
            textColor=ReportColors.text_muted,
            alignment=TA_CENTER,
            spaceAfter=40,
        )
        self.story.append(Paragraph("Comprehensive Website Analysis", subtitle_style))

        # Company name
        company_style = ParagraphStyle(
            "CompanyName",
            fontSize=24,
            leading=28,
            textColor=ReportColors.text_primary,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=8,
        )
        self.story.append(Paragraph(company, company_style))

        # URL
        url_style = ParagraphStyle(
            "URL",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=ReportColors.info,
            spaceAfter=30,
        )
        self.story.append(Paragraph(url, url_style))

        # Score display - explicit styles with proper leading
        score_color = ReportColors.grade(grade)

        score_num_style = ParagraphStyle(
            "ScoreNum",
            fontSize=56,
            leading=60,
            alignment=TA_CENTER,
            textColor=score_color,
            fontName="Helvetica-Bold",
            spaceAfter=0,
        )
        self.story.append(Paragraph(str(score), score_num_style))

        out_of_style = ParagraphStyle(
            "OutOf",
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=ReportColors.text_muted,
            spaceBefore=0,
            spaceAfter=8,
        )
        self.story.append(Paragraph("out of 100", out_of_style))

        grade_disp_style = ParagraphStyle(
            "GradeDisp",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=score_color,
            fontName="Helvetica-Bold",
            spaceAfter=20,
        )
        self.story.append(Paragraph(f"Grade: {grade}", grade_disp_style))

        self.story.append(Spacer(1, 0.5*inch))

        # Date
        info_style = ParagraphStyle(
            "Info",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=ReportColors.text_muted,
            spaceAfter=40,
        )
        self.story.append(Paragraph(f"Report Date: {date}", info_style))

        # Prepared by
        prepared_style = ParagraphStyle(
            "Prepared",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=ReportColors.text_secondary,
            spaceAfter=4,
        )
        self.story.append(Paragraph("Prepared by", prepared_style))

        brand_style = ParagraphStyle(
            "Brand",
            fontSize=14,
            leading=18,
            textColor=ReportColors.info,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        self.story.append(Paragraph("RaapTech SEO Intelligence", brand_style))

        contact_style = ParagraphStyle(
            "Contact",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=ReportColors.text_muted,
        )
        self.story.append(Paragraph("www.raaptech.com", contact_style))

        self.story.append(PageBreak())
        self.story.append(switch_to_body_template())

    def _add_table_of_contents(self):
        """Add table of contents."""
        self.story.append(SectionTitle("Table of Contents"))
        self.story.append(Spacer(1, 0.3*inch))

        has_market_intel = "market_intelligence" in self.data

        if has_market_intel:
            toc_items = [
                ("1. Executive Summary", "Key findings and overall assessment"),
                ("2. Score Breakdown", "Component scores and methodology"),
                ("3. Market Position", "Competitive standing analysis"),
                ("4. Technical SEO", "Site structure, speed, security"),
                ("5. Content & Authority", "Content quality and E-E-A-T"),
                ("6. AI Visibility", "Presence in AI-generated responses"),
                ("7. Action Plan", "30/60/90-day prioritized tasks"),
            ]
        else:
            toc_items = [
                ("1. Executive Summary", "Key findings and overall assessment"),
                ("2. Score Breakdown", "Component scores and methodology"),
                ("3. Technical SEO", "Site structure, speed, security"),
                ("4. Content & Authority", "Content quality and E-E-A-T"),
                ("5. AI Visibility", "Presence in AI-generated responses"),
                ("6. Action Plan", "30/60/90-day prioritized tasks"),
            ]

        toc_style = ParagraphStyle(
            "TOC",
            fontSize=12,
            leading=16,
            spaceAfter=2,
            leftIndent=20,
            textColor=ReportColors.text_primary,
        )
        toc_desc_style = ParagraphStyle(
            "TOCDesc",
            fontSize=10,
            leading=14,
            textColor=ReportColors.text_muted,
            leftIndent=40,
            spaceAfter=12,
        )

        for title, desc in toc_items:
            self.story.append(Paragraph(f"<b>{title}</b>", toc_style))
            self.story.append(Paragraph(desc, toc_desc_style))

        self.story.append(PageBreak())

    def _add_executive_summary(self):
        """Add executive summary section."""
        self.story.append(SectionTitle("Executive Summary", number=1))

        score = self.data.get("overall_score", 0) or 0
        grade = self.data.get("grade", "F")
        tech_score = self.data.get("audits", {}).get("technical", {}).get("score", 0) or 0
        content_score = self.data.get("audits", {}).get("content", {}).get("score", 0) or 0
        ai_score = self.data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0

        # KPI Cards row
        kpis = [
            ("Overall", str(score), "neutral"),
            ("Technical", str(tech_score), "up" if tech_score >= 70 else "down"),
            ("Content", str(content_score), "up" if content_score >= 70 else "down"),
            ("AI Visibility", str(ai_score), "up" if ai_score >= 50 else "down"),
        ]
        self.story.append(KpiCardRow(kpis))
        self.story.append(Spacer(1, 0.25*inch))

        # Score gauge chart
        gauge_path = str(self.charts_dir / "score_gauge.png")
        charts.create_score_gauge(score, grade, self.company_name, gauge_path)
        if os.path.exists(gauge_path):
            img = Image(gauge_path, width=3.5*inch, height=2.4*inch)
            img.hAlign = 'CENTER'
            self.story.append(img)

        self.story.append(Spacer(1, 0.2*inch))

        # Component bars chart
        bars_path = str(self.charts_dir / "component_bars.png")
        charts.create_component_bars(tech_score, content_score, ai_score, bars_path)
        if os.path.exists(bars_path):
            img = Image(bars_path, width=5.5*inch, height=2*inch)
            img.hAlign = 'CENTER'
            self.story.append(img)

        self.story.append(Spacer(1, 0.25*inch))

        # Executive summary text - convert markdown to proper formatting
        exec_summary = self.data.get("executive_summary", "")
        if exec_summary:
            clean_summary = clean_ai_copy(exec_summary)
            # Convert markdown to ReportLab
            formatted_summary = markdown_to_reportlab(clean_summary)
            self.story.append(CalloutBox("Key Assessment", formatted_summary, "info"))

        # Quick wins
        quick_wins = self.data.get("quick_wins", [])
        if quick_wins:
            self.story.append(Spacer(1, 0.2*inch))
            self.story.append(Paragraph("<b>Quick Wins (High Impact, Low Effort)</b>", self.styles["SubSection"]))
            for win in quick_wins[:5]:
                clean_win = clean_ai_copy(win)
                # Remove any emoji-like characters
                clean_win = re.sub(r'[^\x00-\x7F]+', '', clean_win).strip()
                if clean_win:
                    self.story.append(Paragraph(f"• {clean_win}", self.styles["Finding"]))

        self.story.append(PageBreak())

    def _add_score_breakdown(self):
        """Add score breakdown and methodology section."""
        self.story.append(SectionTitle("Score Breakdown", number=2))

        intro = ("The SEO Health Score combines three key areas, weighted by their "
                "impact on modern search visibility. AI Visibility receives higher weight (35%) "
                "because AI-powered search is rapidly changing how customers discover businesses.")
        self.story.append(Paragraph(intro, self.styles["BodyText"]))
        self.story.append(Spacer(1, 0.2*inch))

        # Methodology table - full width
        method_data = [
            ["Component", "Weight", "What We Measure"],
            ["Technical SEO", "30%", "Crawlability, speed, security, mobile, structured data"],
            ["Content & Authority", "35%", "Content quality, E-E-A-T, keywords, backlinks"],
            ["AI Visibility", "35%", "Presence in ChatGPT, Claude, Perplexity responses"],
        ]

        method_table = Table(method_data, colWidths=[2*inch, 1*inch, 4*inch])
        method_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, ReportColors.border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ReportColors.background]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        self.story.append(method_table)
        self.story.append(Spacer(1, 0.3*inch))

        # Grade scale
        self.story.append(Paragraph("<b>Grade Scale</b>", self.styles["SubSection"]))
        self.story.append(Spacer(1, 0.1*inch))

        grade_data = [
            ["Grade", "Score", "Interpretation"],
            ["A", "90-100", "Excellent - Industry leader"],
            ["B", "80-89", "Good - Above average"],
            ["C", "70-79", "Average - Room for improvement"],
            ["D", "60-69", "Below Average - Significant gaps"],
            ["F", "0-59", "Poor - Urgent attention needed"],
        ]

        grade_table = Table(grade_data, colWidths=[1*inch, 1.2*inch, 4.8*inch])
        grade_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, ReportColors.border),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            # Grade colors
            ("TEXTCOLOR", (0, 1), (0, 1), ReportColors.grade("A")),
            ("TEXTCOLOR", (0, 2), (0, 2), ReportColors.grade("B")),
            ("TEXTCOLOR", (0, 3), (0, 3), ReportColors.grade("C")),
            ("TEXTCOLOR", (0, 4), (0, 4), ReportColors.grade("D")),
            ("TEXTCOLOR", (0, 5), (0, 5), ReportColors.grade("F")),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ]))
        self.story.append(grade_table)

        self.story.append(PageBreak())

    def _add_market_position_section(self):
        """Add market position analysis section."""
        market_intel = self.data.get("market_intelligence", {})
        if not market_intel:
            return

        self.story.append(SectionTitle("Market Position", number=3))

        classification = market_intel.get("classification", {})
        benchmark = market_intel.get("benchmark", {})
        landscape = market_intel.get("market_landscape", {})

        # Industry classification
        industry = classification.get("industry", "Unknown")
        vertical = classification.get("vertical", "Unknown")
        niche = classification.get("niche", "Unknown")

        class_text = f"<b>Industry:</b> {industry} > {vertical} > {niche}"
        self.story.append(Paragraph(class_text, self.styles["BodyText"]))
        self.story.append(Spacer(1, 0.15*inch))

        # Market position
        rank = benchmark.get("market_position_rank", 0)
        total = len(market_intel.get("competitors", [])) + 1

        if rank > 0:
            position_color = ReportColors.grade("A") if rank <= 2 else ReportColors.grade("C") if rank <= 4 else ReportColors.grade("F")
            self.story.append(Paragraph(
                f'<font color="{position_color.hexval()}"><b>Market Position: #{rank} of {total} analyzed</b></font>',
                self.styles["SubSection"]
            ))
            self.story.append(Spacer(1, 0.15*inch))

        # Vs market average table
        vs_avg = benchmark.get("vs_market_average", {})
        if vs_avg:
            overall = self.data.get("overall_score", 0) or 0
            tech = self.data.get("audits", {}).get("technical", {}).get("score", 0) or 0
            content = self.data.get("audits", {}).get("content", {}).get("score", 0) or 0
            ai = self.data.get("audits", {}).get("ai_visibility", {}).get("score", 0) or 0

            data = [["Metric", "Your Score", "vs Market Avg", "Status"]]
            metrics = [
                ("Overall Score", overall, vs_avg.get("overall", 0)),
                ("Technical SEO", tech, vs_avg.get("technical", 0)),
                ("Content & Authority", content, vs_avg.get("content", 0)),
                ("AI Visibility", ai, vs_avg.get("ai_visibility", 0)),
            ]

            for name, score, diff in metrics:
                diff_str = f"+{diff}" if diff >= 0 else str(diff)
                status = "Above Avg" if diff > 0 else "At Avg" if diff == 0 else "Below Avg"
                data.append([name, str(score), diff_str, status])

            table = Table(data, colWidths=[2.2*inch, 1.3*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, ReportColors.border),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            self.story.append(table)

        # Critical gaps
        gaps = benchmark.get("critical_gaps", [])
        if gaps:
            self.story.append(Spacer(1, 0.2*inch))
            self.story.append(Paragraph("<b>Critical Gaps</b>", self.styles["SubSection"]))
            for gap in gaps[:4]:
                self.story.append(Paragraph(f"• {gap}", self.styles["Finding"]))

        # AI opportunity
        ai_opportunity = landscape.get("ai_visibility_opportunity", "")
        if ai_opportunity:
            self.story.append(Spacer(1, 0.2*inch))
            self.story.append(CalloutBox("AI Visibility Opportunity", ai_opportunity, "warning"))

        self.story.append(PageBreak())

    def _add_technical_section(self):
        """Add technical SEO section."""
        tech = self.data.get("audits", {}).get("technical", {})
        if not tech:
            return

        score = tech.get("score", 0) or 0
        has_market_intel = "market_intelligence" in self.data
        section_num = 4 if has_market_intel else 3

        self.story.append(SectionTitle("Technical SEO Analysis", number=section_num))

        # Score indicator
        score_color = ReportColors.score_color(score)
        status = "Good" if score >= 70 else "Needs Work" if score >= 50 else "Critical"
        self.story.append(Paragraph(
            f'<font color="{score_color.hexval()}"><b>Score: {score}/100</b></font> - {status}',
            self.styles["SubSection"]
        ))
        self.story.append(Spacer(1, 0.15*inch))

        intro = ("Technical SEO forms the foundation of search visibility. "
                "Issues here prevent search engines from properly crawling and indexing your content.")
        self.story.append(Paragraph(intro, self.styles["BodyText"]))
        self.story.append(Spacer(1, 0.2*inch))

        # Components breakdown chart
        components = tech.get("components", {})
        if components:
            categories = []
            scores = []
            max_scores = []

            for name, comp_data in components.items():
                if isinstance(comp_data, dict):
                    categories.append(name.replace("_", " ").title())
                    scores.append(comp_data.get("score", 0) or 0)
                    max_scores.append(comp_data.get("max", 100) or 100)

            if categories:
                chart_path = str(self.charts_dir / "tech_components.png")
                charts.create_ranked_bar_chart(
                    categories, scores, max_scores,
                    "Technical Component Scores", chart_path
                )
                if os.path.exists(chart_path):
                    img = Image(chart_path, width=6*inch, height=max(2, len(categories)*0.4)*inch)
                    img.hAlign = 'CENTER'
                    self.story.append(img)

        # Key findings - deduplicated
        self.story.append(Spacer(1, 0.2*inch))
        self.story.append(Paragraph("<b>Key Findings</b>", self.styles["SubSection"]))

        seen_descriptions = set()
        findings_added = 0

        for _comp_name, comp_data in components.items():
            if isinstance(comp_data, dict) and findings_added < 5:
                issues = comp_data.get("issues", [])
                for issue in issues[:2]:
                    if isinstance(issue, dict):
                        desc = issue.get("description", "")
                        if desc and desc not in seen_descriptions:
                            seen_descriptions.add(desc)
                            severity = issue.get("severity", "medium")
                            rec = issue.get("recommendation", "")
                            for elem in FindingBlock(desc, rec, severity):
                                self.story.append(elem)
                            findings_added += 1
                            if findings_added >= 5:
                                break

        self.story.append(PageBreak())

    def _add_content_section(self):
        """Add content & authority section."""
        content = self.data.get("audits", {}).get("content", {})
        if not content:
            return

        score = content.get("score", 0) or 0
        has_market_intel = "market_intelligence" in self.data
        section_num = 5 if has_market_intel else 4

        self.story.append(SectionTitle("Content & Authority", number=section_num))

        score_color = ReportColors.score_color(score)
        status = "Good" if score >= 70 else "Needs Work" if score >= 50 else "Critical"
        self.story.append(Paragraph(
            f'<font color="{score_color.hexval()}"><b>Score: {score}/100</b></font> - {status}',
            self.styles["SubSection"]
        ))
        self.story.append(Spacer(1, 0.15*inch))

        intro = ("Content quality and authority signals determine how search engines "
                "evaluate your expertise. E-E-A-T (Experience, Expertise, Authoritativeness, Trust) "
                "is critical for ranking in competitive markets.")
        self.story.append(Paragraph(intro, self.styles["BodyText"]))
        self.story.append(Spacer(1, 0.2*inch))

        # Components table
        components = content.get("components", {})
        if components:
            data = [["Component", "Score", "Max", "Status"]]
            for name, comp_data in components.items():
                if isinstance(comp_data, dict):
                    comp_score = comp_data.get("score", 0) or 0
                    max_score = comp_data.get("max", 100) or 100
                    pct = comp_score / max_score * 100 if max_score > 0 else 0
                    status = "Good" if pct >= 80 else "Needs Work" if pct >= 50 else "Poor"
                    data.append([
                        name.replace("_", " ").title(),
                        str(comp_score),
                        str(max_score),
                        status
                    ])

            table = Table(data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.6*inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, ReportColors.border),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ReportColors.background]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            self.story.append(table)

        self.story.append(PageBreak())

    def _add_ai_visibility_section(self):
        """Add AI visibility section."""
        ai = self.data.get("audits", {}).get("ai_visibility", {})
        if not ai:
            return

        score = ai.get("score", 0) or 0
        has_market_intel = "market_intelligence" in self.data
        section_num = 6 if has_market_intel else 5

        self.story.append(SectionTitle("AI Visibility Analysis", number=section_num))

        score_color = ReportColors.score_color(score)
        status = "Good" if score >= 70 else "Needs Work" if score >= 50 else "Critical"
        self.story.append(Paragraph(
            f'<font color="{score_color.hexval()}"><b>Score: {score}/100</b></font> - {status}',
            self.styles["SubSection"]
        ))
        self.story.append(Spacer(1, 0.15*inch))

        # Why it matters callout
        self.story.append(CalloutBox(
            "Why AI Visibility Matters",
            "AI-powered search (ChatGPT, Claude, Perplexity, Google AI Overviews) is rapidly "
            "changing how customers find businesses. This analysis evaluates how your brand "
            "appears in AI-generated responses - a competitive advantage most SEO agencies don't measure.",
            "warning"
        ))
        self.story.append(Spacer(1, 0.2*inch))

        # Components table
        components = ai.get("components", {})
        if components:
            data = [["Component", "Score", "Max", "Status"]]
            for name, comp_data in components.items():
                if isinstance(comp_data, dict):
                    comp_score = comp_data.get("score", 0) or 0
                    max_score = comp_data.get("max", 100) or 100
                    pct = comp_score / max_score * 100 if max_score > 0 else 0
                    status = "Good" if pct >= 80 else "Needs Work" if pct >= 50 else "Poor"
                    data.append([
                        name.replace("_", " ").title(),
                        str(comp_score),
                        str(max_score),
                        status
                    ])

            table = Table(data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.6*inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, ReportColors.border),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ReportColors.background]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            self.story.append(table)

        # Recommendations
        recs = ai.get("recommendations", [])
        if recs:
            self.story.append(Spacer(1, 0.2*inch))
            self.story.append(Paragraph("<b>AI Optimization Actions</b>", self.styles["SubSection"]))
            for rec in recs[:4]:
                if isinstance(rec, dict):
                    action = rec.get("action", "")
                    details = rec.get("details", "")
                    severity = rec.get("priority", "medium")
                    for elem in FindingBlock(action, details, severity):
                        self.story.append(elem)

        self.story.append(PageBreak())

    def _add_action_plan(self):
        """Add 30/60/90-day action plan."""
        has_market_intel = "market_intelligence" in self.data
        section_num = 7 if has_market_intel else 6

        self.story.append(SectionTitle("30/60/90-Day Action Plan", number=section_num))

        intro = ("The following tasks are prioritized by impact and effort. "
                "Focus on Priority 1 items first for maximum return on investment.")
        self.story.append(Paragraph(intro, self.styles["BodyText"]))
        self.story.append(Spacer(1, 0.2*inch))

        # Get detailed action plan
        detailed_plan = self.data.get("detailed_action_plan", {})

        if detailed_plan:
            # Priority 1 - Immediate (30 days)
            p1_tasks = detailed_plan.get("priority_1_immediate", [])
            if p1_tasks:
                self.story.append(Paragraph(
                    '<font color="#DC2626"><b>PRIORITY 1: Immediate (30 Days)</b></font>',
                    self.styles["SubSection"]
                ))
                self.story.append(Spacer(1, 0.1*inch))

                # Top 5 priorities callout
                top_priorities = [t.get("action", "")[:60] for t in p1_tasks[:5]]
                self.story.append(PriorityCallout(top_priorities))
                self.story.append(Spacer(1, 0.15*inch))

                # Simplified 4-column table
                tasks = []
                for task in p1_tasks[:4]:
                    tasks.append({
                        "task": task.get("action", ""),
                        "impact": task.get("impact", "").split("-")[0].strip() if task.get("impact") else "HIGH",
                        "effort": task.get("effort", ""),
                        "timeline": task.get("deadline", ""),
                    })
                self.story.append(PlanTable(tasks))
                self.story.append(Spacer(1, 0.25*inch))

            # Priority 2 - Short Term (60 days)
            p2_tasks = detailed_plan.get("priority_2_short_term", [])
            if p2_tasks:
                self.story.append(Paragraph(
                    '<font color="#D97706"><b>PRIORITY 2: Short Term (30-60 Days)</b></font>',
                    self.styles["SubSection"]
                ))
                self.story.append(Spacer(1, 0.1*inch))

                tasks = []
                for task in p2_tasks[:3]:
                    tasks.append({
                        "task": task.get("action", ""),
                        "impact": task.get("impact", "").split("-")[0].strip() if task.get("impact") else "MEDIUM",
                        "effort": task.get("effort", ""),
                        "timeline": task.get("deadline", ""),
                    })
                self.story.append(PlanTable(tasks))
                self.story.append(Spacer(1, 0.25*inch))

            # Priority 3 - Strategic (90 days)
            p3_tasks = detailed_plan.get("priority_3_strategic", [])
            if p3_tasks:
                self.story.append(Paragraph(
                    '<font color="#65A30D"><b>PRIORITY 3: Strategic (60-90 Days)</b></font>',
                    self.styles["SubSection"]
                ))
                self.story.append(Spacer(1, 0.1*inch))

                tasks = []
                for task in p3_tasks[:3]:
                    tasks.append({
                        "task": task.get("action", ""),
                        "impact": task.get("impact", "").split("-")[0].strip() if task.get("impact") else "HIGH",
                        "effort": task.get("effort", ""),
                        "timeline": task.get("deadline", ""),
                    })
                self.story.append(PlanTable(tasks))
        else:
            self._add_legacy_recommendations()

        # Next steps CTA
        self.story.append(Spacer(1, 0.3*inch))
        self._add_next_steps_cta()

    def _add_legacy_recommendations(self):
        """Add recommendations from audit data (fallback)."""
        all_recs = []
        for audit_name, audit_data in self.data.get("audits", {}).items():
            if audit_data and "recommendations" in audit_data:
                for rec in audit_data["recommendations"]:
                    rec["source"] = audit_name
                    all_recs.append(rec)

        priority_order = {"high": 0, "medium": 1, "low": 2, "quick_win": 1}
        all_recs.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))

        high_recs = [r for r in all_recs if r.get("priority") == "high"]
        if high_recs:
            self.story.append(Paragraph(
                '<font color="#DC2626"><b>HIGH PRIORITY</b></font>',
                self.styles["SubSection"]
            ))
            for rec in high_recs[:5]:
                action = rec.get("action", "")
                details = rec.get("details", "")
                for elem in FindingBlock(action, details, "high"):
                    self.story.append(elem)

    def _add_next_steps_cta(self):
        """Add next steps call-to-action."""
        content_style = ParagraphStyle(
            "CTAContent",
            fontSize=11,
            leading=16,
            textColor=ReportColors.text_secondary,
        )

        roi_data = self.data.get("roi_projection", {})
        inaction = roi_data.get("cost_of_inaction", {})

        steps_text = (
            "<b>1. Schedule Strategy Call</b> - Review findings and discuss priorities<br/><br/>"
            "<b>2. Approve Engagement</b> - 4-6 month SEO acceleration program<br/><br/>"
            "<b>3. Begin Implementation</b> - Quick wins in 30 days, measurable results in 90"
        )

        urgency = ""
        if inaction.get("monthly_opportunity_cost"):
            urgency = f"<i>Every month of delay costs {inaction['monthly_opportunity_cost']} in missed opportunities.</i>"

        content = Paragraph(
            f'<font color="#1F2937" size="14"><b>RECOMMENDED NEXT STEPS</b></font><br/><br/>'
            f'{steps_text}<br/><br/>'
            f'<font color="#DC2626">{urgency}</font><br/><br/>'
            f'<b>Contact:</b> info@raaptech.com | www.raaptech.com',
            content_style
        )

        table = Table([[content]], colWidths=[6.5*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
            ("BOX", (0, 0), (-1, -1), 2, ReportColors.success),
            ("LEFTPADDING", (0, 0), (-1, -1), 20),
            ("RIGHTPADDING", (0, 0), (-1, -1), 20),
            ("TOPPADDING", (0, 0), (-1, -1), 15),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
        ]))
        self.story.append(table)

    def generate(self) -> str:
        """Generate the PDF report."""
        doc = PremiumReportDoc(
            self.output_path,
            company_name=self.company_name,
            report_type="SEO Health Report",
        )

        # Build report sections
        self._add_cover_page()
        self._add_table_of_contents()
        self._add_executive_summary()
        self._add_score_breakdown()

        # Add market position if available
        if "market_intelligence" in self.data:
            self._add_market_position_section()

        self._add_technical_section()
        self._add_content_section()
        self._add_ai_visibility_section()
        self._add_action_plan()

        # Build PDF
        doc.build(self.story)

        return self.output_path


def generate_premium_report(json_path: str, output_path: str = None) -> str:
    """Generate premium PDF report from JSON audit data."""
    with open(json_path) as f:
        data = json.load(f)

    if output_path is None:
        output_path = json_path.replace(".json", "_PREMIUM.pdf")

    generator = PremiumReportGenerator(data, output_path)
    result = generator.generate()

    print(f"Premium PDF report generated: {result}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m packages.seo_health_report.premium_report <json_file> [output_file]")
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    generate_premium_report(json_path, output_path)
