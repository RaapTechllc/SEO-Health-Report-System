"""Integration tests for webhook API endpoints."""

import sys
from unittest.mock import MagicMock

# Mock stripe before any imports that might need it
sys.modules.setdefault("stripe", MagicMock())

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_auth_user():
    """Create a mock authenticated user with tenant."""
    user = MagicMock()
    user.id = "user_123"
    user.email = "test@example.com"
    user.role = "user"
    user.tenant_id = "tenant_123"
    return user


@pytest.fixture
def mock_auth_user_no_tenant():
    """Create a mock user without tenant."""
    user = MagicMock()
    user.id = "user_456"
    user.email = "notenant@example.com"
    user.role = "user"
    user.tenant_id = None
    return user


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    from apps.api.main import app
    return TestClient(app)


@pytest.fixture
def auth_client(mock_auth_user):
    """Create test client with mocked authentication."""
    from apps.api.main import app
    from auth import require_auth

    app.dependency_overrides[require_auth] = lambda: mock_auth_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestCreateWebhook:
    """Tests for POST /webhooks endpoint."""

    def test_create_webhook_requires_auth(self, client):
        response = client.post("/webhooks", json={
            "url": "https://example.com/webhook",
            "events": ["audit.completed"]
        })
        assert response.status_code == 401

    def test_create_webhook_requires_tenant(self, mock_auth_user_no_tenant):
        from apps.api.main import app
        from auth import require_auth

        app.dependency_overrides[require_auth] = lambda: mock_auth_user_no_tenant
        client = TestClient(app)

        response = client.post(
            "/webhooks",
            json={
                "url": "https://example.com/webhook",
                "events": ["audit.completed"]
            },
        )
        app.dependency_overrides.clear()
        assert response.status_code == 400

    def test_create_webhook_validates_url(self, auth_client):
        response = auth_client.post(
            "/webhooks",
            json={
                "url": "not-a-url",
                "events": ["audit.completed"]
            },
        )
        assert response.status_code == 422

    def test_create_webhook_validates_events(self, auth_client):
        response = auth_client.post(
            "/webhooks",
            json={
                "url": "https://example.com/webhook",
                "events": ["invalid.event"]
            },
        )
        assert response.status_code == 422

    def test_create_webhook_requires_events(self, auth_client):
        response = auth_client.post(
            "/webhooks",
            json={
                "url": "https://example.com/webhook",
                "events": []
            },
        )
        assert response.status_code == 422


class TestListWebhooks:
    """Tests for GET /webhooks endpoint."""

    def test_list_webhooks_requires_auth(self, client):
        response = client.get("/webhooks")
        assert response.status_code == 401


class TestGetWebhook:
    """Tests for GET /webhooks/{id} endpoint."""

    def test_get_webhook_requires_auth(self, client):
        response = client.get("/webhooks/wh_123")
        assert response.status_code == 401


class TestDeleteWebhook:
    """Tests for DELETE /webhooks/{id} endpoint."""

    def test_delete_webhook_requires_auth(self, client):
        response = client.delete("/webhooks/wh_123")
        assert response.status_code == 401


class TestGetDeliveries:
    """Tests for GET /webhooks/{id}/deliveries endpoint."""

    def test_get_deliveries_requires_auth(self, client):
        response = client.get("/webhooks/wh_123/deliveries")
        assert response.status_code == 401


class TestTestWebhook:
    """Tests for POST /webhooks/{id}/test endpoint."""

    def test_test_webhook_requires_auth(self, client):
        response = client.post("/webhooks/wh_123/test")
        assert response.status_code == 401
