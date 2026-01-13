"""
Tests for config module.
"""

import os
import pytest
from seo_health_report.config import Config, get_config, set_config, reload_config


class TestConfigDefaults:
    """Test default configuration values."""

    def test_api_timeout_default(self):
        """Test default API timeout."""
        config = Config()
        assert config.api_timeout == 30

    def test_anthropic_model_default(self):
        """Test default Anthropic model."""
        config = Config()
        assert config.anthropic_model == "claude-sonnet-4-20250514"

    def test_cache_dir_default(self):
        """Test default cache directory."""
        config = Config()
        assert ".seo-health-cache" in config.cache_dir

    def test_cache_ttl_defaults(self):
        """Test default cache TTL values."""
        config = Config()
        assert config.cache_ttl_pagespeed == 86400
        assert config.cache_ttl_ai_response == 604800
        assert config.cache_ttl_http_fetch == 3600

    def test_scoring_weights_default(self):
        """Test default scoring weights sum to 1.0."""
        config = Config()
        total = (
            config.score_weight_technical
            + config.score_weight_content
            + config.score_weight_ai
        )
        assert abs(total - 1.0) < 0.01

    def test_grade_thresholds_default(self):
        """Test default grade thresholds."""
        config = Config()
        assert config.grade_a_threshold == 90
        assert config.grade_b_threshold == 80
        assert config.grade_c_threshold == 70
        assert config.grade_d_threshold == 60

    def test_default_colors_exist(self):
        """Test default colors dictionary exists."""
        config = Config()
        assert "primary" in config.default_colors
        assert "secondary" in config.default_colors
        assert "warning" in config.default_colors
        assert "danger" in config.default_colors

    def test_crawl_config_defaults(self):
        """Test default crawl configuration."""
        config = Config()
        assert config.crawl_max_depth == 50
        assert config.crawl_timeout == 30
        assert "SEO-Health-Report-Bot" in config.crawl_user_agent


class TestConfigEnvironmentVariables:
    """Test configuration from environment variables."""

    def test_api_timeout_from_env(self, monkeypatch):
        """Test API timeout from environment variable."""
        monkeypatch.setenv("SEO_HEALTH_API_TIMEOUT", "60")
        config = Config()
        assert config.api_timeout == 60

    def test_anthropic_model_from_env(self, monkeypatch):
        """Test Anthropic model from environment variable."""
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        config = Config()
        assert config.anthropic_model == "claude-3-opus-20240229"

    def test_cache_dir_from_env(self, monkeypatch):
        """Test cache directory from environment variable."""
        monkeypatch.setenv("SEO_HEALTH_CACHE_DIR", "/tmp/test-cache")
        config = Config()
        assert config.cache_dir == "/tmp/test-cache"

    def test_scoring_weights_from_env(self, monkeypatch):
        """Test scoring weights from environment variables."""
        monkeypatch.setenv("SEO_HEALTH_WEIGHT_TECHNICAL", "0.25")
        monkeypatch.setenv("SEO_HEALTH_WEIGHT_CONTENT", "0.40")
        monkeypatch.setenv("SEO_HEALTH_WEIGHT_AI", "0.35")
        config = Config()
        assert config.score_weight_technical == 0.25
        assert config.score_weight_content == 0.40
        assert config.score_weight_ai == 0.35

    def test_grade_thresholds_from_env(self, monkeypatch):
        """Test grade thresholds from environment variables."""
        monkeypatch.setenv("SEO_HEALTH_GRADE_A", "95")
        monkeypatch.setenv("SEO_HEALTH_GRADE_B", "85")
        monkeypatch.setenv("SEO_HEALTH_GRADE_C", "75")
        monkeypatch.setenv("SEO_HEALTH_GRADE_D", "65")
        config = Config()
        assert config.grade_a_threshold == 95
        assert config.grade_b_threshold == 85
        assert config.grade_c_threshold == 75
        assert config.grade_d_threshold == 65

    def test_log_level_from_env(self, monkeypatch):
        """Test log level from environment variable."""
        monkeypatch.setenv("SEO_HEALTH_LOG_LEVEL", "DEBUG")
        config = Config()
        assert config.log_level == "DEBUG"


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_returns_dict(self):
        """Test validation returns dict with errors and warnings."""
        config = Config()
        validation = config.validate()
        assert isinstance(validation, dict)
        assert "errors" in validation
        assert "warnings" in validation

    def test_validate_no_anthropic_key_warning(self, monkeypatch):
        """Test validation warns when ANTHROPIC_API_KEY missing."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        config = Config()
        validation = config.validate()
        assert len(validation["warnings"]) > 0
        assert any("ANTHROPIC_API_KEY" in w for w in validation["warnings"])

    def test_validate_weights_sum_error(self, monkeypatch):
        """Test validation errors when weights don't sum to 1.0."""
        monkeypatch.setenv("SEO_HEALTH_WEIGHT_TECHNICAL", "0.50")
        monkeypatch.setenv("SEO_HEALTH_WEIGHT_CONTENT", "0.50")
        monkeypatch.setenv("SEO_HEALTH_WEIGHT_AI", "0.50")
        config = Config()
        validation = config.validate()
        assert len(validation["errors"]) > 0
        assert any("sum to 1.0" in e for e in validation["errors"])

    def test_validate_grade_thresholds_error(self, monkeypatch):
        """Test validation errors when grade thresholds invalid."""
        monkeypatch.setenv("SEO_HEALTH_GRADE_A", "60")
        monkeypatch.setenv("SEO_HEALTH_GRADE_B", "80")
        monkeypatch.setenv("SEO_HEALTH_GRADE_C", "90")
        monkeypatch.setenv("SEO_HEALTH_GRADE_D", "70")
        config = Config()
        validation = config.validate()
        assert len(validation["errors"]) > 0

    def test_validate_negative_timeout_error(self, monkeypatch):
        """Test validation errors for negative timeout."""
        monkeypatch.setenv("SEO_HEALTH_API_TIMEOUT", "-1")
        config = Config()
        validation = config.validate()
        assert len(validation["errors"]) > 0
        assert any("timeout" in e.lower() for e in validation["errors"])

    def test_validate_invalid_output_format_warning(self, monkeypatch):
        """Test validation warns for invalid output format."""
        monkeypatch.setenv("SEO_HEALTH_OUTPUT_FORMAT", "invalid")
        config = Config()
        validation = config.validate()
        assert len(validation["warnings"]) > 0
        assert any("output format" in w.lower() for w in validation["warnings"])


class TestConfigHelperMethods:
    """Test configuration helper methods."""

    def test_get_color(self):
        """Test getting color by name."""
        config = Config()
        primary = config.get_color("primary")
        assert primary is not None
        assert primary == config.default_colors["primary"]

    def test_get_color_with_default(self):
        """Test getting color with default fallback."""
        config = Config()
        color = config.get_color("nonexistent", "#000000")
        assert color == "#000000"

    def test_get_page_colors(self):
        """Test getting page color dict."""
        config = Config()
        page_colors = config.get_page_colors()
        assert isinstance(page_colors, dict)
        assert "primary" in page_colors
        assert "secondary" in page_colors
        assert "text" in page_colors
        assert "background" in page_colors

    def test_get_grade_color_high(self):
        """Test grade color for high scores."""
        config = Config()
        color = config.get_grade_color(95)
        assert color == config.default_colors.get("success", "#34a853")

    def test_get_grade_color_medium(self):
        """Test grade color for medium scores."""
        config = Config()
        color = config.get_grade_color(75)
        assert color == "#fbbc04"

    def test_get_grade_color_low(self):
        """Test grade color for low scores."""
        config = Config()
        color = config.get_grade_color(40)
        assert color == config.default_colors.get("danger", "#ea4335")

    def test_get_log_file_path(self, tmp_path, monkeypatch):
        """Test getting log file path."""
        log_dir = str(tmp_path / "logs")
        monkeypatch.setenv("SEO_HEALTH_LOG_DIR", log_dir)

        config = Config()
        log_file = config.get_log_file_path()

        assert log_dir in log_file
        assert "seo-health-report.log" in log_file

    def test_get_log_file_path_creates_dir(self, tmp_path, monkeypatch):
        """Test get_log_file_path creates directory."""
        log_dir = str(tmp_path / "new_logs")
        monkeypatch.setenv("SEO_HEALTH_LOG_DIR", log_dir)

        config = Config()
        log_file = config.get_log_file_path()

        assert os.path.exists(os.path.dirname(log_file))


class TestConfigGlobal:
    """Test global config instance management."""

    def test_get_config_returns_instance(self):
        """Test get_config returns Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_same_instance(self):
        """Test get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_set_config(self):
        """Test set_config changes global instance."""
        custom_config = Config()
        custom_config.api_timeout = 60

        set_config(custom_config)

        retrieved = get_config()
        assert retrieved.api_timeout == 60

    def test_reload_config(self, monkeypatch):
        """Test reload_config creates new instance."""
        monkeypatch.setenv("SEO_HEALTH_API_TIMEOUT", "45")

        # Get initial config
        config1 = get_config()
        initial_timeout = config1.api_timeout

        # Change env and reload
        monkeypatch.setenv("SEO_HEALTH_API_TIMEOUT", "90")
        config2 = reload_config()

        # Should have new value
        assert config2.api_timeout != initial_timeout
        assert config2.api_timeout == 90


class TestConfigDataclass:
    """Test Config dataclass behavior."""

    def test_config_is_mutable(self):
        """Test config values can be modified."""
        config = Config()
        config.api_timeout = 120
        assert config.api_timeout == 120

    def test_config_defaults_independent_instances(self):
        """Test config instances have independent defaults."""
        config1 = Config()
        config2 = Config()

        config1.api_timeout = 100

        assert config2.api_timeout == 30  # Still default
