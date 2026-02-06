"""Unit tests for branding API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers.branding import router
from auth import require_auth
from database import get_db

app = FastAPI()
app.include_router(router)


class MockUser:
    """Mock user for testing."""
    def __init__(self, tenant_id=None):
        self.id = "user_123"
        self.email = "test@example.com"
        self.tenant_id = tenant_id
        self.role = "user"


def get_mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_user_with_tenant():
    return MockUser(tenant_id="tenant_123")


@pytest.fixture
def mock_user_without_tenant():
    return MockUser(tenant_id=None)


@pytest.fixture
def client_with_tenant(mock_user_with_tenant):
    """Client with authenticated user that has a tenant."""
    app.dependency_overrides[require_auth] = lambda: mock_user_with_tenant
    app.dependency_overrides[get_db] = get_mock_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_without_tenant(mock_user_without_tenant):
    """Client with authenticated user that has no tenant."""
    app.dependency_overrides[require_auth] = lambda: mock_user_without_tenant
    app.dependency_overrides[get_db] = get_mock_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestGetBranding:
    """Test GET /tenant/branding endpoint."""

    def test_returns_branding_for_authenticated_user(self, client_with_tenant):
        mock_branding = {
            "id": "branding_123",
            "tenant_id": "tenant_123",
            "logo_url": None,
            "primary_color": "#1E3A8A",
            "secondary_color": "#3B82F6",
            "footer_text": None,
            "is_custom": False,
        }

        with patch("apps.api.routers.branding.BrandingService") as MockService:
            MockService.return_value.get_branding.return_value = mock_branding
            response = client_with_tenant.get("/tenant/branding")

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "tenant_123"
        assert data["primary_color"] == "#1E3A8A"

    def test_returns_400_when_no_tenant(self, client_without_tenant):
        response = client_without_tenant.get("/tenant/branding")

        assert response.status_code == 400
        assert "User must belong to a tenant" in response.json()["detail"]


class TestUpdateBranding:
    """Test PATCH /tenant/branding endpoint."""

    def test_updates_branding_successfully(self, client_with_tenant):
        mock_branding = {
            "id": "branding_123",
            "tenant_id": "tenant_123",
            "logo_url": None,
            "primary_color": "#FF5733",
            "secondary_color": "#3B82F6",
            "footer_text": None,
            "is_custom": True,
        }

        with patch("apps.api.routers.branding.BrandingService") as MockService:
            MockService.return_value.update_branding.return_value = mock_branding
            response = client_with_tenant.patch(
                "/tenant/branding",
                json={"primary_color": "#FF5733"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["primary_color"] == "#FF5733"

    def test_validates_color_format(self, client_with_tenant):
        response = client_with_tenant.patch(
            "/tenant/branding",
            json={"primary_color": "invalid-color"}
        )

        assert response.status_code == 422  # Validation error

    def test_returns_400_when_no_tenant(self, client_without_tenant):
        response = client_without_tenant.patch(
            "/tenant/branding",
            json={"primary_color": "#FF5733"}
        )

        assert response.status_code == 400

    def test_updates_logo_url(self, client_with_tenant):
        mock_branding = {
            "id": "branding_123",
            "tenant_id": "tenant_123",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#1E3A8A",
            "secondary_color": "#3B82F6",
            "footer_text": None,
            "is_custom": True,
        }

        with patch("apps.api.routers.branding.BrandingService") as MockService:
            MockService.return_value.update_branding.return_value = mock_branding
            response = client_with_tenant.patch(
                "/tenant/branding",
                json={"logo_url": "https://example.com/logo.png"}
            )

        assert response.status_code == 200
        assert response.json()["logo_url"] == "https://example.com/logo.png"

    def test_updates_footer_text(self, client_with_tenant):
        mock_branding = {
            "id": "branding_123",
            "tenant_id": "tenant_123",
            "logo_url": None,
            "primary_color": "#1E3A8A",
            "secondary_color": "#3B82F6",
            "footer_text": "Custom Footer",
            "is_custom": True,
        }

        with patch("apps.api.routers.branding.BrandingService") as MockService:
            MockService.return_value.update_branding.return_value = mock_branding
            response = client_with_tenant.patch(
                "/tenant/branding",
                json={"footer_text": "Custom Footer"}
            )

        assert response.status_code == 200
        assert response.json()["footer_text"] == "Custom Footer"


class TestDeleteBranding:
    """Test DELETE /tenant/branding endpoint."""

    def test_deletes_branding_successfully(self, client_with_tenant):
        with patch("apps.api.routers.branding.BrandingService") as MockService:
            MockService.return_value.delete_branding.return_value = True
            response = client_with_tenant.delete("/tenant/branding")

        assert response.status_code == 204

    def test_returns_400_when_no_tenant(self, client_without_tenant):
        response = client_without_tenant.delete("/tenant/branding")

        assert response.status_code == 400


class TestColorValidation:
    """Test color validation in request model."""

    def test_accepts_valid_colors(self, client_with_tenant):
        valid_colors = ["#1E3A8A", "#ffffff", "#000000", "#AbCdEf"]

        for color in valid_colors:
            with patch("apps.api.routers.branding.BrandingService") as MockService:
                MockService.return_value.update_branding.return_value = {
                    "id": "x", "tenant_id": "t", "logo_url": None,
                    "primary_color": color, "secondary_color": "#000000",
                    "footer_text": None, "is_custom": True
                }
                response = client_with_tenant.patch(
                    "/tenant/branding",
                    json={"primary_color": color}
                )

            assert response.status_code == 200, f"Color {color} should be valid"

    def test_rejects_invalid_colors(self, client_with_tenant):
        invalid_colors = ["red", "1E3A8A", "#1E3A8", "#GGGGGG", "rgb(0,0,0)"]

        for color in invalid_colors:
            response = client_with_tenant.patch(
                "/tenant/branding",
                json={"primary_color": color}
            )

            assert response.status_code == 422, f"Color {color} should be invalid"
