"""Tests for quota enforcement service."""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import TenantQuota
from packages.seo_health_report.quotas.service import (
    TIER_DEFAULTS,
    QuotaExceededError,
    QuotaService,
    QuotaStatus,
    check_quota,
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.scalar.return_value = 0
    return db


@pytest.fixture
def tenant_id():
    """Generate a test tenant ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_quota(tenant_id):
    """Create a sample TenantQuota object."""
    quota = MagicMock(spec=TenantQuota)
    quota.id = str(uuid.uuid4())
    quota.tenant_id = tenant_id
    quota.monthly_audits_limit = 10
    quota.monthly_audits_used = 5
    quota.billing_cycle_start = datetime.now(timezone.utc) - timedelta(days=15)
    quota.max_concurrent_audits = 2
    quota.max_pages_per_audit = 50
    quota.max_ai_prompts_per_audit = 10
    return quota


class TestTierDefaults:
    """Test tier default configurations."""

    def test_basic_tier_defaults(self):
        assert TIER_DEFAULTS["basic"]["monthly_audits"] == 10
        assert TIER_DEFAULTS["basic"]["concurrent"] == 2
        assert TIER_DEFAULTS["basic"]["pages"] == 50
        assert TIER_DEFAULTS["basic"]["prompts"] == 10

    def test_pro_tier_defaults(self):
        assert TIER_DEFAULTS["pro"]["monthly_audits"] == 50
        assert TIER_DEFAULTS["pro"]["concurrent"] == 5
        assert TIER_DEFAULTS["pro"]["pages"] == 200
        assert TIER_DEFAULTS["pro"]["prompts"] == 50

    def test_enterprise_tier_defaults(self):
        assert TIER_DEFAULTS["enterprise"]["monthly_audits"] == -1
        assert TIER_DEFAULTS["enterprise"]["concurrent"] == 20
        assert TIER_DEFAULTS["enterprise"]["pages"] == 1000
        assert TIER_DEFAULTS["enterprise"]["prompts"] == 200


class TestQuotaStatus:
    """Test QuotaStatus dataclass."""

    def test_quota_status_creation(self):
        status = QuotaStatus(
            monthly_audits_used=5,
            monthly_audits_limit=10,
            monthly_audits_remaining=5,
            concurrent_audits=1,
            max_concurrent=2,
            can_start_audit=True,
        )
        assert status.monthly_audits_used == 5
        assert status.monthly_audits_limit == 10
        assert status.monthly_audits_remaining == 5
        assert status.can_start_audit is True
        assert status.quota_exceeded_reason is None

    def test_quota_status_with_exceeded_reason(self):
        status = QuotaStatus(
            monthly_audits_used=10,
            monthly_audits_limit=10,
            monthly_audits_remaining=0,
            concurrent_audits=0,
            max_concurrent=2,
            can_start_audit=False,
            quota_exceeded_reason="Monthly limit reached",
        )
        assert status.can_start_audit is False
        assert status.quota_exceeded_reason == "Monthly limit reached"


class TestQuotaService:
    """Test QuotaService methods."""

    def test_get_or_create_quota_creates_new(self, mock_db, tenant_id):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = QuotaService(mock_db)
        service.get_or_create_quota(tenant_id, "basic")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_or_create_quota_returns_existing(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        quota = service.get_or_create_quota(tenant_id)

        assert quota == sample_quota
        mock_db.add.assert_not_called()

    def test_get_or_create_quota_pro_tier(self, mock_db, tenant_id):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = QuotaService(mock_db)
        service.get_or_create_quota(tenant_id, "pro")

        added_quota = mock_db.add.call_args[0][0]
        assert added_quota.monthly_audits_limit == 50
        assert added_quota.max_concurrent_audits == 5

    def test_get_or_create_quota_enterprise_tier(self, mock_db, tenant_id):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = QuotaService(mock_db)
        service.get_or_create_quota(tenant_id, "enterprise")

        added_quota = mock_db.add.call_args[0][0]
        assert added_quota.monthly_audits_limit == -1
        assert added_quota.max_concurrent_audits == 20

    def test_check_quota_can_start(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = QuotaService(mock_db)
        status = service.check_quota(tenant_id)

        assert status.can_start_audit is True
        assert status.monthly_audits_remaining == 5

    def test_check_quota_monthly_limit_exceeded(self, mock_db, tenant_id, sample_quota):
        sample_quota.monthly_audits_used = 10
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = QuotaService(mock_db)
        status = service.check_quota(tenant_id)

        assert status.can_start_audit is False
        assert "Monthly audit limit reached" in status.quota_exceeded_reason

    def test_check_quota_concurrent_limit_exceeded(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_quota
        query_mock.filter.return_value.scalar.return_value = 2
        mock_db.query.return_value = query_mock

        service = QuotaService(mock_db)
        status = service.check_quota(tenant_id)

        assert status.can_start_audit is False
        assert "Concurrent audit limit reached" in status.quota_exceeded_reason

    def test_check_quota_unlimited_monthly(self, mock_db, tenant_id, sample_quota):
        sample_quota.monthly_audits_limit = -1
        sample_quota.monthly_audits_used = 1000
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = QuotaService(mock_db)
        status = service.check_quota(tenant_id)

        assert status.can_start_audit is True
        assert status.monthly_audits_remaining == -1

    def test_increment_usage(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        initial_used = sample_quota.monthly_audits_used

        service = QuotaService(mock_db)
        service.increment_usage(tenant_id)

        assert sample_quota.monthly_audits_used == initial_used + 1
        mock_db.commit.assert_called()

    def test_increment_usage_creates_quota_if_missing(self, mock_db, tenant_id):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = QuotaService(mock_db)
        service.increment_usage(tenant_id)

        mock_db.add.assert_called()

    def test_check_page_limit_within(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        assert service.check_page_limit(tenant_id, 30) is True

    def test_check_page_limit_exceeded(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        assert service.check_page_limit(tenant_id, 100) is False

    def test_check_page_limit_exact(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        assert service.check_page_limit(tenant_id, 50) is True

    def test_check_ai_prompt_limit_within(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        assert service.check_ai_prompt_limit(tenant_id, 5) is True

    def test_check_ai_prompt_limit_exceeded(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        assert service.check_ai_prompt_limit(tenant_id, 15) is False

    def test_reset_monthly_usage(self, mock_db, tenant_id, sample_quota):
        sample_quota.monthly_audits_used = 10
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        service.reset_monthly_usage(tenant_id)

        assert sample_quota.monthly_audits_used == 0
        mock_db.commit.assert_called()

    def test_reset_monthly_usage_no_quota(self, mock_db, tenant_id):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = QuotaService(mock_db)
        service.reset_monthly_usage(tenant_id)

        mock_db.commit.assert_not_called()

    def test_update_tier_existing(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        service.update_tier(tenant_id, "pro")

        assert sample_quota.monthly_audits_limit == 50
        assert sample_quota.max_concurrent_audits == 5
        mock_db.commit.assert_called()

    def test_update_tier_creates_if_missing(self, mock_db, tenant_id):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = QuotaService(mock_db)
        service.update_tier(tenant_id, "enterprise")

        added_quota = mock_db.add.call_args[0][0]
        assert added_quota.monthly_audits_limit == -1

    def test_get_page_limit(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        assert service.get_page_limit(tenant_id) == 50

    def test_get_ai_prompt_limit(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota

        service = QuotaService(mock_db)
        assert service.get_ai_prompt_limit(tenant_id) == 10

    def test_decrement_concurrent_noop(self, mock_db, tenant_id):
        service = QuotaService(mock_db)
        service.decrement_concurrent(tenant_id)


class TestEnforceQuota:
    """Test enforce_quota method and QuotaExceededError."""

    def test_enforce_quota_success(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = QuotaService(mock_db)
        status = service.enforce_quota(tenant_id)

        assert status.can_start_audit is True

    def test_enforce_quota_monthly_exceeded_raises(self, mock_db, tenant_id, sample_quota):
        sample_quota.monthly_audits_used = 10
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = QuotaService(mock_db)

        with pytest.raises(QuotaExceededError) as exc_info:
            service.enforce_quota(tenant_id)

        assert exc_info.value.quota_type == "monthly_audits"
        assert exc_info.value.limit == 10
        assert exc_info.value.used == 10

    def test_enforce_quota_concurrent_exceeded_raises(self, mock_db, tenant_id, sample_quota):
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_quota
        query_mock.filter.return_value.scalar.return_value = 2
        mock_db.query.return_value = query_mock

        service = QuotaService(mock_db)

        with pytest.raises(QuotaExceededError) as exc_info:
            service.enforce_quota(tenant_id)

        assert exc_info.value.quota_type == "concurrent_audits"


class TestQuotaExceededError:
    """Test QuotaExceededError exception."""

    def test_error_attributes(self):
        error = QuotaExceededError(
            "Monthly limit exceeded",
            "monthly_audits",
            10,
            10,
        )
        assert str(error) == "Monthly limit exceeded"
        assert error.quota_type == "monthly_audits"
        assert error.limit == 10
        assert error.used == 10

    def test_error_concurrent_type(self):
        error = QuotaExceededError(
            "Too many concurrent audits",
            "concurrent_audits",
            2,
            2,
        )
        assert error.quota_type == "concurrent_audits"


class TestCheckQuotaConvenienceFunction:
    """Test the check_quota convenience function."""

    def test_check_quota_function(self, mock_db, tenant_id, sample_quota):
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        status = check_quota(mock_db, tenant_id)

        assert isinstance(status, QuotaStatus)
        assert status.monthly_audits_used == 5


class TestResetDateCalculation:
    """Test billing cycle reset date calculation."""

    def test_reset_date_in_future(self, mock_db, tenant_id, sample_quota):
        sample_quota.billing_cycle_start = datetime.now(timezone.utc) - timedelta(days=15)
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = QuotaService(mock_db)
        status = service.check_quota(tenant_id)

        assert status.reset_date is not None
        assert status.reset_date > datetime.now(timezone.utc)

    def test_reset_date_handles_year_boundary(self, mock_db, tenant_id, sample_quota):
        sample_quota.billing_cycle_start = datetime(2024, 12, 15, tzinfo=timezone.utc)
        mock_db.query.return_value.filter.return_value.first.return_value = sample_quota
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = QuotaService(mock_db)
        status = service.check_quota(tenant_id)

        assert status.reset_date is not None
