"""Finding block component for issues/recommendations."""
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from .colors import ReportColors


def FindingBlock(  # noqa: N802
    title: str,
    description: str,
    severity: str,
    evidence: list[str] = None
) -> list:
    """Create a finding block with severity indicator and optional evidence.

    Args:
        title: Finding title
        description: Finding description
        severity: One of "critical", "high", "medium", "low"
        evidence: Optional list of evidence URLs or snippets

    Returns:
        List of flowable elements
    """
    severity_colors = {
        "critical": "#DC2626",
        "high": "#EA580C",
        "medium": "#D97706",
        "low": "#65A30D",
    }
    color = severity_colors.get(severity.lower(), "#6B7280")

    title_style = ParagraphStyle(
        "FindingTitle",
        fontSize=11,
        leading=14,
        spaceAfter=2,
        textColor=ReportColors.text_primary,
    )

    desc_style = ParagraphStyle(
        "FindingDesc",
        fontSize=10,
        leading=14,
        spaceAfter=4,
        leftIndent=15,
        textColor=ReportColors.text_secondary,
    )

    evidence_style = ParagraphStyle(
        "FindingEvidence",
        fontSize=9,
        leading=12,
        leftIndent=15,
        textColor=ReportColors.text_muted,
    )

    elements = [
        Paragraph(f'<font color="{color}">&#9679;</font> <b>{title}</b>', title_style),
        Paragraph(description, desc_style),
    ]

    if evidence:
        evidence_text = "<br/>".join([f"&#8226; {e}" for e in evidence[:3]])
        elements.append(Paragraph(f"Evidence: {evidence_text}", evidence_style))

    elements.append(Spacer(1, 0.08 * inch))
    return elements
