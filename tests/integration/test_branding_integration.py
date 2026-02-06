"""Integration tests for tenant branding system."""

import sys
import uuid
from unittest.mock import MagicMock

sys.modules.setdefault("stripe", MagicMock())

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Tenant
from packages.seo_health_report.branding import (
    DEFAULT_BRANDING,
    BrandingService,
    apply_html_branding,
    generate_css_variables,
    get_pdf_branding_colors,
    get_pdf_footer_text,
)


@pytest.fixture
def db_session():
    """Create test database session with in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def tenant(db_session):
    """Create a basic tenant."""
    tenant_id = str(uuid.uuid4())
    tenant = Tenant(id=tenant_id, name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture
def tenant_with_branding(db_session, tenant):
    """Create a tenant with custom branding."""
    service = BrandingService(db_session)
    service.update_branding(
        tenant.id,
        primary_color="#FF5733",
        secondary_color="#33FF57",
        footer_text="Custom Footer Text",
        logo_url="https://example.com/logo.png",
    )
    return tenant.id


class TestBrandingPersistence:
    """Tests for branding database persistence."""

    def test_branding_persists_to_database(self, db_session, tenant_with_branding):
        """Test that branding configuration is persisted."""
        service = BrandingService(db_session)
        branding = service.get_branding(tenant_with_branding)

        assert branding["primary_color"] == "#FF5733"
        assert branding["secondary_color"] == "#33FF57"
        assert branding["footer_text"] == "Custom Footer Text"
        assert branding["logo_url"] == "https://example.com/logo.png"
        assert branding["is_custom"] is True

    def test_branding_update_existing(self, db_session, tenant_with_branding):
        """Test updating existing branding."""
        service = BrandingService(db_session)

        service.update_branding(
            tenant_with_branding,
            primary_color="#000000",
        )

        branding = service.get_branding(tenant_with_branding)
        assert branding["primary_color"] == "#000000"
        assert branding["secondary_color"] == "#33FF57"

    def test_branding_delete_resets_to_defaults(self, db_session, tenant_with_branding):
        """Test deleting branding resets to defaults."""
        service = BrandingService(db_session)

        result = service.delete_branding(tenant_with_branding)
        assert result is True

        branding = service.get_branding(tenant_with_branding)
        assert branding["primary_color"] == DEFAULT_BRANDING["primary_color"]
        assert branding["is_custom"] is False


class TestBrandingFallback:
    """Tests for default branding fallback."""

    def test_branding_fallback_to_defaults(self, db_session, tenant):
        """Test fallback to default branding when none configured."""
        service = BrandingService(db_session)
        branding = service.get_branding(tenant.id)

        assert branding["primary_color"] == "#1E3A8A"
        assert branding["secondary_color"] == "#3B82F6"
        assert branding["footer_text"] == "Powered by RaapTech SEO Health Report"
        assert branding["is_custom"] is False

    def test_branding_fallback_for_nonexistent_tenant(self, db_session):
        """Test fallback for non-existent tenant ID."""
        service = BrandingService(db_session)
        branding = service.get_branding("nonexistent-tenant-id")

        assert branding["primary_color"] == DEFAULT_BRANDING["primary_color"]
        assert branding["is_custom"] is False


class TestBrandingValidation:
    """Tests for branding validation."""

    def test_invalid_primary_color_format(self, db_session, tenant):
        """Test that invalid hex color raises ValueError."""
        service = BrandingService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.update_branding(tenant.id, primary_color="red")

        assert "Invalid primary_color format" in str(exc_info.value)

    def test_invalid_secondary_color_format(self, db_session, tenant):
        """Test that invalid secondary color raises ValueError."""
        service = BrandingService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.update_branding(tenant.id, secondary_color="#GGG")

        assert "Invalid secondary_color format" in str(exc_info.value)

    def test_valid_hex_colors_accepted(self, db_session, tenant):
        """Test that valid hex colors are accepted."""
        service = BrandingService(db_session)

        service.update_branding(
            tenant.id,
            primary_color="#FFFFFF",
            secondary_color="#000000",
        )

        branding = service.get_branding(tenant.id)
        assert branding["primary_color"] == "#FFFFFF"
        assert branding["secondary_color"] == "#000000"


class TestHtmlBrandingApplication:
    """Tests for HTML branding application."""

    def test_branding_applies_to_html_reports(self, db_session, tenant_with_branding):
        """Test that branding is applied to HTML reports."""
        service = BrandingService(db_session)
        branding = service.get_report_branding(tenant_with_branding)

        html = """
        <html>
        <head><style>.header { color: #1a73e8; }</style></head>
        <body>
            <div class="container">
                <p>Generated by SEO Health Report System</p>
            </div>
        </body>
        </html>
        """

        branded = apply_html_branding(html, branding)

        assert "#FF5733" in branded
        assert "Custom Footer Text" in branded

    def test_branding_replaces_default_colors(self):
        """Test that default colors are replaced."""
        branding = {
            "primary_color": "#AABBCC",
            "secondary_color": "#DDEEFF",
            "footer_text": "My Footer",
        }

        html = """
        <div style="color: #1a73e8;">Primary</div>
        <div style="color: #34a853;">Secondary</div>
        """

        branded = apply_html_branding(html, branding)

        assert "#AABBCC" in branded
        assert "#DDEEFF" in branded
        assert "#1a73e8" not in branded
        assert "#34a853" not in branded

    def test_branding_adds_logo(self):
        """Test that logo is added when provided."""
        branding = {
            "primary_color": "#1E3A8A",
            "secondary_color": "#3B82F6",
            "footer_text": "Footer",
            "logo_url": "https://example.com/logo.png",
        }

        html = '<html><body><div class="container">Content</div></body></html>'

        branded = apply_html_branding(html, branding)

        assert "https://example.com/logo.png" in branded
        assert '<img src="https://example.com/logo.png"' in branded


class TestPdfBranding:
    """Tests for PDF branding helpers."""

    def test_get_pdf_branding_colors(self):
        """Test PDF color extraction."""
        branding = {
            "primary_color": "#FF0000",
            "secondary_color": "#00FF00",
        }

        colors = get_pdf_branding_colors(branding)

        assert colors["primary"] == "#FF0000"
        assert colors["secondary"] == "#00FF00"
        assert "warning" in colors
        assert "danger" in colors

    def test_get_pdf_footer_text(self):
        """Test PDF footer text extraction."""
        branding = {"footer_text": "Custom PDF Footer"}

        footer = get_pdf_footer_text(branding)
        assert footer == "Custom PDF Footer"

    def test_get_pdf_footer_text_default(self):
        """Test PDF footer falls back to default."""
        branding = {}

        footer = get_pdf_footer_text(branding)
        assert footer == DEFAULT_BRANDING["footer_text"]


class TestCssVariables:
    """Tests for CSS variable generation."""

    def test_generate_css_variables(self):
        """Test CSS variable generation."""
        branding = {
            "primary_color": "#1E3A8A",
            "secondary_color": "#3B82F6",
        }

        css = generate_css_variables(branding)

        assert ":root {" in css
        assert "--brand-primary: #1E3A8A" in css
        assert "--brand-secondary: #3B82F6" in css
        assert "--brand-primary-dark:" in css
        assert "--brand-primary-light:" in css

    def test_css_variables_with_custom_colors(self):
        """Test CSS variables with custom colors."""
        branding = {
            "primary_color": "#FF5733",
            "secondary_color": "#33FF57",
        }

        css = generate_css_variables(branding)

        assert "--brand-primary: #FF5733" in css
        assert "--brand-secondary: #33FF57" in css


class TestReportBranding:
    """Tests for get_report_branding function."""

    def test_get_report_branding_with_tenant(self, db_session, tenant_with_branding):
        """Test get_report_branding returns tenant branding."""
        service = BrandingService(db_session)
        branding = service.get_report_branding(tenant_with_branding)

        assert branding["primary_color"] == "#FF5733"
        assert branding["footer_text"] == "Custom Footer Text"

    def test_get_report_branding_without_tenant(self, db_session):
        """Test get_report_branding returns defaults for None tenant."""
        service = BrandingService(db_session)
        branding = service.get_report_branding(None)

        assert branding == DEFAULT_BRANDING


class TestBrandingTimestamps:
    """Tests for branding timestamp tracking."""

    def test_branding_has_created_at(self, db_session, tenant_with_branding):
        """Test that branding has created_at timestamp."""
        service = BrandingService(db_session)
        branding = service.get_branding(tenant_with_branding)

        assert branding["created_at"] is not None

    def test_branding_has_updated_at(self, db_session, tenant_with_branding):
        """Test that branding has updated_at timestamp."""
        service = BrandingService(db_session)
        branding = service.get_branding(tenant_with_branding)

        assert branding["updated_at"] is not None


class TestBrandingApiIntegration:
    """Tests for branding API integration."""

    def test_branding_service_requires_db_session(self):
        """Test that BrandingService requires a database session."""
        with pytest.raises(TypeError):
            BrandingService()

    def test_multiple_tenants_independent_branding(self, db_session):
        """Test that multiple tenants have independent branding."""
        tenant1_id = str(uuid.uuid4())
        tenant2_id = str(uuid.uuid4())

        tenant1 = Tenant(id=tenant1_id, name="Tenant 1")
        tenant2 = Tenant(id=tenant2_id, name="Tenant 2")
        db_session.add_all([tenant1, tenant2])
        db_session.commit()

        service = BrandingService(db_session)

        service.update_branding(tenant1_id, primary_color="#111111")
        service.update_branding(tenant2_id, primary_color="#222222")

        branding1 = service.get_branding(tenant1_id)
        branding2 = service.get_branding(tenant2_id)

        assert branding1["primary_color"] == "#111111"
        assert branding2["primary_color"] == "#222222"
