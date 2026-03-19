"""Typography scale for premium reports."""
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from .colors import ReportColors

# Typography scale constants (consistent sizing)
TYPOGRAPHY = {
    "h1": {"fontSize": 24, "leading": 28, "spaceAfter": 12},
    "h2": {"fontSize": 18, "leading": 22, "spaceAfter": 10},
    "h3": {"fontSize": 14, "leading": 18, "spaceAfter": 8},
    "body": {"fontSize": 11, "leading": 15, "spaceAfter": 6},
    "caption": {"fontSize": 9, "leading": 12, "spaceAfter": 4},
}


def get_report_styles() -> dict:
    """Get all paragraph styles for premium reports."""
    base = getSampleStyleSheet()

    styles = {
        # Section titles - H1 equivalent
        "SectionTitle": ParagraphStyle(
            "SectionTitle",
            parent=base["Heading1"],
            fontSize=TYPOGRAPHY["h1"]["fontSize"],
            leading=TYPOGRAPHY["h1"]["leading"],
            spaceAfter=TYPOGRAPHY["h1"]["spaceAfter"],
            spaceBefore=20,
            textColor=ReportColors.text_primary,
            fontName="Helvetica-Bold",
        ),

        # Subsection - H2 equivalent
        "SubSection": ParagraphStyle(
            "SubSection",
            parent=base["Heading2"],
            fontSize=TYPOGRAPHY["h2"]["fontSize"],
            leading=TYPOGRAPHY["h2"]["leading"],
            spaceAfter=TYPOGRAPHY["h2"]["spaceAfter"],
            spaceBefore=12,
            textColor=ReportColors.text_primary,
            fontName="Helvetica-Bold",
        ),

        # H3 equivalent
        "Heading3": ParagraphStyle(
            "Heading3",
            parent=base["Heading3"],
            fontSize=TYPOGRAPHY["h3"]["fontSize"],
            leading=TYPOGRAPHY["h3"]["leading"],
            spaceAfter=TYPOGRAPHY["h3"]["spaceAfter"],
            spaceBefore=8,
            textColor=ReportColors.text_primary,
            fontName="Helvetica-Bold",
        ),

        # Body text
        "BodyText": ParagraphStyle(
            "BodyText",
            parent=base["Normal"],
            fontSize=TYPOGRAPHY["body"]["fontSize"],
            leading=TYPOGRAPHY["body"]["leading"],
            spaceAfter=TYPOGRAPHY["body"]["spaceAfter"],
            textColor=ReportColors.text_secondary,
            alignment=TA_JUSTIFY,
        ),

        # Caption/metadata
        "Caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontSize=TYPOGRAPHY["caption"]["fontSize"],
            leading=TYPOGRAPHY["caption"]["leading"],
            spaceAfter=TYPOGRAPHY["caption"]["spaceAfter"],
            textColor=ReportColors.text_muted,
        ),

        # Finding item (bullet point style)
        "Finding": ParagraphStyle(
            "Finding",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            spaceAfter=4,
            leftIndent=15,
            textColor=ReportColors.text_secondary,
        ),

        # Centered text
        "Centered": ParagraphStyle(
            "Centered",
            parent=base["Normal"],
            fontSize=TYPOGRAPHY["body"]["fontSize"],
            leading=TYPOGRAPHY["body"]["leading"],
            alignment=TA_CENTER,
            textColor=ReportColors.text_secondary,
        ),
    }

    return styles
