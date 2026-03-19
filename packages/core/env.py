"""
Centralized environment loading for SEO Health Report System.

Usage:
    from packages.core.env import load_env
    load_env()  # Call once at application startup

This module:
1. Finds the project root (where pyproject.toml lives)
2. Loads .env.local first (if exists), then .env
3. Adds package paths to sys.path
"""

import sys
from pathlib import Path
from typing import Optional

_env_loaded = False
_project_root: Optional[Path] = None


def get_project_root() -> Path:
    """
    Find the project root directory by looking for pyproject.toml.

    Returns:
        Path to project root directory
    """
    global _project_root

    if _project_root is not None:
        return _project_root

    current = Path(__file__).resolve()

    # Walk up the tree looking for pyproject.toml
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            _project_root = parent
            return _project_root

    # Fallback: assume we're in packages/core/
    _project_root = current.parent.parent.parent
    return _project_root


def load_env(force: bool = False) -> None:
    """
    Load environment variables from .env files.

    Priority order:
    1. .env.local (local development overrides)
    2. .env (default configuration)

    Args:
        force: If True, reload even if already loaded
    """
    global _env_loaded

    if _env_loaded and not force:
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        # dotenv not installed, skip loading
        _env_loaded = True
        return

    root = get_project_root()

    # Load .env first, then .env.local (so local overrides defaults)
    env_file = root / ".env"
    env_local = root / ".env.local"

    if env_file.exists():
        load_dotenv(env_file)

    if env_local.exists():
        load_dotenv(env_local, override=True)

    _env_loaded = True


def setup_paths() -> None:
    """
    Add standard package paths to sys.path.

    This ensures imports like 'from packages.seo_health_report import ...'
    work regardless of where the script is run from.
    """
    root = get_project_root()

    # Add root to path for absolute imports
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    # Add packages directory
    packages_dir = str(root / "packages")
    if packages_dir not in sys.path:
        sys.path.insert(0, packages_dir)


def init() -> None:
    """
    Full initialization: load environment and setup paths.

    Call this once at application startup.
    """
    load_env()
    setup_paths()
