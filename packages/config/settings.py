"""
Pydantic Settings for SEO Health Report System.

Type-safe, validated configuration management with environment variable support.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .environments import Environment, get_current_environment


class Settings(BaseSettings):
    """
    Centralized settings for the SEO Health Report System.

    All settings can be overridden via environment variables.
    Uses the SEO_HEALTH_ prefix for most SEO-specific settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===========================================
    # Environment Configuration
    # ===========================================
    app_env: str = Field(
        default="development",
        validation_alias="APP_ENV",
        description="Application environment (development, staging, production, test)",
    )

    # ===========================================
    # API Keys - Primary
    # ===========================================
    anthropic_api_key: Optional[str] = Field(
        default=None,
        validation_alias="ANTHROPIC_API_KEY",
        description="Anthropic API key for Claude AI",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        description="OpenAI API key for ChatGPT",
    )
    perplexity_api_key: Optional[str] = Field(
        default=None,
        validation_alias="PERPLEXITY_API_KEY",
        description="Perplexity API key",
    )
    xai_api_key: Optional[str] = Field(
        default=None,
        validation_alias="XAI_API_KEY",
        description="xAI API key for Grok",
    )

    # ===========================================
    # API Keys - Google Ecosystem
    # ===========================================
    google_api_key: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_API_KEY",
        description="Google API key (fallback for all Google services)",
    )
    google_gemini_api_key: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_GEMINI_API_KEY",
        description="Google Gemini API key for image generation",
    )
    google_kg_api_key: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_KG_API_KEY",
        description="Google Knowledge Graph API key",
    )
    pagespeed_api_key: Optional[str] = Field(
        default=None,
        validation_alias="PAGESPEED_API_KEY",
        description="Google PageSpeed Insights API key",
    )

    # ===========================================
    # API Keys - Payment & Auth
    # ===========================================
    stripe_secret_key: Optional[str] = Field(
        default=None,
        validation_alias="STRIPE_SECRET_KEY",
        description="Stripe secret key for payments",
    )
    stripe_webhook_secret: Optional[str] = Field(
        default=None,
        validation_alias="STRIPE_WEBHOOK_SECRET",
        description="Stripe webhook signing secret",
    )

    # ===========================================
    # Authentication
    # ===========================================
    jwt_secret_key: Optional[str] = Field(
        default=None,
        validation_alias="JWT_SECRET_KEY",
        description="Secret key for JWT token signing",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
        description="Algorithm for JWT signing",
    )
    jwt_expire_hours: int = Field(
        default=24,
        validation_alias="JWT_EXPIRE_HOURS",
        description="JWT token expiration in hours",
    )

    # ===========================================
    # Database
    # ===========================================
    database_url: Optional[str] = Field(
        default=None,
        validation_alias="DATABASE_URL",
        description="Database connection URL",
    )

    # ===========================================
    # Model Configuration
    # ===========================================
    anthropic_model: str = Field(
        default="claude-sonnet-4-5",
        validation_alias="ANTHROPIC_MODEL",
        description="Anthropic model to use",
    )
    google_model: str = Field(
        default="gemini-3-flash-preview",
        validation_alias="GOOGLE_MODEL",
        description="Google Gemini model to use",
    )
    google_image_model: str = Field(
        default="imagen-3.0-generate-002",
        validation_alias="GOOGLE_IMAGE_MODEL",
        description="Google image generation model",
    )

    # ===========================================
    # API Configuration
    # ===========================================
    api_timeout: int = Field(
        default=30,
        validation_alias="SEO_HEALTH_API_TIMEOUT",
        ge=1,
        le=300,
        description="API request timeout in seconds",
    )
    base_url: Optional[str] = Field(
        default=None,
        validation_alias="BASE_URL",
        description="Base URL for the API server",
    )

    # ===========================================
    # Cache Configuration
    # ===========================================
    cache_dir: str = Field(
        default_factory=lambda: os.path.join(os.path.expanduser("~"), ".seo-health-cache"),
        validation_alias="SEO_HEALTH_CACHE_DIR",
        description="Directory for cache files",
    )
    cache_ttl_pagespeed: int = Field(
        default=86400,  # 24 hours
        validation_alias="SEO_HEALTH_CACHE_TTL_PAGESPEED",
        ge=0,
        description="PageSpeed cache TTL in seconds",
    )
    cache_ttl_ai_response: int = Field(
        default=604800,  # 7 days
        validation_alias="SEO_HEALTH_CACHE_TTL_AI",
        ge=0,
        description="AI response cache TTL in seconds",
    )
    cache_ttl_http_fetch: int = Field(
        default=3600,  # 1 hour
        validation_alias="SEO_HEALTH_CACHE_TTL_HTTP",
        ge=0,
        description="HTTP fetch cache TTL in seconds",
    )

    # ===========================================
    # PageSpeed Configuration
    # ===========================================
    pagespeed_api_endpoint: str = Field(
        default="https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
        validation_alias="SEO_HEALTH_PAGESPEED_ENDPOINT",
        description="PageSpeed API endpoint URL",
    )
    pagespeed_strategy: str = Field(
        default="mobile",
        validation_alias="SEO_HEALTH_PAGESPEED_STRATEGY",
        description="PageSpeed strategy (mobile or desktop)",
    )

    # ===========================================
    # Scoring Configuration
    # ===========================================
    score_weight_technical: float = Field(
        default=0.30,
        validation_alias="SEO_HEALTH_WEIGHT_TECHNICAL",
        ge=0.0,
        le=1.0,
        description="Weight for technical SEO score",
    )
    score_weight_content: float = Field(
        default=0.35,
        validation_alias="SEO_HEALTH_WEIGHT_CONTENT",
        ge=0.0,
        le=1.0,
        description="Weight for content authority score",
    )
    score_weight_ai: float = Field(
        default=0.35,
        validation_alias="SEO_HEALTH_WEIGHT_AI",
        ge=0.0,
        le=1.0,
        description="Weight for AI visibility score",
    )

    # ===========================================
    # Grade Thresholds
    # ===========================================
    grade_a_threshold: int = Field(
        default=90,
        validation_alias="SEO_HEALTH_GRADE_A",
        ge=0,
        le=100,
        description="Minimum score for grade A",
    )
    grade_b_threshold: int = Field(
        default=80,
        validation_alias="SEO_HEALTH_GRADE_B",
        ge=0,
        le=100,
        description="Minimum score for grade B",
    )
    grade_c_threshold: int = Field(
        default=70,
        validation_alias="SEO_HEALTH_GRADE_C",
        ge=0,
        le=100,
        description="Minimum score for grade C",
    )
    grade_d_threshold: int = Field(
        default=60,
        validation_alias="SEO_HEALTH_GRADE_D",
        ge=0,
        le=100,
        description="Minimum score for grade D",
    )

    # ===========================================
    # AI Systems Configuration
    # ===========================================
    ai_query_timeout: int = Field(
        default=30,
        validation_alias="SEO_HEALTH_AI_TIMEOUT",
        ge=1,
        le=300,
        description="AI query timeout in seconds",
    )
    ai_rate_limit_ms: int = Field(
        default=1000,
        validation_alias="SEO_HEALTH_AI_RATE_LIMIT",
        ge=0,
        description="Rate limit between AI queries in milliseconds",
    )

    # ===========================================
    # Crawl Configuration
    # ===========================================
    crawl_max_depth: int = Field(
        default=50,
        validation_alias="SEO_HEALTH_CRAWL_DEPTH",
        ge=1,
        le=1000,
        description="Maximum crawl depth",
    )
    crawl_timeout: int = Field(
        default=30,
        validation_alias="SEO_HEALTH_CRAWL_TIMEOUT",
        ge=1,
        le=300,
        description="Crawl request timeout in seconds",
    )
    crawl_user_agent: str = Field(
        default="SEO-Health-Report-Bot/1.0 (Technical Audit)",
        validation_alias="SEO_HEALTH_USER_AGENT",
        description="User agent for crawl requests",
    )

    # ===========================================
    # Output Configuration
    # ===========================================
    output_format: str = Field(
        default="docx",
        validation_alias="SEO_HEALTH_OUTPUT_FORMAT",
        description="Default output format (docx, pdf, md)",
    )
    output_dir: str = Field(
        default=".",
        validation_alias="SEO_HEALTH_OUTPUT_DIR",
        description="Default output directory",
    )

    # ===========================================
    # Logging Configuration
    # ===========================================
    log_level: str = Field(
        default="INFO",
        validation_alias="SEO_HEALTH_LOG_LEVEL",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_dir: str = Field(
        default="logs",
        validation_alias="SEO_HEALTH_LOG_DIR",
        description="Log directory",
    )
    log_file: str = Field(
        default="seo-health-report.log",
        validation_alias="SEO_HEALTH_LOG_FILE",
        description="Log file name",
    )
    log_max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        validation_alias="SEO_HEALTH_LOG_MAX_BYTES",
        ge=1024,
        description="Maximum log file size in bytes",
    )
    log_backup_count: int = Field(
        default=5,
        validation_alias="SEO_HEALTH_LOG_BACKUP_COUNT",
        ge=0,
        le=100,
        description="Number of log backup files to keep",
    )

    # ===========================================
    # Content Analysis Configuration
    # ===========================================
    min_content_length: int = Field(
        default=300,
        validation_alias="SEO_HEALTH_MIN_CONTENT_LENGTH",
        ge=0,
        description="Minimum content length in characters",
    )
    max_title_length: int = Field(
        default=60,
        validation_alias="SEO_HEALTH_MAX_TITLE_LENGTH",
        ge=1,
        description="Maximum title length in characters",
    )
    max_description_length: int = Field(
        default=160,
        validation_alias="SEO_HEALTH_MAX_DESC_LENGTH",
        ge=1,
        description="Maximum meta description length in characters",
    )

    # ===========================================
    # Default Brand Colors
    # ===========================================
    default_colors: dict[str, str] = Field(
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
        },
        description="Default brand colors",
    )

    # ===========================================
    # Validators
    # ===========================================

    @field_validator("pagespeed_strategy")
    @classmethod
    def validate_pagespeed_strategy(cls, v: str) -> str:
        valid = ["mobile", "desktop"]
        if v.lower() not in valid:
            raise ValueError(f"pagespeed_strategy must be one of: {', '.join(valid)}")
        return v.lower()

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        valid = ["docx", "pdf", "md"]
        if v.lower() not in valid:
            raise ValueError(f"output_format must be one of: {', '.join(valid)}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid:
            raise ValueError(f"log_level must be one of: {', '.join(valid)}")
        return v.upper()

    @model_validator(mode="after")
    def validate_scoring_weights(self) -> "Settings":
        """Ensure scoring weights sum to 1.0."""
        total = self.score_weight_technical + self.score_weight_content + self.score_weight_ai
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Scoring weights must sum to 1.0 (currently: {total:.2f}). "
                f"Technical={self.score_weight_technical}, "
                f"Content={self.score_weight_content}, "
                f"AI={self.score_weight_ai}"
            )
        return self

    @model_validator(mode="after")
    def validate_grade_thresholds(self) -> "Settings":
        """Ensure grade thresholds are in descending order."""
        if not (
            self.grade_a_threshold
            > self.grade_b_threshold
            > self.grade_c_threshold
            > self.grade_d_threshold
            > 0
        ):
            raise ValueError(
                f"Grade thresholds must be in descending order: A > B > C > D > 0. "
                f"Got: A={self.grade_a_threshold}, B={self.grade_b_threshold}, "
                f"C={self.grade_c_threshold}, D={self.grade_d_threshold}"
            )
        return self

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Check production security requirements."""
        env = get_current_environment()
        if env.is_production:
            if not self.jwt_secret_key:
                raise ValueError("JWT_SECRET_KEY is required in production")
            if self.jwt_secret_key and len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
        return self

    # ===========================================
    # Convenience Properties
    # ===========================================

    @property
    def environment(self) -> Environment:
        """Get the current environment as an enum."""
        return Environment.from_string(self.app_env)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.is_production

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.is_development

    @property
    def effective_google_api_key(self) -> Optional[str]:
        """Get the effective Google API key with fallback chain."""
        return self.google_api_key

    @property
    def effective_gemini_api_key(self) -> Optional[str]:
        """Get the effective Gemini API key with fallback chain."""
        return self.google_gemini_api_key or self.google_api_key

    @property
    def effective_kg_api_key(self) -> Optional[str]:
        """Get the effective Knowledge Graph API key with fallback chain."""
        return self.google_kg_api_key or self.google_api_key

    @property
    def effective_pagespeed_api_key(self) -> Optional[str]:
        """Get the effective PageSpeed API key with fallback chain."""
        return self.pagespeed_api_key or self.google_api_key

    @property
    def log_file_path(self) -> Path:
        """Get the full path to the log file."""
        return Path(self.log_dir) / self.log_file

    @property
    def ai_systems_priority(self) -> list[str]:
        """Get the priority list of AI systems to query."""
        return ["claude", "openai", "perplexity"]

    @property
    def pagespeed_categories(self) -> list[str]:
        """Get the PageSpeed categories to audit."""
        return ["performance", "accessibility", "best-practices", "seo"]

    # ===========================================
    # Helper Methods
    # ===========================================

    def get_color(self, color_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a brand color by name."""
        return self.default_colors.get(color_name, default)

    def get_grade_color(self, score: int) -> str:
        """Get color based on score/grade."""
        if score >= self.grade_a_threshold:
            return self.default_colors.get("success", "#34a853")
        elif score >= self.grade_c_threshold:
            return self.default_colors.get("warning", "#fbbc04")
        else:
            return self.default_colors.get("danger", "#ea4335")

    def get_grade(self, score: int) -> str:
        """Get letter grade from numeric score."""
        if score >= self.grade_a_threshold:
            return "A"
        elif score >= self.grade_b_threshold:
            return "B"
        elif score >= self.grade_c_threshold:
            return "C"
        elif score >= self.grade_d_threshold:
            return "D"
        else:
            return "F"


# Module-level cached settings instance
_settings_instance: Optional[Settings] = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get the singleton Settings instance.

    Uses lru_cache to ensure only one instance is created.

    Returns:
        Settings instance
    """
    return Settings()


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.

    Clears the cache and creates a new Settings instance.

    Returns:
        New Settings instance
    """
    get_settings.cache_clear()
    return get_settings()


__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
]
