"""Section title component."""
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from .colors import ReportColors


def SectionTitle(text: str, number: int = None) -> Paragraph:  # noqa: N802
    """Create a premium section title with optional numbering.

    Args:
        text: Section title text
        number: Optional section number (e.g., 1, 2, 3)

    Returns:
        Paragraph flowable
    """
    prefix = f"{number}. " if number else ""
    style = ParagraphStyle(
        "SectionTitle",
        fontSize=24,
        leading=28,
        spaceAfter=12,
        spaceBefore=20,
        textColor=ReportColors.text_primary,
        fontName="Helvetica-Bold",
    )
    return Paragraph(f"{prefix}{text}", style)
