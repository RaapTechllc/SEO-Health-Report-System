"""
Tier Configuration Loader

Loads tier-specific environment variables from config/tier_*.env files.
This allows dynamic model selection based on the audit tier.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Find the project root (where config/ directory should be)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Tier config directory
CONFIG_DIR = PROJECT_ROOT / "config"

# Mapping of tier names to config files
TIER_CONFIG_FILES = {
    "low": "tier_low.env",
    "medium": "tier_medium.env",
    "high": "tier_high.env",
}

# Variables that should be loaded from tier configs
TIER_VARIABLES = [
    # OpenAI
    "OPENAI_MODEL_FAST",
    "OPENAI_MODEL_QUALITY",
    "OPENAI_MODEL",
    "OPENAI_IMAGE_MODEL",
    # Anthropic
    "ANTHROPIC_MODEL_FAST",
    "ANTHROPIC_MODEL_QUALITY",
    "ANTHROPIC_MODEL",
    # Google/Gemini
    "GOOGLE_MODEL_FAST",
    "GOOGLE_MODEL_QUALITY",
    "GOOGLE_MODEL",
    "GOOGLE_IMAGE_MODEL",
    # Perplexity
    "PERPLEXITY_MODEL_FAST",
    "PERPLEXITY_MODEL_QUALITY",
    "PERPLEXITY_MODEL",
    # xAI Grok
    "XAI_MODEL_FAST",
    "XAI_MODEL_QUALITY",
    "XAI_MODEL",
    # Report config
    "REPORT_TIER",
    "REPORT_TIER_NAME",
    "REPORT_AI_QUERIES_PER_PROVIDER",
    "REPORT_INCLUDE_SOCIAL_SENTIMENT",
    "REPORT_INCLUDE_COMPETITIVE_ANALYSIS",
    "REPORT_EXECUTIVE_SUMMARY_PROVIDER",
]


def parse_env_file(file_path: Path) -> dict[str, str]:
    """
    Parse a .env file and return a dictionary of key-value pairs.

    Args:
        file_path: Path to the .env file

    Returns:
        Dictionary of environment variable names to values
    """
    env_vars = {}

    if not file_path.exists():
        logger.warning(f"Tier config file not found: {file_path}")
        return env_vars

    with open(file_path) as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                env_vars[key] = value

    return env_vars


def load_tier_config(tier: str) -> dict[str, str]:
    """
    Load tier-specific configuration into the environment.

    This function:
    1. Reads the appropriate tier_*.env file
    2. Sets the environment variables
    3. Returns the loaded config for reference

    Args:
        tier: Tier name ('low', 'medium', 'high')

    Returns:
        Dictionary of loaded configuration values
    """
    # Normalize tier name
    tier = tier.lower().strip()

    # Map legacy tier names
    tier_mapping = {
        "basic": "low",
        "pro": "medium",
        "enterprise": "high",
        "budget": "low",
        "balanced": "medium",
        "premium": "high",
    }
    tier = tier_mapping.get(tier, tier)

    # Get config file name
    config_file = TIER_CONFIG_FILES.get(tier)
    if not config_file:
        logger.warning(f"Unknown tier '{tier}', defaulting to 'low'")
        config_file = TIER_CONFIG_FILES["low"]
        tier = "low"

    config_path = CONFIG_DIR / config_file

    logger.info(f"Loading tier config: {config_path}")

    # Parse the config file
    tier_config = parse_env_file(config_path)

    # Set environment variables
    loaded_vars = {}
    for var_name in TIER_VARIABLES:
        if var_name in tier_config:
            os.environ[var_name] = tier_config[var_name]
            loaded_vars[var_name] = tier_config[var_name]
            logger.debug(f"Set {var_name}={tier_config[var_name]}")

    # Always set REPORT_TIER
    os.environ["REPORT_TIER"] = tier
    loaded_vars["REPORT_TIER"] = tier

    logger.info(f"Loaded {len(loaded_vars)} tier configuration variables for '{tier}' tier")

    return loaded_vars


def get_current_tier() -> str:
    """Get the currently configured tier."""
    return os.environ.get("REPORT_TIER", "low")


def get_tier_model(provider: str, quality: str = "fast") -> str:
    """
    Get the model name for a provider based on current tier config.

    Args:
        provider: Provider name ('openai', 'anthropic', 'google', 'perplexity', 'xai')
        quality: Quality level ('fast' or 'quality')

    Returns:
        Model name from current tier config
    """
    provider = provider.upper()
    quality = quality.upper()

    var_name = f"{provider}_MODEL_{quality}"
    fallback_var = f"{provider}_MODEL"

    model = os.environ.get(var_name) or os.environ.get(fallback_var)

    if not model:
        # Default fallbacks
        defaults = {
            "OPENAI": "gpt-5-nano",
            "ANTHROPIC": "claude-4-haiku-20251120",
            "GOOGLE": "gemini-3.0-flash",
            "PERPLEXITY": "sonar",
            "XAI": "grok-4-1-fast-reasoning",
        }
        model = defaults.get(provider, "unknown")
        logger.warning(f"No model configured for {provider}, using default: {model}")

    return model


def get_tier_info() -> dict[str, str]:
    """
    Get information about the current tier configuration.

    Returns:
        Dictionary with tier name, display name, and key settings
    """
    return {
        "tier": get_current_tier(),
        "display_name": os.environ.get("REPORT_TIER_NAME", "Unknown"),
        "ai_queries_per_provider": os.environ.get("REPORT_AI_QUERIES_PER_PROVIDER", "3"),
        "include_social_sentiment": os.environ.get("REPORT_INCLUDE_SOCIAL_SENTIMENT", "true"),
        "include_competitive_analysis": os.environ.get("REPORT_INCLUDE_COMPETITIVE_ANALYSIS", "false"),
    }
