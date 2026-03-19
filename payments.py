"""
Stripe payment integration for SEO Health Report.
"""

import os
from typing import Optional

import stripe

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Pricing tiers (in cents)
TIER_PRICES = {
    "basic": {"amount": 80000, "name": "Basic SEO Audit", "description": "Technical + Content audit"},
    "pro": {"amount": 250000, "name": "Pro SEO Audit", "description": "Full audit with AI visibility"},
    "enterprise": {"amount": 600000, "name": "Enterprise SEO Audit", "description": "Custom branding + competitive analysis"}
}


def create_checkout_session(
    tier: str,
    user_id: str,
    user_email: str,
    audit_url: str,
    success_url: str,
    cancel_url: str
) -> dict:
    """
    Create a Stripe checkout session.

    Returns dict with session_id and checkout_url.
    """
    if tier not in TIER_PRICES:
        raise ValueError(f"Invalid tier: {tier}")

    price_info = TIER_PRICES[tier]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": price_info["name"],
                        "description": price_info["description"],
                    },
                    "unit_amount": price_info["amount"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user_email,
            metadata={
                "user_id": user_id,
                "tier": tier,
                "audit_url": audit_url,
            },
        )

        return {
            "session_id": session.id,
            "checkout_url": session.url,
            "amount": price_info["amount"],
            "tier": tier
        }

    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


def verify_webhook_signature(payload: bytes, signature: str) -> dict:
    """
    Verify Stripe webhook signature and return event.
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        return event
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid webhook signature")


def get_session_details(session_id: str) -> dict:
    """Get checkout session details."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "id": session.id,
            "payment_status": session.payment_status,
            "customer_email": session.customer_email,
            "amount_total": session.amount_total,
            "metadata": session.metadata,
        }
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


def get_payment_intent(payment_intent_id: str) -> dict:
    """Get payment intent details."""
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {
            "id": intent.id,
            "status": intent.status,
            "amount": intent.amount,
            "currency": intent.currency,
        }
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")


def create_refund(payment_intent_id: str, amount: Optional[int] = None) -> dict:
    """Create a refund for a payment."""
    try:
        refund_params = {"payment_intent": payment_intent_id}
        if amount:
            refund_params["amount"] = amount

        refund = stripe.Refund.create(**refund_params)
        return {
            "id": refund.id,
            "status": refund.status,
            "amount": refund.amount,
        }
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")
