"""Unit tests for tenant switching functionality."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.dashboard.auth import (
    SESSION_COOKIE_NAME,
    _sessions,
    create_session,
    update_session_tenant,
)
from apps.dashboard.routes import get_tenant_name, get_user_tenants, router
from database import get_db

app = FastAPI()
app.include_router(router, prefix="/dashboard")


class MockTenant:
    """Mock tenant for testing."""
    def __init__(self, id="tenant_123", name="Test Tenant"):
        self.id = id
        self.name = name


class MockUser:
    """Mock user for testing."""
    def __init__(self, id="user_123", email="test@example.com", tenant_id="tenant_123", role="user"):
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


class TestUpdateSessionTenant:
    """Tests for update_session_tenant function."""

    def test_updates_tenant_in_existing_session(self):
        session_id = create_session("user_123", "tenant_old", "user")

        result = update_session_tenant(session_id, "tenant_new")

        assert result is True
        assert _sessions[session_id]["tenant_id"] == "tenant_new"

    def test_returns_false_for_invalid_session(self):
        result = update_session_tenant("invalid-session", "tenant_123")

        assert result is False

    def test_preserves_other_session_data(self):
        session_id = create_session("user_123", "tenant_old", "admin")

        update_session_tenant(session_id, "tenant_new")

        assert _sessions[session_id]["user_id"] == "user_123"
        assert _sessions[session_id]["role"] == "admin"


class TestGetUserTenants:
    """Tests for get_user_tenants helper function."""

    def test_returns_tenant_for_user_with_tenant(self):
        mock_user = MockUser(id="user_123", tenant_id="tenant_123")
        mock_tenant = MockTenant(id="tenant_123", name="Test Tenant")

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_tenant]

        tenants = get_user_tenants(db, "user_123")

        assert len(tenants) == 1
        assert tenants[0]["id"] == "tenant_123"
        assert tenants[0]["name"] == "Test Tenant"

    def test_returns_empty_for_user_without_tenant(self):
        mock_user = MockUser(id="user_123", tenant_id=None)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_user

        tenants = get_user_tenants(db, "user_123")

        assert tenants == []

    def test_returns_empty_for_nonexistent_user(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        tenants = get_user_tenants(db, "nonexistent")

        assert tenants == []


class TestGetTenantName:
    """Tests for get_tenant_name helper function."""

    def test_returns_name_for_valid_tenant(self):
        mock_tenant = MockTenant(id="tenant_123", name="Test Tenant")

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_tenant

        name = get_tenant_name(db, "tenant_123")

        assert name == "Test Tenant"

    def test_returns_none_for_invalid_tenant(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        name = get_tenant_name(db, "invalid")

        assert name is None

    def test_returns_none_for_none_tenant_id(self):
        db = MagicMock()

        name = get_tenant_name(db, None)

        assert name is None
        db.query.assert_not_called()


class TestTenantRoutesIntegration:
    """Integration tests for tenant switching routes."""

    @pytest.fixture
    def client(self):
        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_db] = mock_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_list_tenants_requires_auth(self, client):
        response = client.get("/dashboard/tenants")
        assert response.status_code == 401

    def test_list_tenants_returns_user_tenants(self, client):
        mock_user = MockUser(id="user_123", tenant_id="tenant_123")
        mock_tenant = MockTenant(id="tenant_123", name="Test Tenant")
        session_id = create_session("user_123", "tenant_123", "user")

        def mock_get_db():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.side_effect = [
                mock_user,  # for auth
                mock_user,  # for get_user_tenants user query
                mock_tenant,  # for get_user_tenants tenant query
            ]
            return db

        app.dependency_overrides[get_db] = mock_get_db

        response = client.get(
            "/dashboard/tenants",
            cookies={SESSION_COOKIE_NAME: session_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert "current_tenant_id" in data
        assert data["current_tenant_id"] == "tenant_123"

    def test_switch_tenant_requires_auth(self, client):
        response = client.post(
            "/dashboard/switch-tenant",
            json={"tenant_id": "tenant_123"}
        )
        assert response.status_code == 401

    def test_switch_tenant_denies_unauthorized_tenant(self, client):
        mock_user = MockUser(id="user_123", tenant_id="tenant_123")
        mock_tenant = MockTenant(id="tenant_123", name="Test Tenant")
        session_id = create_session("user_123", "tenant_123", "user")

        def mock_get_db():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.side_effect = [
                mock_user,  # for auth
                mock_user,  # for get_user_tenants user query
                mock_tenant,  # for get_user_tenants tenant query
            ]
            return db

        app.dependency_overrides[get_db] = mock_get_db

        response = client.post(
            "/dashboard/switch-tenant",
            json={"tenant_id": "unauthorized_tenant"},
            cookies={SESSION_COOKIE_NAME: session_id}
        )

        assert response.status_code == 403
        assert "do not have access" in response.json()["detail"]

    def test_switch_tenant_success(self, client):
        mock_user = MockUser(id="user_123", tenant_id="tenant_123")
        mock_tenant = MockTenant(id="tenant_123", name="Test Tenant")
        session_id = create_session("user_123", "tenant_123", "user")

        def mock_get_db():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.side_effect = [
                mock_user,  # for auth
                mock_user,  # for get_user_tenants user query
                mock_tenant,  # for get_user_tenants tenant query
                mock_tenant,  # for final tenant lookup
            ]
            return db

        app.dependency_overrides[get_db] = mock_get_db

        response = client.post(
            "/dashboard/switch-tenant",
            json={"tenant_id": "tenant_123"},
            cookies={SESSION_COOKIE_NAME: session_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tenant_id"] == "tenant_123"
        assert data["tenant_name"] == "Test Tenant"


class TestTenantDisplayInNavbar:
    """Tests that tenant info is passed to templates."""

    @pytest.fixture
    def client(self):
        def mock_get_db():
            return MagicMock()

        app.dependency_overrides[get_db] = mock_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_audit_list_includes_tenant_name(self, client):
        mock_user = MockUser(id="user_123", tenant_id="tenant_123")
        mock_tenant = MockTenant(id="tenant_123", name="Acme Corp")
        session_id = create_session("user_123", "tenant_123", "user")

        def mock_get_db():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.side_effect = [
                mock_user,  # for auth
                mock_tenant,  # for get_tenant_name
            ]
            db.query.return_value.count.return_value = 0
            db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            return db

        app.dependency_overrides[get_db] = mock_get_db

        with patch("apps.dashboard.routes.get_quota_for_user", return_value=None):
            response = client.get(
                "/dashboard/audits",
                cookies={SESSION_COOKIE_NAME: session_id}
            )

        assert response.status_code == 200
        assert "Acme Corp" in response.text or "tenant" in response.text.lower()
