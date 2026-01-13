"""Pytest configuration and shared fixtures for SEO Health Report tests."""

import os
import sys
import pytest
import importlib.util
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import seo-health-report package dynamically (has hyphen in name)
spec = importlib.util.spec_from_file_location(
    "seo_health_report", os.path.join(project_root, "seo-health-report", "__init__.py")
)
seo_health_report_module = importlib.util.module_from_spec(spec)
sys.modules["seo_health_report"] = seo_health_report_module
spec.loader.exec_module(seo_health_report_module)


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    from seo_health_report.config import Config

    return Config()


@pytest.fixture
def mock_smtp_server(monkeypatch):
    """Mock SMTP server for testing email delivery."""
    import smtplib

    mock_instance = MagicMock()

    def mock_smtp(*args, **kwargs):
        return mock_instance.__enter__.__enter__.return_value

    monkeypatch.setattr(smtplib, "SMTP", mock_smtp)
    return mock_instance


@pytest.fixture
def mock_async_client():
    """Mock async HTTP client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value={"status": 200, "text": "response"})
    client.post = AsyncMock(return_value={"status": 200})
    return client


@pytest.fixture
def mock_scheduled_job():
    """Mock APScheduler job."""
    job = MagicMock()
    job.id = "test-job-id"
    job.next_run_time = "2024-01-10 10:00:00"
    job.kwargs = {"url": "https://example.com"}
    job.trigger = MagicMock()
    return job


@pytest.fixture
def sample_audit_results():
    """Sample audit results for testing."""
    return {
        "audits": {
            "technical": {"score": 75, "issues": [], "recommendations": []},
            "content": {"score": 80, "issues": [], "recommendations": []},
            "ai_visibility": {"score": 70, "issues": [], "recommendations": []},
        },
        "warnings": [],
        "errors": [],
    }


@pytest.fixture
def sample_issues():
    """Sample issues for testing."""
    return [
        {"type": "technical", "severity": "critical", "description": "Issue 1"},
        {"type": "content", "severity": "high", "description": "Issue 2"},
    ]


@pytest.fixture
def sample_recommendations():
    """Sample recommendations for testing."""
    return [
        {"action": "Fix meta tags", "effort": "low", "impact": "high"},
        {"action": "Add schema markup", "effort": "medium", "impact": "medium"},
    ]


@pytest.fixture
def sample_brand_colors():
    """Sample brand colors for testing."""
    return {
        "primary": "#1a73e8",
        "secondary": "#34a853",
        "warning": "#fbbc04",
        "danger": "#ea4335",
    }


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test files."""
    test_dir = tmp_path / "test_output"
    test_dir.mkdir(exist_ok=True)
    return str(test_dir)
