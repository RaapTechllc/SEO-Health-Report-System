"""Payment and Stripe integration routes."""

import logging
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.openapi import ERROR_RESPONSES, PRICING_EXAMPLE
from apps.api.routers.audits import TIER_MAPPING, run_audit_task
from auth import require_auth
from database import Audit, Payment, User, get_db
from payments import TIER_PRICES, create_checkout_session, verify_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])


class CheckoutRequest(BaseModel):
    """Request model for creating a checkout session."""
    tier: str
    url: str
    company_name: str

    class Config:
        json_schema_extra = {
            "example": {
                "tier": "pro",
                "url": "https://example.com",
                "company_name": "Example Corp"
            }
        }


@router.post(
    "/checkout/create",
    summary="Create checkout session",
    description="Create a Stripe checkout session for purchasing an audit tier.",
    responses={
        200: {
            "description": "Checkout session created",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "cs_test_abc123",
                        "checkout_url": "https://checkout.stripe.com/...",
                        "amount": 7900
                    }
                }
            }
        },
        400: ERROR_RESPONSES[400],
        401: ERROR_RESPONSES[401],
        500: ERROR_RESPONSES[500],
    }
)
async def create_checkout(
    request: CheckoutRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session."""
    if request.tier not in TIER_PRICES:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {request.tier}")

    base_url = os.getenv("BASE_URL", "http://localhost:8000")

    try:
        result = create_checkout_session(
            tier=request.tier,
            user_id=user.id,
            user_email=user.email,
            audit_url=request.url,
            success_url=f"{base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/checkout/cancel"
        )

        payment = Payment(
            id=f"pay_{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            stripe_checkout_session_id=result["session_id"],
            amount=result["amount"],
            tier=request.tier,
            status="pending"
        )
        db.add(payment)
        db.commit()

        return result

    except Exception:
        logger.exception("Checkout session creation failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/checkout/success",
    summary="Checkout success",
    description="Redirect endpoint after successful Stripe checkout."
)
async def checkout_success(session_id: str):
    """Handle successful checkout redirect."""
    return {"status": "success", "session_id": session_id, "message": "Payment successful! Your audit will begin shortly."}


@router.get(
    "/checkout/cancel",
    summary="Checkout cancelled",
    description="Redirect endpoint when checkout is cancelled."
)
async def checkout_cancel():
    """Handle cancelled checkout."""
    return {"status": "cancelled", "message": "Checkout was cancelled."}


@router.post(
    "/webhooks/stripe",
    summary="Stripe webhook",
    description="Handle Stripe webhook events for payment processing.",
    responses={
        200: {"description": "Webhook processed"},
        400: ERROR_RESPONSES[400],
    }
)
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook_signature(payload, signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        payment = db.query(Payment).filter(
            Payment.stripe_checkout_session_id == session["id"]
        ).first()

        if payment:
            payment.status = "succeeded"
            payment.stripe_payment_intent_id = session.get("payment_intent")

            metadata = session.get("metadata", {})
            audit_id = f"audit_{uuid.uuid4().hex[:12]}"

            requested_tier = metadata.get("tier", "medium")
            tier = TIER_MAPPING.get(requested_tier.lower(), "medium")

            audit = Audit(
                id=audit_id,
                user_id=metadata.get("user_id"),
                url=metadata.get("audit_url", ""),
                company_name="",
                tier=tier,
                status="pending"
            )
            db.add(audit)
            payment.audit_id = audit_id
            db.commit()

            background_tasks.add_task(
                run_audit_task, audit_id, metadata.get("audit_url", ""),
                "", [], [], tier
            )

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == intent["id"]
        ).first()
        if payment:
            payment.status = "failed"
            db.commit()

    return {"status": "ok"}


@router.get(
    "/pricing",
    summary="Get pricing tiers",
    description="Get available pricing tiers and their features.",
    responses={
        200: {
            "description": "Pricing information",
            "content": {
                "application/json": {
                    "example": PRICING_EXAMPLE
                }
            }
        }
    }
)
async def get_pricing():
    """Get available pricing tiers."""
    return {
        "tiers": {
            tier: {
                "name": info["name"],
                "description": info["description"],
                "price": info["amount"] / 100,
                "currency": "USD"
            }
            for tier, info in TIER_PRICES.items()
        }
    }
