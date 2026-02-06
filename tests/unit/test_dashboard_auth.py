"""Unit tests for dashboard session-based authentication."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from apps.dashboard.auth import (
    SESSION_COOKIE_NAME,
    _sessions,
    cleanup_expired_sessions,
    clear_session_cookie,
    create_session,
    delete_session,
    get_current_dashboard_user,
    get_session,
    require_dashboard_auth,
    set_session_cookie,
)
from apps.dashboard.routes import router
from database import get_db

app = FastAPI()
app.include_router(router, prefix="/dashboard")


class MockUser:
    """Mock user for testing."""
    def __init__(self, id="user_123", email="test@example.com", tenant_id=None, role="user"):
        self.id = id
        self.email = email
        self.tenant_id = tenant_id
        self.role = role


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear sessions before and after each test."""
    _sessions.clear()
    yield
    _sessions.clear()


class TestCreateSession:
    """Tests for create_session function."""

    def test_creates_session_with_valid_data(self):
        session_id = create_session("user_123", "tenant_456", "admin")

        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        assert session_id in _sessions

    def test_session_contains_correct_data(self):
        session_id = create_session("user_123", "tenant_456", "admin")
        session = _sessions[session_id]

        assert session["user_id"] == "user_123"
        assert session["tenant_id"] == "tenant_456"
        assert session["role"] == "admin"
        assert "created_at" in session
        assert "expires_at" in session

    def test_session_with_none_tenant(self):
        session_id = create_session("user_123", None, "user")
        session = _sessions[session_id]

        assert session["tenant_id"] is None

    def test_creates_unique_session_ids(self):
        id1 = create_session("user_1", None, "user")
        id2 = create_session("user_2", None, "user")

        assert id1 != id2


class TestGetSession:
    """Tests for get_session function."""

    def test_returns_valid_session(self):
        session_id = create_session("user_123", "tenant_456", "admin")
        session = get_session(session_id)

        assert session is not None
        assert session["user_id"] == "user_123"

    def test_returns_none_for_invalid_id(self):
        session = get_session("invalid-session-id")

        assert session is None

    def test_returns_none_for_expired_session(self):
        session_id = create_session("user_123", None, "user")

        expired_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        _sessions[session_id]["expires_at"] = expired_time

        session = get_session(session_id)

        assert session is None
        assert session_id not in _sessions


class TestDeleteSession:
    """Tests for delete_session function."""

    def test_deletes_existing_session(self):
        session_id = create_session("user_123", None, "user")
        assert session_id in _sessions

        delete_session(session_id)

        assert session_id not in _sessions

    def test_handles_nonexistent_session(self):
        delete_session("nonexistent-id")


class TestSetSessionCookie:
    """Tests for set_session_cookie function."""

    def test_sets_cookie_with_correct_attributes(self):
        from fastapi.responses import Response
        response = Response()

        set_session_cookie(response, "test-session-id")

        cookie_header = response.headers.get("set-cookie", "")
        assert SESSION_COOKIE_NAME in cookie_header
        assert "httponly" in cookie_header.lower()
        assert "samesite=lax" in cookie_header.lower()
        assert "path=/dashboard" in cookie_header.lower()


class TestClearSessionCookie:
    """Tests for clear_session_cookie function."""

    def test_clears_cookie(self):
        from fastapi.responses import Response
        response = Response()

        clear_session_cookie(response)

        cookie_header = response.headers.get("set-cookie", "")
        assert SESSION_COOKIE_NAME in cookie_header


class TestGetCurrentDashboardUser:
    """Tests for get_current_dashboard_user function."""

    def test_returns_none_without_cookie(self):
        request = MagicMock()
        request.cookies = {}
        db = MagicMock()

        result = get_current_dashboard_user(request, db)

        assert result is None

    def test_returns_none_for_invalid_session(self):
        request = MagicMock()
        request.cookies = {SESSION_COOKIE_NAME: "invalid-session"}
        db = MagicMock()

        result = get_current_dashboard_user(request, db)

        assert result is None

    def test_returns_user_for_valid_session(self):
        session_id = create_session("user_123", "tenant_456", "admin")

        request = MagicMock()
        request.cookies = {SESSION_COOKIE_NAME: session_id}

        mock_user = MockUser(id="user_123", tenant_id="tenant_456", role="admin")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_current_dashboard_user(request, db)

        assert result is not None
        assert result["id"] == "user_123"
        assert result["tenant_id"] == "tenant_456"
        assert result["role"] == "admin"

    def test_deletes_session_when_user_not_found(self):
        session_id = create_session("user_123", None, "user")

        request = MagicMock()
        request.cookies = {SESSION_COOKIE_NAME: session_id}

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_current_dashboard_user(request, db)

        assert result is None
        assert session_id not in _sessions


class TestRequireDashboardAuth:
    """Tests for require_dashboard_auth dependency."""

    def test_raises_401_without_session(self):
        request = MagicMock()
        request.cookies = {}
        db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            require_dashboard_auth(request, db)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    def test_returns_user_with_valid_session(self):
        session_id = create_session("user_123", "tenant_456", "admin")

        request = MagicMock()
        request.cookies = {SESSION_COOKIE_NAME: session_id}

        mock_user = MockUser(id="user_123", tenant_id="tenant_456", role="admin")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_user

        result = require_dashboard_auth(request, db)

        assert result["id"] == "user_123"


class TestCleanupExpiredSessions:
    """Tests for cleanup_expired_sessions function."""

    def test_removes_expired_sessions(self):
        valid_session = create_session("user_1", None, "user")
        expired_session = create_session("user_2", None, "user")

        expired_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        _sessions[expired_session]["expires_at"] = expired_time

        removed = cleanup_expired_sessions()

        assert removed == 1
        assert valid_session in _sessions
        assert expired_session not in _sessions

    def test_returns_zero_when_no_expired_sessions(self):
        create_session("user_1", None, "user")

        removed = cleanup_expired_sessions()

        assert removed == 0


class TestDashboardRoutesIntegration:
    """Integration tests for dashboard routes with session auth."""

    @pytest.fixture
    def client(self):
        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_db] = mock_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_login_page_accessible(self, client):
        response = client.get("/dashboard/login", follow_redirects=False)
        assert response.status_code == 200

    def test_audits_requires_auth(self, client):
        response = client.get("/dashboard/audits", follow_redirects=False)
        assert response.status_code == 401

    def test_logout_clears_session(self, client):
        session_id = create_session("user_123", None, "user")

        response = client.post(
            "/dashboard/logout",
            cookies={SESSION_COOKIE_NAME: session_id},
            follow_redirects=False
        )

        assert response.status_code == 302
        assert "/dashboard/login" in response.headers.get("location", "")
        assert session_id not in _sessions

    def test_login_creates_session_on_success(self, client):
        mock_user = MockUser(id="user_123", tenant_id="tenant_456", role="user")

        with patch("apps.dashboard.routes.authenticate_user", return_value=mock_user):
            response = client.post(
                "/dashboard/login",
                data={"email": "test@example.com", "password": "password123"},
                follow_redirects=False
            )

        assert response.status_code == 302
        assert "/dashboard/audits" in response.headers.get("location", "")

        set_cookie = response.headers.get("set-cookie", "")
        assert SESSION_COOKIE_NAME in set_cookie

    def test_login_returns_error_on_failure(self, client):
        with patch("apps.dashboard.routes.authenticate_user", return_value=None):
            response = client.post(
                "/dashboard/login",
                data={"email": "test@example.com", "password": "wrongpassword"},
                follow_redirects=False
            )

        assert response.status_code == 401
