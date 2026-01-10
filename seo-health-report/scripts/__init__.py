"""
SEO Health Report Scripts

Master orchestrator functionality for generating comprehensive SEO reports.
"""

from .orchestrate import run_full_audit
from .calculate_scores import calculate_composite_score, determine_grade
from .generate_summary import generate_executive_summary
from .build_report import build_report_document, generate_pdf
from .apply_branding import apply_branding

# Optional PDF components (requires reportlab)
try:
    from .pdf_components import (
        create_cover_page, create_score_gauge, create_section_header,
        create_findings_table, create_recommendations_list
    )
    _HAS_PDF_COMPONENTS = True
except ImportError:
    create_cover_page = None
    create_score_gauge = None
    create_section_header = None
    create_findings_table = None
    create_recommendations_list = None
    _HAS_PDF_COMPONENTS = False

__all__ = [
    'run_full_audit',
    'calculate_composite_score',
    'determine_grade',
    'generate_executive_summary',
    'build_report_document',
    'generate_pdf',
    'apply_branding',
    'create_cover_page',
    'create_score_gauge',
    'create_section_header',
    'create_findings_table',
    'create_recommendations_list'
]
