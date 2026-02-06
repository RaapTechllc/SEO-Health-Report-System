"""
Branding management API endpoints.

Provides GET/PATCH operations for tenant branding configuration.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from auth import require_auth
from database import User, get_db
from packages.seo_health_report.branding import BrandingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenant/branding", tags=["branding"])


class BrandingResponse(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    logo_url: Optional[str]
    primary_color: str
    secondary_color: str
    footer_text: Optional[str]
    is_custom: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UpdateBrandingRequest(BaseModel):
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    footer_text: Optional[str] = None

    @field_validator("primary_color", "secondary_color", mode="before")
    @classmethod
    def validate_color(cls, v):
        if v is None:
            return v
        import re
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("Color must be hex format like #1E3A8A")
        return v


@router.get("", response_model=BrandingResponse)
async def get_branding(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Get current tenant branding configuration.

    Returns default RaapTech branding if no custom branding is set.
    """
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = BrandingService(db)
    return service.get_branding(user.tenant_id)


@router.patch("", response_model=BrandingResponse)
async def update_branding(
    request: UpdateBrandingRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Update tenant branding configuration.

    Only provided fields will be updated. Omit a field to keep its current value.
    Set a field to null to reset it to the default.
    """
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = BrandingService(db)

    try:
        return service.update_branding(
            tenant_id=user.tenant_id,
            logo_url=request.logo_url,
            primary_color=request.primary_color,
            secondary_color=request.secondary_color,
            footer_text=request.footer_text,
        )
    except ValueError as e:
        logger.warning("Invalid branding update request: %s", e)
        raise HTTPException(status_code=400, detail="Invalid branding configuration")


@router.delete("", status_code=204)
async def delete_branding(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Delete custom branding and reset to defaults.
    """
    if not user.tenant_id:
        raise HTTPException(status_code=400, detail="User must belong to a tenant")

    service = BrandingService(db)
    service.delete_branding(user.tenant_id)
