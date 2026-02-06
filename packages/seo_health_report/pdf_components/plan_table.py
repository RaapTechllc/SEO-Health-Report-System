"""30/60/90 Day Action Plan table component."""
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Table, TableStyle

from .colors import ReportColors


def PlanTable(tasks: list[dict]) -> Table:  # noqa: N802
    """Create a professional action plan table (simplified 4-column layout).

    Args:
        tasks: List of dicts with keys: task, impact, effort, timeline

    Returns:
        Table flowable with action plan
    """
    body_style = ParagraphStyle(
        "PlanBody",
        fontSize=9,
        leading=12,
        textColor=ReportColors.text_secondary,
    )

    # Simplified 4-column header for better fit
    data = [["Task", "Impact", "Effort", "Timeline"]]

    small_style = ParagraphStyle(
        "PlanSmall",
        fontSize=8,
        leading=10,
        textColor=ReportColors.text_secondary,
    )

    for task in tasks:
        # Truncate very long task text
        task_text = task.get("task", "")
        if len(task_text) > 80:
            task_text = task_text[:77] + "..."

        data.append([
            Paragraph(task_text, body_style),
            task.get("impact", "")[:8],
            Paragraph(task.get("effort", ""), small_style),
            Paragraph(task.get("timeline", ""), small_style),
        ])

    # 4 columns totaling ~7 inches - wider effort/timeline for wrapping
    col_widths = [3.4*inch, 0.7*inch, 1.2*inch, 1.4*inch]
    table = Table(data, colWidths=col_widths)

    table.setStyle(TableStyle([
        # Header styling
        ("BACKGROUND", (0, 0), (-1, 0), ReportColors.text_primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Body styling
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ReportColors.background]),
        ("GRID", (0, 0), (-1, -1), 0.5, ReportColors.border),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def PriorityCallout(priorities: list[str]) -> Table:  # noqa: N802
    """Create a 'Top 5 Priorities' callout box.

    Args:
        priorities: List of top priority items

    Returns:
        Table flowable styled as callout
    """
    content_style = ParagraphStyle(
        "PriorityContent",
        fontSize=10,
        leading=14,
        textColor=ReportColors.text_secondary,
    )

    items = "<br/>".join([f"<b>{i+1}.</b> {p}" for i, p in enumerate(priorities[:5])])
    content = Paragraph(
        f'<font color="#DC2626"><b>TOP 5 PRIORITIES</b></font><br/><br/>{items}',
        content_style
    )

    table = Table([[content]], colWidths=[6.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ("BOX", (0, 0), (-1, -1), 2, ReportColors.danger),
        ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table
