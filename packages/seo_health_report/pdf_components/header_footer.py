"""Header and footer for BaseDocTemplate."""
from reportlab.lib.units import inch

from .colors import ReportColors


def add_header_footer(canvas, doc, company_name: str = "", report_type: str = "SEO Health Report"):
    """Add consistent header and footer to pages.

    Args:
        canvas: ReportLab canvas
        doc: Document being built
        company_name: Company name for header
        report_type: Type of report for header
    """
    canvas.saveState()

    # Header line (subtle separator)
    canvas.setStrokeColor(ReportColors.border)
    canvas.setLineWidth(0.5)
    canvas.line(0.75*inch, 10.5*inch, 7.75*inch, 10.5*inch)

    # Header text (left: company, right: report type)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(ReportColors.text_muted)
    if company_name:
        canvas.drawString(0.75*inch, 10.6*inch, company_name)
    canvas.drawRightString(7.75*inch, 10.6*inch, report_type)

    # Footer line
    canvas.line(0.75*inch, 0.6*inch, 7.75*inch, 0.6*inch)

    # Footer text
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(ReportColors.text_muted)
    canvas.drawString(0.75*inch, 0.4*inch, "Confidential")
    canvas.drawCentredString(4.25*inch, 0.4*inch, "RaapTech SEO Intelligence")
    canvas.drawRightString(7.75*inch, 0.4*inch, f"Page {doc.page}")

    canvas.restoreState()
