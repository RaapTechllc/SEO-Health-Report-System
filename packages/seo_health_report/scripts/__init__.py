"""
SEO Health Report Scripts

Master orchestrator functionality for generating comprehensive SEO reports.
"""

from .apply_branding import apply_branding
from .build_report import build_report_document, generate_pdf
from .calculate_scores import calculate_composite_score, determine_grade
from .generate_summary import generate_executive_summary
from .idempotency import canonicalize_url, compute_idempotency_key
from .orchestrate import run_full_audit
from .rate_limiter import (
    TIER_LIMITS,
    RateLimitedSession,
    RateLimiter,
    RateLimiterConfig,
    rate_limited_fetch,
)
from .redaction import redact_dict, redact_sensitive
from .webhook import (
    WebhookResult,
    build_audit_webhook_payload,
    deliver_webhook,
    sign_webhook_payload,
    validate_callback_url,
    verify_webhook_signature,
)

# Optional PDF components (requires reportlab)
try:
    from .pdf_components import (
        create_cover_page,
        create_findings_table,
        create_recommendations_list,
        create_score_gauge,
        create_section_header,
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
    'redact_sensitive',
    'redact_dict',
    'canonicalize_url',
    'compute_idempotency_key',
    'create_cover_page',
    'create_score_gauge',
    'create_section_header',
    'create_findings_table',
    'create_recommendations_list',
    'RateLimiter',
    'RateLimiterConfig',
    'RateLimitedSession',
    'rate_limited_fetch',
    'TIER_LIMITS',
    'WebhookResult',
    'sign_webhook_payload',
    'verify_webhook_signature',
    'validate_callback_url',
    'deliver_webhook',
    'build_audit_webhook_payload',
]
