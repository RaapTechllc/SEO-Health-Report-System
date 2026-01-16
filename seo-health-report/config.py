"""
Configuration Management

Centralized configuration for SEO Health Report system.
Supports environment variable overrides and provides sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List


@dataclass
class Config:
    """Centralized configuration for SEO Health Report."""

    # API Configuration
    api_timeout: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_API_TIMEOUT", "30"))
    )
    anthropic_model: str = field(
        default_factory=lambda: os.environ.get(
            "ANTHROPIC_MODEL", "claude-sonnet-4-5"
        )
    )

    # Cache Configuration
    cache_dir: str = field(
        default_factory=lambda: os.environ.get(
            "SEO_HEALTH_CACHE_DIR",
            os.path.join(os.path.expanduser("~"), ".seo-health-cache"),
        )
    )
    cache_ttl_pagespeed: int = field(
        default_factory=lambda: int(
            os.environ.get("SEO_HEALTH_CACHE_TTL_PAGESPEED", "86400")
        )
    )
    cache_ttl_ai_response: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_CACHE_TTL_AI", "604800"))
    )
    cache_ttl_http_fetch: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_CACHE_TTL_HTTP", "3600"))
    )

    # PageSpeed API Configuration
    pagespeed_api_endpoint: str = field(
        default_factory=lambda: os.environ.get(
            "SEO_HEALTH_PAGESPEED_ENDPOINT",
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
        )
    )
    pagespeed_strategy: str = field(
        default_factory=lambda: os.environ.get(
            "SEO_HEALTH_PAGESPEED_STRATEGY", "mobile"
        )
    )
    pagespeed_strategy: str = field(
        default_factory=lambda: os.environ.get(
            "SEO_HEALTH_PAGESPEED_STRATEGY", "mobile"
        )
    )
    pagespeed_categories: list = field(
        default_factory=lambda: [
            "performance",
            "accessibility",
            "best-practices",
            "seo",
        ]
    )

    # Scoring Configuration
    score_weight_technical: float = field(
        default_factory=lambda: float(
            os.environ.get("SEO_HEALTH_WEIGHT_TECHNICAL", "0.30")
        )
    )
    score_weight_content: float = field(
        default_factory=lambda: float(
            os.environ.get("SEO_HEALTH_WEIGHT_CONTENT", "0.35")
        )
    )
    score_weight_ai: float = field(
        default_factory=lambda: float(os.environ.get("SEO_HEALTH_WEIGHT_AI", "0.35"))
    )

    # Grade Thresholds
    grade_a_threshold: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_GRADE_A", "90"))
    )
    grade_b_threshold: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_GRADE_B", "80"))
    )
    grade_c_threshold: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_GRADE_C", "70"))
    )
    grade_d_threshold: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_GRADE_D", "60"))
    )

    # AI Systems Priority Configuration (Top 3 Systems)
    ai_systems_priority: List[str] = field(default_factory=lambda: [
        "claude",      # Google AI search proxy (Bard/Gemini)
        "openai",      # OpenAI search (ChatGPT)  
        "perplexity"   # Perplexity AI search
    ])
    ai_query_timeout: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_AI_TIMEOUT", "30"))
    )
    ai_rate_limit_ms: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_AI_RATE_LIMIT", "1000"))
    )

    # Default Brand Colors
    default_colors: Dict[str, str] = field(
        default_factory=lambda: {
            "primary": "#1a73e8",
            "secondary": "#34a853",
            "accent": "#fbbc04",
            "warning": "#fbbc04",
            "danger": "#ea4335",
            "success": "#34a853",
            "text": "#202124",
            "background": "#ffffff",
            "border": "#dadce0",
        }
    )

    # Crawl Configuration
    crawl_max_depth: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_CRAWL_DEPTH", "50"))
    )
    crawl_timeout: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_CRAWL_TIMEOUT", "30"))
    )
    crawl_user_agent: str = field(
        default_factory=lambda: os.environ.get(
            "SEO_HEALTH_USER_AGENT", "SEO-Health-Report-Bot/1.0 (Technical Audit)"
        )
    )

    # Output Configuration
    output_format: str = field(
        default_factory=lambda: os.environ.get("SEO_HEALTH_OUTPUT_FORMAT", "docx")
    )
    output_dir: str = field(
        default_factory=lambda: os.environ.get("SEO_HEALTH_OUTPUT_DIR", ".")
    )

    # Logging Configuration
    log_level: str = field(
        default_factory=lambda: os.environ.get("SEO_HEALTH_LOG_LEVEL", "INFO")
    )
    log_dir: str = field(
        default_factory=lambda: os.environ.get("SEO_HEALTH_LOG_DIR", "logs")
    )
    log_file: str = field(
        default_factory=lambda: os.environ.get(
            "SEO_HEALTH_LOG_FILE", "seo-health-report.log"
        )
    )
    log_max_bytes: int = field(
        default_factory=lambda: int(
            os.environ.get("SEO_HEALTH_LOG_MAX_BYTES", str(10 * 1024 * 1024))
        )
    )
    log_backup_count: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_LOG_BACKUP_COUNT", "5"))
    )

    # Content Analysis Configuration
    min_content_length: int = field(
        default_factory=lambda: int(
            os.environ.get("SEO_HEALTH_MIN_CONTENT_LENGTH", "300")
        )
    )
    max_title_length: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_MAX_TITLE_LENGTH", "60"))
    )
    max_description_length: int = field(
        default_factory=lambda: int(os.environ.get("SEO_HEALTH_MAX_DESC_LENGTH", "160"))
    )

    def validate(self) -> Dict[str, Any]:
        """
        Validate configuration and return any errors or warnings.

        Returns:
            Dict with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []

        # Validate API keys
        if not os.environ.get("ANTHROPIC_API_KEY"):
            warnings.append(
                "ANTHROPIC_API_KEY not set - AI visibility audit will be limited"
            )

        # Validate scoring weights sum to 1
        total_weight = (
            self.score_weight_technical
            + self.score_weight_content
            + self.score_weight_ai
        )
        if abs(total_weight - 1.0) > 0.01:
            errors.append(
                f"Scoring weights must sum to 1.0 (currently: {total_weight:.2f})"
            )

        # Validate grade thresholds
        if not (
            self.grade_a_threshold
            > self.grade_b_threshold
            > self.grade_c_threshold
            > self.grade_d_threshold
            > 0
        ):
            errors.append(
                "Grade thresholds must be in descending order: A > B > C > D > 0"
            )

        # Validate timeout values
        if self.api_timeout <= 0:
            errors.append("API timeout must be positive")
        if self.crawl_timeout <= 0:
            errors.append("Crawl timeout must be positive")

        # Validate cache TTL values
        if self.cache_ttl_pagespeed < 0:
            errors.append("PageSpeed cache TTL must be non-negative")
        if self.cache_ttl_ai_response < 0:
            errors.append("AI response cache TTL must be non-negative")
        if self.cache_ttl_http_fetch < 0:
            errors.append("HTTP fetch cache TTL must be non-negative")

        # Validate output format
        valid_formats = ["docx", "pdf", "md"]
        if self.output_format not in valid_formats:
            warnings.append(
                f"Invalid output format '{self.output_format}'. "
                f"Must be one of: {', '.join(valid_formats)}"
            )

        return {"errors": errors, "warnings": warnings}

    def get_color(
        self, color_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a brand color by name.

        Args:
            color_name: Name of color (primary, secondary, etc.)
            default: Default color if not found

        Returns:
            Hex color string or default
        """
        return self.default_colors.get(color_name, default)

    def get_page_colors(self) -> Dict[str, str]:
        """
        Get all page-related colors.

        Returns:
            Dict with page color configuration
        """
        return {
            "primary": self.default_colors.get("primary", "#1a73e8"),
            "secondary": self.default_colors.get("secondary", "#34a853"),
            "text": self.default_colors.get("text", "#202124"),
            "background": self.default_colors.get("background", "#ffffff"),
            "border": self.default_colors.get("border", "#dadce0"),
        }

    def get_grade_color(self, score: int) -> str:
        """
        Get color based on score/grade.

        Args:
            score: Score value (0-100)

        Returns:
            Hex color string
        """
        if score >= self.grade_a_threshold:
            return self.default_colors.get("success", "#34a853")
        elif score >= self.grade_b_threshold:
            return "#fbbc04"
        elif score >= self.grade_c_threshold:
            return "#fbbc04"
        else:
            return self.default_colors.get("danger", "#ea4335")

    def get_log_file_path(self) -> str:
        """
        Get full path to log file.

        Returns:
            Full path to log file
        """
        os.makedirs(self.log_dir, exist_ok=True)
        return os.path.join(self.log_dir, self.log_file)


# Global config instance
_config_instance = None


def get_config() -> Config:
    """
    Get or create global configuration instance.

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def set_config(config: Config) -> None:
    """
    Set global configuration instance.

    Args:
        config: Config instance to set
    """
    global _config_instance
    _config_instance = config


def reload_config() -> Config:
    """
    Reload configuration from environment variables.

    Returns:
        New Config instance
    """
    global _config_instance
    _config_instance = Config()
    return _config_instance


__all__ = ["Config", "get_config", "set_config", "reload_config"]
