"""
Branding service for tenant customization.

Features:
- Logo URL management
- Color scheme customization (hex validation)
- Footer text customization
- Fallback to default RaapTech branding
"""

import logging
import re
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DEFAULT_BRANDING = {
    "logo_url": None,
    "primary_color": "#1E3A8A",
    "secondary_color": "#3B82F6",
    "footer_text": "Powered by RaapTech SEO Health Report",
}

HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_hex_color(color: str) -> bool:
    """Validate hex color format."""
    return bool(HEX_COLOR_PATTERN.match(color))


class BrandingService:
    """
    Service for managing tenant branding configuration.

    Usage:
        service = BrandingService(db_session)

        # Get branding (with fallback to defaults)
        branding = service.get_branding(tenant_id)

        # Update branding
        branding = service.update_branding(
            tenant_id,
            primary_color="#FF5733",
            logo_url="https://example.com/logo.png"
        )
    """

    def __init__(self, db: Session):
        self.db = db

    def get_branding(self, tenant_id: str) -> dict[str, Any]:
        """
        Get branding for a tenant with fallback to defaults.

        Args:
            tenant_id: Tenant ID

        Returns:
            Branding configuration dict
        """
        from database import TenantBranding

        branding = self.db.query(TenantBranding).filter(
            TenantBranding.tenant_id == tenant_id
        ).first()

        if not branding:
            return {
                "tenant_id": tenant_id,
                **DEFAULT_BRANDING,
                "is_custom": False,
            }

        return {
            "id": branding.id,
            "tenant_id": branding.tenant_id,
            "logo_url": branding.logo_url,
            "primary_color": branding.primary_color or DEFAULT_BRANDING["primary_color"],
            "secondary_color": branding.secondary_color or DEFAULT_BRANDING["secondary_color"],
            "footer_text": branding.footer_text or DEFAULT_BRANDING["footer_text"],
            "is_custom": True,
            "created_at": branding.created_at.isoformat() if branding.created_at else None,
            "updated_at": branding.updated_at.isoformat() if branding.updated_at else None,
        }

    def update_branding(
        self,
        tenant_id: str,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        footer_text: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update or create branding for a tenant.

        Args:
            tenant_id: Tenant ID
            logo_url: URL to logo image
            primary_color: Primary brand color (hex)
            secondary_color: Secondary brand color (hex)
            footer_text: Custom footer text

        Returns:
            Updated branding configuration

        Raises:
            ValueError: If color format is invalid
        """
        from database import TenantBranding

        # Validate colors
        if primary_color and not validate_hex_color(primary_color):
            raise ValueError(f"Invalid primary_color format: {primary_color}. Use hex format like #1E3A8A")
        if secondary_color and not validate_hex_color(secondary_color):
            raise ValueError(f"Invalid secondary_color format: {secondary_color}. Use hex format like #3B82F6")

        # Get or create branding
        branding = self.db.query(TenantBranding).filter(
            TenantBranding.tenant_id == tenant_id
        ).first()

        if not branding:
            branding = TenantBranding(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
            )
            self.db.add(branding)

        # Update fields if provided
        if logo_url is not None:
            branding.logo_url = logo_url
        if primary_color is not None:
            branding.primary_color = primary_color
        if secondary_color is not None:
            branding.secondary_color = secondary_color
        if footer_text is not None:
            branding.footer_text = footer_text

        self.db.commit()
        self.db.refresh(branding)

        logger.info(f"Updated branding for tenant {tenant_id}")

        return self.get_branding(tenant_id)

    def delete_branding(self, tenant_id: str) -> bool:
        """
        Delete custom branding for a tenant (resets to defaults).

        Args:
            tenant_id: Tenant ID

        Returns:
            True if deleted, False if no custom branding existed
        """
        from database import TenantBranding

        branding = self.db.query(TenantBranding).filter(
            TenantBranding.tenant_id == tenant_id
        ).first()

        if not branding:
            return False

        self.db.delete(branding)
        self.db.commit()

        logger.info(f"Deleted branding for tenant {tenant_id}")
        return True

    def get_report_branding(self, tenant_id: Optional[str]) -> dict[str, Any]:
        """
        Get branding configuration for report generation.

        This method is designed for use in report generators,
        returning only the fields needed for rendering.

        Args:
            tenant_id: Tenant ID or None for default branding

        Returns:
            Dict with logo_url, primary_color, secondary_color, footer_text
        """
        if not tenant_id:
            return DEFAULT_BRANDING.copy()

        branding = self.get_branding(tenant_id)

        return {
            "logo_url": branding.get("logo_url"),
            "primary_color": branding.get("primary_color", DEFAULT_BRANDING["primary_color"]),
            "secondary_color": branding.get("secondary_color", DEFAULT_BRANDING["secondary_color"]),
            "footer_text": branding.get("footer_text", DEFAULT_BRANDING["footer_text"]),
        }
