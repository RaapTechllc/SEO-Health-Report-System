"""
Core utilities for SEO Health Report System.

This package provides shared functionality used across all modules:
- Environment loading
- Logging configuration
- Common exceptions
"""

from packages.core.env import get_project_root, load_env

__all__ = ["load_env", "get_project_root"]
