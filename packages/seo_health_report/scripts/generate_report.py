"""
Report Generation Module

Provides HTML and PDF report generation with graceful fallback.
"""

import logging
from pathlib import Path
from typing import Optional

from packages.schemas.models import AuditResult

logger = logging.getLogger(__name__)

# Check weasyprint availability at module load
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML as WeasyprintHTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WeasyprintHTML = None
    logger.info("weasyprint not available - PDF generation disabled")


async def generate_pdf_report(
    audit_result: AuditResult,
    raw_result: dict,
    tenant_id: str,
    html_path: Optional[str] = None,
) -> Optional[str]:
    """
    Generate PDF report from HTML. Returns path or None if unavailable.

    Args:
        audit_result: The audit result object
        raw_result: Raw audit data dictionary
        tenant_id: Tenant identifier for report storage
        html_path: Optional path to existing HTML file

    Returns:
        Path to generated PDF file, or None if PDF generation is unavailable
    """
    if not WEASYPRINT_AVAILABLE:
        logger.debug("PDF generation skipped - weasyprint not installed")
        return None

    try:
        # Import here to avoid issues when weasyprint isn't available
        from weasyprint import HTML

        # If no html_path provided, we need to generate HTML first
        if not html_path:
            # Import the HTML generator from the handler
            from apps.worker.handlers.full_audit import generate_html_report_simple
            html_path = await generate_html_report_simple(audit_result, raw_result, tenant_id)

        # Verify HTML file exists
        html_file = Path(html_path)
        if not html_file.exists():
            logger.warning(f"HTML file not found at {html_path}, cannot generate PDF")
            return None

        # Generate PDF path
        pdf_path = str(html_file.with_suffix('.pdf'))

        # Generate PDF
        logger.info(f"Generating PDF report at {pdf_path}")
        HTML(filename=str(html_file)).write_pdf(pdf_path)

        logger.info(f"PDF report generated successfully: {pdf_path}")
        return pdf_path

    except Exception as e:
        # Graceful fallback - log error but don't fail the audit
        logger.warning(f"PDF generation failed (graceful fallback): {e}")
        return None


def is_pdf_available() -> bool:
    """Check if PDF generation is available."""
    return WEASYPRINT_AVAILABLE


__all__ = [
    "generate_pdf_report",
    "is_pdf_available",
    "WEASYPRINT_AVAILABLE",
]
