"""
Social Media Audit Module

Score company's social media presence and brand consistency.
"""

from .social_media_audit import (
    run_social_audit,
    check_linkedin_presence,
    find_social_profiles,
    check_social_consistency,
    generate_social_recommendations
)

__version__ = "1.0.0"

__all__ = [
    'run_social_audit',
    'check_linkedin_presence',
    'find_social_profiles',
    'check_social_consistency',
    'generate_social_recommendations'
]
