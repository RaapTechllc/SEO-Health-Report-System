"""
Premium PDF Layout using BaseDocTemplate.

Provides proper page templates with header/footer support.
Based on premium-pdf-reports skill guidelines.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageTemplate,
)

from .pdf_components.colors import ReportColors


class PremiumReportDoc(BaseDocTemplate):
    """Premium report document with proper page templates."""

    def __init__(
        self,
        filename: str,
        company_name: str = "",
        report_type: str = "SEO Health Report",
        **kwargs
    ):
        """Initialize premium report document.

        Args:
            filename: Output PDF path
            company_name: Company name for header
            report_type: Report type for header
        """
        self.company_name = company_name
        self.report_type = report_type

        super().__init__(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            **kwargs
        )

        content_frame = Frame(
            0.75*inch,
            0.75*inch,
            7*inch,
            9.5*inch,
            id='content',
            showBoundary=0,
        )

        cover_template = PageTemplate(
            id='cover',
            frames=[content_frame],
            onPage=self._cover_page_callback,
        )

        body_template = PageTemplate(
            id='body',
            frames=[content_frame],
            onPage=self._body_page_callback,
        )

        self.addPageTemplates([cover_template, body_template])

    def _cover_page_callback(self, canvas, doc):
        """Callback for cover page - minimal decoration."""
        canvas.saveState()
        canvas.setStrokeColor(ReportColors.info)
        canvas.setLineWidth(2)
        canvas.line(0.75*inch, 0.5*inch, 7.75*inch, 0.5*inch)
        canvas.restoreState()

    def _body_page_callback(self, canvas, doc):
        """Callback for body pages - full header/footer."""
        canvas.saveState()

        canvas.setStrokeColor(ReportColors.border)
        canvas.setLineWidth(0.5)
        canvas.line(0.75*inch, 10.5*inch, 7.75*inch, 10.5*inch)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(ReportColors.text_muted)
        if self.company_name:
            canvas.drawString(0.75*inch, 10.6*inch, self.company_name)
        canvas.drawRightString(7.75*inch, 10.6*inch, self.report_type)

        canvas.line(0.75*inch, 0.6*inch, 7.75*inch, 0.6*inch)

        canvas.drawString(0.75*inch, 0.4*inch, "Confidential")
        canvas.drawCentredString(4.25*inch, 0.4*inch, "RaapTech SEO Intelligence")
        canvas.drawRightString(7.75*inch, 0.4*inch, f"Page {doc.page}")

        canvas.restoreState()


def switch_to_body_template():
    """Return flowable to switch to body template after cover page."""
    return NextPageTemplate('body')
