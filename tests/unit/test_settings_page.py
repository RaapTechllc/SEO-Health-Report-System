"""Unit tests for settings page and password change functionality."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.dashboard.auth import (
    SESSION_COOKIE_NAME,
    _sessions,
    create_session,
)
from apps.dashboard.routes import router
from database import get_db

app = FastAPI()
app.include_router(router, prefix="/dashboard")


class MockUser:
    """Mock user for testing."""
    def __init__(
        self,
        id="user_123",
        email="test@example.com",
        tenant_id=None,
        role="user",
        password_hash="salt:hash",
        created_at=None
    ):
        self.id = id
        self.email = email
        self.tenant_id = tenant_id
        self.role = role
        self.password_hash = password_hash
        self.created_at = created_at or datetime.utcnow()


class MockTenant:
    """Mock tenant for testing."""
    def __init__(self, id="tenant_456", name="Test Org", settings_json=None):
        self.id = id
        self.name = name
        self.settings_json = settings_json


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear sessions before and after each test."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def client(mock_db):
    """Create test client with mocked database."""
    def mock_get_db():
        return mock_db

    app.dependency_overrides[get_db] = mock_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestSettingsPage:
    """Tests for GET /dashboard/settings."""

    def test_settings_requires_auth(self, client):
        """Settings page requires authentication."""
        response = client.get("/dashboard/settings", follow_redirects=False)
        assert response.status_code == 401

    def test_settings_page_loads_for_authenticated_user(self, client, mock_db):
        """Settings page loads successfully for authenticated user."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.get(
            "/dashboard/settings",
            cookies={SESSION_COOKIE_NAME: session_id},
            follow_redirects=False
        )

        assert response.status_code == 200
        assert b"Account Settings" in response.content
        assert b"test@example.com" in response.content

    def test_settings_shows_user_role(self, client, mock_db):
        """Settings page displays user role."""
        session_id = create_session("user_123", None, "admin")
        mock_user = MockUser(role="admin")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.get(
            "/dashboard/settings",
            cookies={SESSION_COOKIE_NAME: session_id},
            follow_redirects=False
        )

        assert response.status_code == 200
        assert b"admin" in response.content.lower()

    def test_settings_shows_tenant_info_when_available(self, client, mock_db):
        """Settings page shows tenant information if user has a tenant."""
        session_id = create_session("user_123", "tenant_456", "user")
        mock_user = MockUser(tenant_id="tenant_456")
        mock_tenant = MockTenant(settings_json={"tier": "pro"})

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,   # for require_dashboard_auth -> get_current_dashboard_user
            mock_user,   # for settings_page user_record lookup
            mock_tenant, # for get_tenant_name
            mock_tenant, # for tenant_info lookup in settings_page
        ]

        with patch("apps.dashboard.routes.get_quota_for_user", return_value=None):
            response = client.get(
                "/dashboard/settings",
                cookies={SESSION_COOKIE_NAME: session_id},
                follow_redirects=False
            )

        assert response.status_code == 200
        assert b"Test Org" in response.content
        assert b"pro" in response.content.lower()

    def test_settings_shows_branding_link_for_admin(self, client, mock_db):
        """Admin users see link to branding settings."""
        session_id = create_session("user_123", "tenant_456", "admin")
        mock_user = MockUser(role="admin", tenant_id="tenant_456")
        mock_tenant = MockTenant()

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,   # for require_dashboard_auth -> get_current_dashboard_user
            mock_user,   # for settings_page user_record lookup
            mock_tenant, # for get_tenant_name
            mock_tenant, # for tenant_info lookup in settings_page
        ]

        with patch("apps.dashboard.routes.get_quota_for_user", return_value=None):
            response = client.get(
                "/dashboard/settings",
                cookies={SESSION_COOKIE_NAME: session_id},
                follow_redirects=False
            )

        assert response.status_code == 200
        assert b"Manage Branding Settings" in response.content

    def test_settings_hides_branding_link_for_non_admin(self, client, mock_db):
        """Non-admin users don't see branding settings link."""
        session_id = create_session("user_123", "tenant_456", "user")
        mock_user = MockUser(role="user", tenant_id="tenant_456")
        mock_tenant = MockTenant()

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,   # for require_dashboard_auth -> get_current_dashboard_user
            mock_user,   # for settings_page user_record lookup
            mock_tenant, # for get_tenant_name
            mock_tenant, # for tenant_info lookup in settings_page
        ]

        with patch("apps.dashboard.routes.get_quota_for_user", return_value=None):
            response = client.get(
                "/dashboard/settings",
                cookies={SESSION_COOKIE_NAME: session_id},
                follow_redirects=False
            )

        assert response.status_code == 200
        assert b"Manage Branding Settings" not in response.content

    def test_settings_displays_success_message(self, client, mock_db):
        """Settings page displays success message from query param."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.get(
            "/dashboard/settings?success=Password+updated+successfully",
            cookies={SESSION_COOKIE_NAME: session_id},
            follow_redirects=False
        )

        assert response.status_code == 200
        assert b"Password updated successfully" in response.content

    def test_settings_displays_error_message(self, client, mock_db):
        """Settings page displays error message from query param."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.get(
            "/dashboard/settings?error=Current+password+is+incorrect",
            cookies={SESSION_COOKIE_NAME: session_id},
            follow_redirects=False
        )

        assert response.status_code == 200
        assert b"Current password is incorrect" in response.content


class TestChangePassword:
    """Tests for POST /dashboard/settings/password."""

    def test_change_password_requires_auth(self, client):
        """Password change requires authentication."""
        response = client.post(
            "/dashboard/settings/password",
            data={
                "current_password": "old",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
            follow_redirects=False
        )
        assert response.status_code == 401

    def test_change_password_validates_password_match(self, client, mock_db):
        """Password change fails if new passwords don't match."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.post(
            "/dashboard/settings/password",
            data={
                "current_password": "old",
                "new_password": "newpassword123",
                "confirm_password": "differentpassword",
            },
            cookies={SESSION_COOKIE_NAME: session_id},
            follow_redirects=False
        )

        assert response.status_code == 302
        assert "error=Passwords+do+not+match" in response.headers.get("location", "")

    def test_change_password_validates_minimum_length(self, client, mock_db):
        """Password change fails if new password is too short."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.post(
            "/dashboard/settings/password",
            data={
                "current_password": "old",
                "new_password": "short",
                "confirm_password": "short",
            },
            cookies={SESSION_COOKIE_NAME: session_id},
            follow_redirects=False
        )

        assert response.status_code == 302
        assert "error=Password+must+be+at+least+8+characters" in response.headers.get("location", "")

    def test_change_password_validates_current_password(self, client, mock_db):
        """Password change fails if current password is wrong."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser(password_hash="salt:correcthash")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("apps.dashboard.routes.verify_password", return_value=False):
            response = client.post(
                "/dashboard/settings/password",
                data={
                    "current_password": "wrongpassword",
                    "new_password": "newpassword123",
                    "confirm_password": "newpassword123",
                },
                cookies={SESSION_COOKIE_NAME: session_id},
                follow_redirects=False
            )

        assert response.status_code == 302
        assert "error=Current+password+is+incorrect" in response.headers.get("location", "")

    def test_change_password_success(self, client, mock_db):
        """Password change succeeds with valid data."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser(password_hash="salt:correcthash")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("apps.dashboard.routes.verify_password", return_value=True):
            with patch("apps.dashboard.routes.hash_password", return_value="newsalt:newhash"):
                response = client.post(
                    "/dashboard/settings/password",
                    data={
                        "current_password": "correctpassword",
                        "new_password": "newpassword123",
                        "confirm_password": "newpassword123",
                    },
                    cookies={SESSION_COOKIE_NAME: session_id},
                    follow_redirects=False
                )

        assert response.status_code == 302
        assert "success=Password+updated+successfully" in response.headers.get("location", "")
        mock_db.commit.assert_called_once()

    def test_change_password_updates_hash(self, client, mock_db):
        """Password change updates the password hash in database."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser(password_hash="oldsalt:oldhash")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("apps.dashboard.routes.verify_password", return_value=True):
            with patch("apps.dashboard.routes.hash_password", return_value="newsalt:newhash") as mock_hash:
                client.post(
                    "/dashboard/settings/password",
                    data={
                        "current_password": "correctpassword",
                        "new_password": "newpassword123",
                        "confirm_password": "newpassword123",
                    },
                    cookies={SESSION_COOKIE_NAME: session_id},
                    follow_redirects=False
                )

        mock_hash.assert_called_once_with("newpassword123")
        assert mock_user.password_hash == "newsalt:newhash"


class TestNavbarSettingsLink:
    """Tests to verify settings link appears in navbar."""

    def test_navbar_has_settings_link(self, client, mock_db):
        """Navbar contains settings link when authenticated."""
        session_id = create_session("user_123", None, "user")
        mock_user = MockUser()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.get(
            "/dashboard/settings",
            cookies={SESSION_COOKIE_NAME: session_id},
            follow_redirects=False
        )

        assert response.status_code == 200
        assert b'href="/dashboard/settings"' in response.content
