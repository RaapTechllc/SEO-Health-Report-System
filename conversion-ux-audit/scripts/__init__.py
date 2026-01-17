"""
Conversion UX Audit Scripts

Phone, CTA, Form, and Tracking checks.
"""

from .check_phone import (
    analyze_phone_optimization,
    extract_phone_numbers,
    check_click_to_call,
    check_phone_placement,
)
from .check_cta import (
    analyze_cta_optimization,
    extract_ctas,
    check_cta_clarity,
    check_cta_placement,
)
from .check_forms import (
    analyze_form_optimization,
    extract_forms,
    check_form_field_count,
    check_form_mobile_friendly,
)
from .check_tracking import (
    analyze_tracking_setup,
    check_ga4_installed,
    check_phone_click_tracking,
)

__all__ = [
    'analyze_phone_optimization',
    'extract_phone_numbers',
    'check_click_to_call',
    'check_phone_placement',
    'analyze_cta_optimization',
    'extract_ctas',
    'check_cta_clarity',
    'check_cta_placement',
    'analyze_form_optimization',
    'extract_forms',
    'check_form_field_count',
    'check_form_mobile_friendly',
    'analyze_tracking_setup',
    'check_ga4_installed',
    'check_phone_click_tracking',
]
