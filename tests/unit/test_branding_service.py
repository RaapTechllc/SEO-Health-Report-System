"""Unit tests for branding service."""

from unittest.mock import MagicMock, patch

import pytest

from packages.seo_health_report.branding.service import (
    DEFAULT_BRANDING,
    BrandingService,
    validate_hex_color,
)


class TestValidateHexColor:
    """Test hex color validation."""

    def test_valid_colors(self):
        assert validate_hex_color("#1E3A8A") is True
        assert validate_hex_color("#ffffff") is True
        assert validate_hex_color("#000000") is True
        assert validate_hex_color("#FF5733") is True
        assert validate_hex_color("#AbCdEf") is True

    def test_invalid_colors(self):
        assert validate_hex_color("1E3A8A") is False  # missing #
        assert validate_hex_color("#1E3A8") is False  # too short
        assert validate_hex_color("#1E3A8A00") is False  # too long
        assert validate_hex_color("#GGGGGG") is False  # invalid chars
        assert validate_hex_color("red") is False
        assert validate_hex_color("") is False


class TestBrandingServiceGetBranding:
    """Test get_branding method."""

    def test_returns_defaults_when_no_custom_branding(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = BrandingService(mock_db)
        result = service.get_branding("tenant_123")

        assert result["tenant_id"] == "tenant_123"
        assert result["primary_color"] == DEFAULT_BRANDING["primary_color"]
        assert result["secondary_color"] == DEFAULT_BRANDING["secondary_color"]
        assert result["is_custom"] is False

    def test_returns_custom_branding(self):
        mock_branding = MagicMock()
        mock_branding.id = "branding_123"
        mock_branding.tenant_id = "tenant_123"
        mock_branding.logo_url = "https://example.com/logo.png"
        mock_branding.primary_color = "#FF5733"
        mock_branding.secondary_color = "#33FF57"
        mock_branding.footer_text = "Custom Footer"
        mock_branding.created_at = MagicMock()
        mock_branding.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_branding.updated_at = MagicMock()
        mock_branding.updated_at.isoformat.return_value = "2025-01-02T00:00:00"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_branding

        service = BrandingService(mock_db)
        result = service.get_branding("tenant_123")

        assert result["id"] == "branding_123"
        assert result["logo_url"] == "https://example.com/logo.png"
        assert result["primary_color"] == "#FF5733"
        assert result["secondary_color"] == "#33FF57"
        assert result["footer_text"] == "Custom Footer"
        assert result["is_custom"] is True


class TestBrandingServiceUpdateBranding:
    """Test update_branding method."""

    def test_creates_new_branding(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = BrandingService(mock_db)

        with patch.object(service, 'get_branding', return_value={"is_custom": True}):
            service.update_branding(
                tenant_id="tenant_123",
                primary_color="#FF5733",
            )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_updates_existing_branding(self):
        mock_branding = MagicMock()
        mock_branding.primary_color = "#1E3A8A"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_branding

        service = BrandingService(mock_db)

        with patch.object(service, 'get_branding', return_value={"is_custom": True}):
            service.update_branding(
                tenant_id="tenant_123",
                primary_color="#FF5733",
            )

        assert mock_branding.primary_color == "#FF5733"
        mock_db.commit.assert_called()

    def test_validates_primary_color(self):
        mock_db = MagicMock()
        service = BrandingService(mock_db)

        with pytest.raises(ValueError, match="Invalid primary_color format"):
            service.update_branding(
                tenant_id="tenant_123",
                primary_color="invalid",
            )

    def test_validates_secondary_color(self):
        mock_db = MagicMock()
        service = BrandingService(mock_db)

        with pytest.raises(ValueError, match="Invalid secondary_color format"):
            service.update_branding(
                tenant_id="tenant_123",
                secondary_color="not-a-color",
            )

    def test_updates_logo_url(self):
        mock_branding = MagicMock()
        mock_branding.logo_url = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_branding

        service = BrandingService(mock_db)

        with patch.object(service, 'get_branding', return_value={"is_custom": True}):
            service.update_branding(
                tenant_id="tenant_123",
                logo_url="https://example.com/new-logo.png",
            )

        assert mock_branding.logo_url == "https://example.com/new-logo.png"

    def test_updates_footer_text(self):
        mock_branding = MagicMock()
        mock_branding.footer_text = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_branding

        service = BrandingService(mock_db)

        with patch.object(service, 'get_branding', return_value={"is_custom": True}):
            service.update_branding(
                tenant_id="tenant_123",
                footer_text="New Footer Text",
            )

        assert mock_branding.footer_text == "New Footer Text"


class TestBrandingServiceDeleteBranding:
    """Test delete_branding method."""

    def test_deletes_existing_branding(self):
        mock_branding = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_branding

        service = BrandingService(mock_db)
        result = service.delete_branding("tenant_123")

        assert result is True
        mock_db.delete.assert_called_once_with(mock_branding)
        mock_db.commit.assert_called()

    def test_returns_false_when_no_branding(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = BrandingService(mock_db)
        result = service.delete_branding("tenant_123")

        assert result is False
        mock_db.delete.assert_not_called()


class TestBrandingServiceGetReportBranding:
    """Test get_report_branding method."""

    def test_returns_defaults_when_no_tenant(self):
        mock_db = MagicMock()
        service = BrandingService(mock_db)

        result = service.get_report_branding(None)

        assert result == DEFAULT_BRANDING

    def test_returns_tenant_branding(self):
        mock_db = MagicMock()
        service = BrandingService(mock_db)

        with patch.object(service, 'get_branding', return_value={
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#FF5733",
            "secondary_color": "#33FF57",
            "footer_text": "Custom Footer",
        }):
            result = service.get_report_branding("tenant_123")

        assert result["logo_url"] == "https://example.com/logo.png"
        assert result["primary_color"] == "#FF5733"
        assert result["secondary_color"] == "#33FF57"
        assert result["footer_text"] == "Custom Footer"
