"""Quota enforcement service for per-tenant limits."""

import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from database import Audit, TenantQuota

TIER_DEFAULTS = {
    "basic": {"monthly_audits": 10, "concurrent": 2, "pages": 50, "prompts": 10},
    "pro": {"monthly_audits": 50, "concurrent": 5, "pages": 200, "prompts": 50},
    "enterprise": {"monthly_audits": -1, "concurrent": 20, "pages": 1000, "prompts": 200},
}


class QuotaExceededError(Exception):
    """Raised when a tenant exceeds their quota."""

    def __init__(self, message: str, quota_type: str, limit: int, used: int):
        super().__init__(message)
        self.quota_type = quota_type
        self.limit = limit
        self.used = used


@dataclass
class QuotaStatus:
    """Status of a tenant's quota usage."""

    monthly_audits_used: int
    monthly_audits_limit: int
    monthly_audits_remaining: int
    concurrent_audits: int
    max_concurrent: int
    can_start_audit: bool
    quota_exceeded_reason: Optional[str] = None
    reset_date: Optional[datetime] = None


class QuotaService:
    """Service for managing and enforcing per-tenant quotas."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_quota(self, tenant_id: str, tier: str = "basic") -> TenantQuota:
        """Get or create quota for tenant with tier defaults."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if quota:
            return quota

        tier_config = TIER_DEFAULTS.get(tier, TIER_DEFAULTS["basic"])

        quota = TenantQuota(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            monthly_audits_limit=tier_config["monthly_audits"],
            monthly_audits_used=0,
            billing_cycle_start=datetime.now(timezone.utc),
            max_concurrent_audits=tier_config["concurrent"],
            max_pages_per_audit=tier_config["pages"],
            max_ai_prompts_per_audit=tier_config["prompts"],
        )

        self.db.add(quota)
        self.db.commit()
        self.db.refresh(quota)

        return quota

    def _get_concurrent_audit_count(self, tenant_id: str) -> int:
        """Get count of currently running audits for tenant."""
        return self.db.query(func.count(Audit.id)).filter(
            Audit.tenant_id == tenant_id,
            Audit.status.in_(["pending", "running"])
        ).scalar() or 0

    def _calculate_reset_date(self, billing_cycle_start: Optional[datetime]) -> datetime:
        """Calculate the next billing cycle reset date."""
        if not billing_cycle_start:
            billing_cycle_start = datetime.now(timezone.utc)

        next_reset = billing_cycle_start
        now = datetime.now(timezone.utc)

        while next_reset <= now:
            if next_reset.month == 12:
                next_reset = next_reset.replace(year=next_reset.year + 1, month=1)
            else:
                next_reset = next_reset.replace(month=next_reset.month + 1)

        return next_reset

    def check_quota(self, tenant_id: str) -> QuotaStatus:
        """Check if tenant can start a new audit."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if not quota:
            quota = self.get_or_create_quota(tenant_id)

        concurrent_count = self._get_concurrent_audit_count(tenant_id)

        is_unlimited = quota.monthly_audits_limit == -1
        monthly_remaining = (
            float('inf') if is_unlimited
            else max(0, quota.monthly_audits_limit - quota.monthly_audits_used)
        )

        quota_exceeded_reason = None
        can_start = True

        if not is_unlimited and quota.monthly_audits_used >= quota.monthly_audits_limit:
            can_start = False
            quota_exceeded_reason = f"Monthly audit limit reached ({quota.monthly_audits_limit})"
        elif concurrent_count >= quota.max_concurrent_audits:
            can_start = False
            quota_exceeded_reason = f"Concurrent audit limit reached ({quota.max_concurrent_audits})"

        reset_date = self._calculate_reset_date(quota.billing_cycle_start)

        return QuotaStatus(
            monthly_audits_used=quota.monthly_audits_used,
            monthly_audits_limit=quota.monthly_audits_limit,
            monthly_audits_remaining=int(monthly_remaining) if not is_unlimited else -1,
            concurrent_audits=concurrent_count,
            max_concurrent=quota.max_concurrent_audits,
            can_start_audit=can_start,
            quota_exceeded_reason=quota_exceeded_reason,
            reset_date=reset_date,
        )

    def increment_usage(self, tenant_id: str) -> None:
        """Increment monthly audit usage."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if not quota:
            quota = self.get_or_create_quota(tenant_id)

        quota.monthly_audits_used += 1
        quota.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def decrement_concurrent(self, tenant_id: str) -> None:
        """Decrement concurrent count when audit completes.

        Note: This is a no-op since concurrent count is calculated dynamically
        from actual running audits. Keeping for API compatibility.
        """
        pass

    def check_page_limit(self, tenant_id: str, page_count: int) -> bool:
        """Check if page count is within limit."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if not quota:
            quota = self.get_or_create_quota(tenant_id)

        return page_count <= quota.max_pages_per_audit

    def check_ai_prompt_limit(self, tenant_id: str, prompt_count: int) -> bool:
        """Check if AI prompt count is within limit."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if not quota:
            quota = self.get_or_create_quota(tenant_id)

        return prompt_count <= quota.max_ai_prompts_per_audit

    def get_page_limit(self, tenant_id: str) -> int:
        """Get the page limit for a tenant."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if not quota:
            quota = self.get_or_create_quota(tenant_id)

        return quota.max_pages_per_audit

    def get_ai_prompt_limit(self, tenant_id: str) -> int:
        """Get the AI prompt limit for a tenant."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if not quota:
            quota = self.get_or_create_quota(tenant_id)

        return quota.max_ai_prompts_per_audit

    def reset_monthly_usage(self, tenant_id: str) -> None:
        """Reset monthly usage (called on billing cycle)."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if not quota:
            return

        quota.monthly_audits_used = 0
        quota.billing_cycle_start = datetime.now(timezone.utc)
        quota.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def update_tier(self, tenant_id: str, tier: str) -> TenantQuota:
        """Update quota limits based on new tier."""
        quota = self.db.query(TenantQuota).filter(
            TenantQuota.tenant_id == tenant_id
        ).first()

        if not quota:
            return self.get_or_create_quota(tenant_id, tier)

        tier_config = TIER_DEFAULTS.get(tier, TIER_DEFAULTS["basic"])

        quota.monthly_audits_limit = tier_config["monthly_audits"]
        quota.max_concurrent_audits = tier_config["concurrent"]
        quota.max_pages_per_audit = tier_config["pages"]
        quota.max_ai_prompts_per_audit = tier_config["prompts"]
        quota.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(quota)

        return quota

    def enforce_quota(self, tenant_id: str) -> QuotaStatus:
        """Check quota and raise exception if exceeded."""
        status = self.check_quota(tenant_id)

        if not status.can_start_audit:
            if status.quota_exceeded_reason and "Monthly" in status.quota_exceeded_reason:
                raise QuotaExceededError(
                    status.quota_exceeded_reason,
                    "monthly_audits",
                    status.monthly_audits_limit,
                    status.monthly_audits_used,
                )
            else:
                raise QuotaExceededError(
                    status.quota_exceeded_reason or "Quota exceeded",
                    "concurrent_audits",
                    status.max_concurrent,
                    status.concurrent_audits,
                )

        return status


def check_quota(db: Session, tenant_id: str) -> QuotaStatus:
    """Convenience function to check quota."""
    return QuotaService(db).check_quota(tenant_id)
