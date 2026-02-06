"""
Cost Tracking Service

Centralized cost event recording for all AI/API calls during audits.
Implements append-only ledger pattern for accurate cost tracking per report.
"""

import os
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

# Model pricing (USD per 1M tokens unless otherwise noted)
MODEL_PRICING = {
    # OpenAI
    "gpt-5-nano": {"input": 0.025, "output": 0.10},
    "gpt-5-mini": {"input": 0.125, "output": 0.50},
    "gpt-5": {"input": 0.625, "output": 2.50},
    "gpt-5.1": {"input": 1.25, "output": 5.00},
    "gpt-image-1-mini": {"flat": 0.02},  # per image

    # Anthropic
    "claude-4-haiku-20251120": {"input": 0.25, "output": 1.25},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},

    # Google
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-3.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-3.0-pro": {"input": 1.25, "output": 5.00},
    "imagen-4.0-fast-generate-001": {"flat": 0.02},
    "imagen-4.0-generate-001": {"flat": 0.04},
    "imagen-4.0-ultra-generate-001": {"flat": 0.08},

    # xAI
    "grok-4-1-fast": {"input": 0.50, "output": 2.00},
    "grok-4-1": {"input": 2.00, "output": 8.00},

    # Perplexity
    "sonar": {"input": 0.20, "output": 0.80},
    "sonar-pro": {"input": 1.00, "output": 4.00},
}


def calculate_cost(
    model: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    operation: str = "chat"
) -> float:
    """
    Calculate cost in USD for a model call.

    Args:
        model: Model identifier (e.g., 'gpt-5-mini')
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        operation: Type of operation ('chat', 'image', etc.)

    Returns:
        Cost in USD
    """
    pricing = MODEL_PRICING.get(model, {})

    # Flat-rate pricing (images, etc.)
    if "flat" in pricing:
        return pricing["flat"]

    # Token-based pricing
    input_cost = pricing.get("input", 0.0)
    output_cost = pricing.get("output", 0.0)

    cost = 0.0
    if prompt_tokens:
        cost += (prompt_tokens / 1_000_000) * input_cost
    if completion_tokens:
        cost += (completion_tokens / 1_000_000) * output_cost

    return round(cost, 8)


def record_cost_event(
    db: Session,
    audit_id: str,
    provider: str,
    operation: str,
    model: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    cost_usd: Optional[float] = None,
    phase: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """
    Record a cost event for an audit.

    Args:
        db: SQLAlchemy session
        audit_id: The audit this cost belongs to
        provider: Provider name (openai, anthropic, google, xai, perplexity)
        operation: Operation type (chat, image, search, crawl)
        model: Model identifier
        prompt_tokens: Input tokens used
        completion_tokens: Output tokens used
        total_tokens: Total tokens (if not computed from prompt+completion)
        cost_usd: Pre-calculated cost (if None, will be calculated)
        phase: Audit phase (ai_visibility, technical, content, exec_summary, etc.)
        tenant_id: Tenant ID if multi-tenant
        user_id: User ID if known
        metadata: Additional metadata (no raw prompts/responses!)

    Returns:
        The created event ID
    """
    from database import CostEvent

    # Get current tier from environment
    tier = os.environ.get("REPORT_TIER", "medium")

    # Calculate cost if not provided
    if cost_usd is None and model:
        cost_usd = calculate_cost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            operation=operation
        )

    # Get pricing for snapshot
    pricing = MODEL_PRICING.get(model, {}) if model else {}

    event_id = str(uuid.uuid4())
    event = CostEvent(
        id=event_id,
        audit_id=audit_id,
        tenant_id=tenant_id,
        user_id=user_id,
        tier=tier,
        phase=phase,
        provider=provider,
        model=model,
        operation=operation,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens or ((prompt_tokens or 0) + (completion_tokens or 0)),
        input_unit_cost_usd_per_1m=pricing.get("input"),
        output_unit_cost_usd_per_1m=pricing.get("output"),
        flat_cost_usd=pricing.get("flat"),
        cost_usd=cost_usd or 0.0,
        currency="USD",
        metadata_json=metadata,
        created_at=datetime.utcnow(),
    )

    db.add(event)
    db.commit()

    return event_id


def get_audit_cost_summary(db: Session, audit_id: str) -> dict[str, Any]:
    """
    Get cost summary for an audit.

    Returns:
        Dictionary with total cost, breakdown by provider/model/phase
    """
    from sqlalchemy import func

    from database import CostEvent

    # Total cost
    total = db.query(func.sum(CostEvent.cost_usd)).filter(
        CostEvent.audit_id == audit_id
    ).scalar() or 0.0

    # By provider
    by_provider = {}
    provider_results = db.query(
        CostEvent.provider,
        func.sum(CostEvent.cost_usd),
        func.sum(CostEvent.total_tokens)
    ).filter(
        CostEvent.audit_id == audit_id
    ).group_by(CostEvent.provider).all()

    for provider, cost, tokens in provider_results:
        by_provider[provider] = {"cost_usd": cost or 0.0, "total_tokens": tokens or 0}

    # By phase
    by_phase = {}
    phase_results = db.query(
        CostEvent.phase,
        func.sum(CostEvent.cost_usd)
    ).filter(
        CostEvent.audit_id == audit_id
    ).group_by(CostEvent.phase).all()

    for phase, cost in phase_results:
        by_phase[phase or "unknown"] = cost or 0.0

    # Count of events
    event_count = db.query(func.count(CostEvent.id)).filter(
        CostEvent.audit_id == audit_id
    ).scalar() or 0

    return {
        "audit_id": audit_id,
        "total_cost_usd": round(total, 6),
        "event_count": event_count,
        "by_provider": by_provider,
        "by_phase": by_phase,
    }


def check_cost_ceiling(
    db: Session,
    audit_id: str,
    tier: str = "medium",
    buffer_multiplier: float = 1.5
) -> tuple[bool, float, float]:
    """
    Check if audit has exceeded cost ceiling for its tier.

    Args:
        db: SQLAlchemy session
        audit_id: Audit to check
        tier: Tier name (low, medium, high)
        buffer_multiplier: Allow this much over expected cost before triggering

    Returns:
        Tuple of (exceeded: bool, current_cost: float, ceiling: float)
    """
    # Expected costs per tier (with buffer)
    TIER_CEILINGS = {
        "low": 0.023 * buffer_multiplier,
        "medium": 0.051 * buffer_multiplier,
        "high": 0.158 * buffer_multiplier,
    }

    ceiling = TIER_CEILINGS.get(tier, 0.10)

    from sqlalchemy import func

    from database import CostEvent

    current = db.query(func.sum(CostEvent.cost_usd)).filter(
        CostEvent.audit_id == audit_id
    ).scalar() or 0.0

    return (current > ceiling, current, ceiling)
