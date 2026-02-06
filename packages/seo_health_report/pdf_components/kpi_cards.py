"""KPI card row component for displaying key metrics."""
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Table, TableStyle

from .colors import ReportColors


def KpiCardRow(kpis: list[tuple[str, str, str]]) -> Table:  # noqa: N802
    """Create a row of KPI cards.

    Args:
        kpis: List of tuples: (label, value, trend) where trend is "up", "down", or "neutral"

    Returns:
        Table flowable with KPI cards
    """
    cards = []
    for label, value, _trend in kpis:
        card_content = [
            Paragraph(
                f'<font size="9" color="#6B7280">{label}</font>',
                ParagraphStyle("KpiLabel", alignment=1)
            ),
            Paragraph(
                f'<font size="24" color="#1F2937"><b>{value}</b></font>',
                ParagraphStyle("KpiValue", alignment=1)
            ),
        ]
        cards.append(card_content)

    # Create table with cards side by side
    card_width = 1.6 * inch
    table = Table([cards], colWidths=[card_width] * len(kpis))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ReportColors.background),
        ("BOX", (0, 0), (-1, -1), 1, ReportColors.border),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table
