"""
Tenant branding service for report customization.
"""

from .report_integration import (
    apply_html_branding,
    generate_css_variables,
    get_pdf_branding_colors,
    get_pdf_footer_text,
    get_report_branding,
)
from .service import DEFAULT_BRANDING, BrandingService

__all__ = [
    "BrandingService",
    "DEFAULT_BRANDING",
    "get_report_branding",
    "apply_html_branding",
    "get_pdf_branding_colors",
    "get_pdf_footer_text",
    "generate_css_variables",
]
