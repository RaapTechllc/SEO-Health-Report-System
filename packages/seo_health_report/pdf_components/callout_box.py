"""Callout box component with accent bar."""
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Table, TableStyle

from .colors import ReportColors


def CalloutBox(title: str, content: str, severity: str = "info") -> Table:  # noqa: N802
    """Create a callout box with left accent bar.

    Args:
        title: Callout title
        content: Callout content text
        severity: One of "info", "warning", "success", "danger"

    Returns:
        Table flowable styled as callout box
    """
    accent_colors = {
        "info": ReportColors.info,
        "warning": ReportColors.warning,
        "success": ReportColors.success,
        "danger": ReportColors.danger,
    }
    accent = accent_colors.get(severity, ReportColors.info)

    # Build content paragraph
    style = ParagraphStyle(
        "CalloutContent",
        fontSize=10,
        leading=14,
        textColor=ReportColors.text_secondary,
    )

    inner_content = Paragraph(
        f'<font color="{accent.hexval()}"><b>{title}</b></font><br/>{content}',
        style
    )

    table = Table([[inner_content]], colWidths=[6.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ReportColors.background),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 4, accent),
    ]))
    return table
