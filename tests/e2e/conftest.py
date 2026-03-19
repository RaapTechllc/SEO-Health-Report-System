"""
Shared fixtures for E2E tests.

Provides authenticated clients, mock services, and test data fixtures.
"""

import os
import sys
import uuid
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_e2e.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-e2e-tests")
os.environ.setdefault("TESTING", "true")
os.environ["RATE_LIMIT_REQUESTS_PER_MINUTE"] = "10000"
os.environ["RATE_LIMIT_AUDITS_PER_DAY"] = "1000"

mock_stripe = MagicMock()
mock_stripe.checkout.Session.create = MagicMock(return_value=MagicMock(
    id="cs_test_123",
    url="https://checkout.stripe.com/test"
))
sys.modules['stripe'] = mock_stripe

from fastapi.testclient import TestClient


def _create_audit_jobs_table(engine):
    """Create audit_jobs table for testing (matches migration v002)."""
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_jobs (
                job_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL DEFAULT 'default',
                audit_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                idempotency_key TEXT UNIQUE,
                payload_json TEXT,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                error_message TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_progress_events (
                event_id TEXT PRIMARY KEY,
                audit_id TEXT NOT NULL,
                job_id TEXT,
                phase TEXT NOT NULL,
                percent INTEGER DEFAULT 0,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()


@pytest.fixture(scope="module")
def app():
    """Get the FastAPI application instance with initialized database."""
    from database import engine, init_db
    init_db()
    _create_audit_jobs_table(engine)
    from apps.api.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create a test client for the API."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def unique_email() -> str:
    """Generate a unique test email."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def test_password() -> str:
    """Standard test password."""
    return "TestPassword123!"


@pytest.fixture
def registered_user(client: TestClient, unique_email: str, test_password: str) -> dict[str, Any]:
    """Register a new user and return credentials with token."""
    response = client.post(
        "/auth/register",
        json={"email": unique_email, "password": test_password}
    )
    assert response.status_code == 200, f"Registration failed: {response.text}"
    data = response.json()
    return {
        "email": unique_email,
        "password": test_password,
        "user_id": data["user_id"],
        "token": data["access_token"],
    }


@pytest.fixture
def auth_headers(registered_user: dict[str, Any]) -> dict[str, str]:
    """Get authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {registered_user['token']}"}


@pytest.fixture
def mock_external_calls():
    """Mock all external HTTP calls for isolated testing."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        async def mock_get(url, **kwargs):
            response = MagicMock()
            response.status_code = 200
            response.text = "<html><head><title>Test</title></head><body>Test</body></html>"
            response.headers = {"content-type": "text/html"}
            return response

        mock_instance.get = mock_get
        yield mock_instance


@pytest.fixture
def mock_audit_execution():
    """Mock the audit execution to return quickly with realistic results."""
    mock_result = {
        "url": "https://example-plumber.test",
        "company_name": "Example Plumbing Co",
        "timestamp": "2024-01-15T10:00:00",
        "audits": {
            "technical": {
                "score": 85,
                "grade": "B",
                "components": {
                    "crawlability": {"score": 18, "max": 20},
                    "indexing": {"score": 14, "max": 15},
                    "speed": {"score": 22, "max": 25},
                    "mobile": {"score": 13, "max": 15},
                    "security": {"score": 9, "max": 10},
                    "structured_data": {"score": 12, "max": 15},
                },
                "issues": [],
                "recommendations": [],
            },
            "content": {
                "score": 80,
                "grade": "B",
                "components": {},
                "issues": [],
                "recommendations": [],
            },
            "ai_visibility": {
                "score": 78,
                "grade": "C",
                "components": {},
                "issues": [],
                "recommendations": [],
            },
        },
        "warnings": [],
        "errors": [],
    }

    with patch("scripts.orchestrate.run_full_audit") as mock_run:
        async def async_mock(*args, **kwargs):
            return mock_result
        mock_run.side_effect = async_mock
        yield mock_run


@pytest.fixture
def mock_audit_with_errors():
    """Mock audit execution that returns partial results with errors."""
    mock_result = {
        "url": "https://broken-sitemap.test",
        "company_name": "Broken Sitemap HVAC",
        "timestamp": "2024-01-15T10:00:00",
        "audits": {
            "technical": {
                "score": 55,
                "grade": "D",
                "components": {
                    "crawlability": {"score": 15, "max": 20},
                    "indexing": {"score": 5, "max": 15},
                    "speed": {"score": 20, "max": 25},
                    "mobile": {"score": 12, "max": 15},
                    "security": {"score": 8, "max": 10},
                    "structured_data": {"score": 10, "max": 15},
                },
                "issues": [
                    {"severity": "critical", "description": "Sitemap not found"},
                    {"severity": "high", "description": "No sitemap reference in robots.txt"},
                ],
                "recommendations": [
                    {"priority": "high", "action": "Create and submit an XML sitemap"},
                ],
            },
            "content": {
                "score": 60,
                "grade": "D",
                "components": {},
                "issues": [],
                "recommendations": [],
            },
            "ai_visibility": {
                "score": 55,
                "grade": "D",
                "components": {},
                "issues": [],
                "recommendations": [],
            },
        },
        "warnings": ["Some pages could not be crawled"],
        "errors": ["Failed to fetch sitemap: 404 Not Found"],
    }

    with patch("scripts.orchestrate.run_full_audit") as mock_run:
        async def async_mock(*args, **kwargs):
            return mock_result
        mock_run.side_effect = async_mock
        yield mock_run


@pytest.fixture
def fixture_sites():
    """Get test fixture sites."""
    from tests.fixtures.sites import FIXTURE_SITES, get_fixture
    return {"all": FIXTURE_SITES, "get": get_fixture}


@pytest.fixture
def mock_pagespeed():
    """Mock PageSpeed Insights API calls."""
    mock_response = {
        "lighthouseResult": {
            "categories": {
                "performance": {"score": 0.85},
                "accessibility": {"score": 0.90},
                "best-practices": {"score": 0.88},
                "seo": {"score": 0.92},
            },
            "audits": {
                "largest-contentful-paint": {"numericValue": 1800},
                "first-input-delay": {"numericValue": 50},
                "cumulative-layout-shift": {"numericValue": 0.05},
                "speed-index": {"numericValue": 2000},
            }
        }
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        async def mock_get(url, **kwargs):
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = mock_response
            return response

        mock_instance.get = mock_get
        yield mock_instance


@pytest.fixture
def mock_ai_calls():
    """Mock AI/LLM API calls for visibility analysis."""
    with patch("openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test AI response for visibility analysis."

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        yield mock_client


@pytest.fixture
def temp_report_dir(tmp_path):
    """Create temporary directory for report files."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    return str(reports_dir)


@pytest.fixture
def mock_report_files(temp_report_dir):
    """Create mock report files for download testing."""
    import json

    audit_id = "audit_test123456"

    html_path = os.path.join(temp_report_dir, f"{audit_id}_report.html")
    with open(html_path, "w") as f:
        f.write("<html><body><h1>SEO Report</h1></body></html>")

    pdf_path = os.path.join(temp_report_dir, f"{audit_id}_PREMIUM.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n%Mock PDF content\n")

    json_path = os.path.join(temp_report_dir, f"{audit_id}_results.json")
    with open(json_path, "w") as f:
        json.dump({"score": 85, "grade": "B"}, f)

    return {
        "audit_id": audit_id,
        "html_path": html_path,
        "pdf_path": pdf_path,
        "json_path": json_path,
    }


@pytest.fixture
def dashboard_session(client: TestClient, registered_user: dict[str, Any]):
    """Create a dashboard session with cookies for HTML-based tests."""
    login_response = client.post(
        "/dashboard/login",
        data={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
        follow_redirects=False,
    )

    cookies = {}
    for cookie in login_response.cookies.jar:
        cookies[cookie.name] = cookie.value

    return {
        "cookies": cookies,
        "user": registered_user,
    }
