"""Competitor monitoring routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.openapi import COMPETITOR_EXAMPLE, ERROR_RESPONSES
from database import Competitor, get_db

router = APIRouter(prefix="/competitors", tags=["competitors"])


class CompetitorRequest(BaseModel):
    """Request model for adding a competitor to monitor."""
    url: str
    company_name: str
    monitoring_frequency: int = 3600
    alert_threshold: int = 10

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://competitor.com",
                "company_name": "Competitor Inc",
                "monitoring_frequency": 3600,
                "alert_threshold": 10
            }
        }


@router.post(
    "",
    summary="Add competitor",
    description="Add a new competitor URL to monitor for SEO changes.",
    responses={
        200: {
            "description": "Competitor added",
            "content": {
                "application/json": {
                    "example": COMPETITOR_EXAMPLE
                }
            }
        },
        422: ERROR_RESPONSES[422],
    }
)
async def add_competitor(request: CompetitorRequest, db: Session = Depends(get_db)):
    """Add a competitor for monitoring."""
    competitor_id = f"comp_{uuid.uuid4().hex[:12]}"

    competitor = Competitor(
        id=competitor_id,
        url=request.url,
        company_name=request.company_name,
        monitoring_frequency=request.monitoring_frequency,
        alert_threshold=request.alert_threshold
    )
    db.add(competitor)
    db.commit()

    return {
        "competitor_id": competitor_id,
        "url": request.url,
        "company_name": request.company_name,
        "monitoring_frequency": request.monitoring_frequency,
        "alert_threshold": request.alert_threshold,
        "created_at": competitor.created_at.isoformat()
    }


@router.get(
    "",
    summary="List competitors",
    description="Get all monitored competitors and their latest scores.",
    responses={
        200: {
            "description": "List of competitors",
            "content": {
                "application/json": {
                    "example": {
                        "competitors": [COMPETITOR_EXAMPLE]
                    }
                }
            }
        }
    }
)
async def list_competitors(db: Session = Depends(get_db)):
    """List all monitored competitors."""
    competitors = db.query(Competitor).all()
    return {
        "competitors": [{
            "competitor_id": c.id, "url": c.url, "company_name": c.company_name,
            "monitoring_frequency": c.monitoring_frequency, "alert_threshold": c.alert_threshold,
            "last_score": c.last_score,
            "last_audit_at": c.last_audit_at.isoformat() if c.last_audit_at else None
        } for c in competitors]
    }


@router.delete(
    "/{competitor_id}",
    summary="Delete competitor",
    description="Remove a competitor from monitoring.",
    responses={
        200: {"description": "Competitor removed"},
        404: ERROR_RESPONSES[404],
    }
)
async def delete_competitor(competitor_id: str, db: Session = Depends(get_db)):
    """Remove a competitor from monitoring."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    db.delete(competitor)
    db.commit()
    return {"message": "Competitor removed"}
