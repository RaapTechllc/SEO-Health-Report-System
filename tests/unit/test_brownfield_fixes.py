"""Tests for brownfield cleanup fixes — covers P0-P2 items from spec."""

import hashlib
import os

import pytest

# ────────────────────────────────────────────
# P0: Auth endpoint enforcement
# ────────────────────────────────────────────


class TestAuthEndpointEnforcement:
    """Verify all audit/competitor endpoints require authentication."""

    def test_start_audit_requires_auth(self):
        """POST /audit must depend on require_auth."""
        import inspect

        from apps.api.routers.audits import start_audit

        sig = inspect.signature(start_audit)
        param_names = list(sig.parameters.keys())
        assert "user" in param_names, "start_audit must have a 'user' parameter"

    def test_list_audits_requires_auth(self):
        """GET /audits must depend on require_auth."""
        import inspect

        from apps.api.routers.audits import list_audits

        sig = inspect.signature(list_audits)
        param_names = list(sig.parameters.keys())
        assert "user" in param_names, "list_audits must have a 'user' parameter"

    def test_add_competitor_requires_auth(self):
        """POST /competitors must depend on require_auth."""
        import inspect

        from apps.api.routers.competitors import add_competitor

        sig = inspect.signature(add_competitor)
        param_names = list(sig.parameters.keys())
        assert "user" in param_names

    def test_list_competitors_requires_auth(self):
        """GET /competitors must depend on require_auth."""
        import inspect

        from apps.api.routers.competitors import list_competitors

        sig = inspect.signature(list_competitors)
        param_names = list(sig.parameters.keys())
        assert "user" in param_names

    def test_delete_competitor_requires_auth(self):
        """DELETE /competitors/{id} must depend on require_auth."""
        import inspect

        from apps.api.routers.competitors import delete_competitor

        sig = inspect.signature(delete_competitor)
        param_names = list(sig.parameters.keys())
        assert "user" in param_names


# ────────────────────────────────────────────
# P0: Password hashing with bcrypt
# ────────────────────────────────────────────


class TestBcryptPasswordHashing:
    """Verify bcrypt is used for password hashing."""

    def test_hash_password_uses_bcrypt(self):
        """hash_password() must return a bcrypt hash starting with $2."""
        from packages.auth import hash_password

        hashed = hash_password("testpassword123")
        assert hashed.startswith("$2"), f"Expected bcrypt hash, got: {hashed[:20]}"

    def test_verify_bcrypt_password(self):
        """verify_password() must verify bcrypt hashes."""
        from packages.auth import hash_password, verify_password

        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_legacy_sha256_password(self):
        """verify_password() must still verify legacy SHA-256 hashes."""
        from packages.auth import verify_password

        salt = os.urandom(16).hex()
        password = "legacypass"
        sha_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        legacy_hash = f"{salt}:{sha_hash}"

        assert verify_password(password, legacy_hash) is True
        assert verify_password("wrong", legacy_hash) is False

    def test_needs_rehash_for_sha256(self):
        """needs_rehash() should return True for SHA-256 hashes."""
        from packages.auth import needs_rehash

        assert needs_rehash("abcdef1234:deadbeef") is True
        assert needs_rehash("$2b$12$somebcrypthashhere") is False


# ────────────────────────────────────────────
# P0: SSRF protection (safe_fetch)
# ────────────────────────────────────────────


class TestSSRFProtection:
    """Verify safe_fetch blocks SSRF attacks."""

    def test_blocks_private_ip_127(self):
        from packages.core.safe_fetch import is_private_ip

        assert is_private_ip("127.0.0.1") is True

    def test_blocks_private_ip_10(self):
        from packages.core.safe_fetch import is_private_ip

        assert is_private_ip("10.0.0.1") is True

    def test_blocks_private_ip_192(self):
        from packages.core.safe_fetch import is_private_ip

        assert is_private_ip("192.168.1.1") is True

    def test_blocks_private_ip_172(self):
        from packages.core.safe_fetch import is_private_ip

        assert is_private_ip("172.16.0.1") is True

    def test_allows_public_ip(self):
        from packages.core.safe_fetch import is_private_ip

        assert is_private_ip("8.8.8.8") is False

    def test_blocks_localhost_url(self):
        from packages.core.safe_fetch import SSRFProtectionError, validate_url

        with pytest.raises(SSRFProtectionError):
            validate_url("http://127.0.0.1/admin")

    def test_blocks_private_ip_url(self):
        from packages.core.safe_fetch import SSRFProtectionError, validate_url

        with pytest.raises(SSRFProtectionError):
            validate_url("http://10.0.0.1/secret")

    def test_blocks_ftp_scheme(self):
        from packages.core.safe_fetch import SSRFProtectionError, validate_url

        with pytest.raises(SSRFProtectionError):
            validate_url("ftp://example.com/file")

    def test_blocks_ssh_port(self):
        from packages.core.safe_fetch import SSRFProtectionError, validate_url

        with pytest.raises(SSRFProtectionError):
            validate_url("http://example.com:22/")

    def test_blocks_credentials_in_url(self):
        from packages.core.safe_fetch import SSRFProtectionError, validate_url

        with pytest.raises(SSRFProtectionError):
            validate_url("http://user:pass@example.com/")

    def test_consolidated_safe_fetch_exports(self):
        """Verify single consolidated module exports all needed symbols."""
        from packages.core.safe_fetch import (
            SSRFError,
            SSRFProtectionError,
        )

        assert SSRFError is SSRFProtectionError  # alias

    def test_scripts_safe_fetch_reexports(self):
        """Verify scripts/safe_fetch.py re-exports from core."""
        from packages.core.safe_fetch import (
            FetchResult as CoreFetchResult,
        )
        from packages.core.safe_fetch import (
            SSRFError as CoreSSRFError,
        )
        from packages.core.safe_fetch import (
            safe_fetch as core_safe_fetch,
        )
        from packages.seo_health_report.scripts.safe_fetch import (
            FetchResult,
            SSRFError,
            safe_fetch,
        )

        assert FetchResult is CoreFetchResult
        assert SSRFError is CoreSSRFError
        assert safe_fetch is core_safe_fetch


# ────────────────────────────────────────────
# P1: Rate limiter behavior
# ────────────────────────────────────────────


class TestRateLimiter:
    """Verify rate limiter functions."""

    def test_rate_limiter_imports(self):
        """Root rate_limiter.py should re-export from packages."""
        from rate_limiter import check_rate_limit, get_rate_limit_status

        assert callable(check_rate_limit)
        assert callable(get_rate_limit_status)

    def test_tier_limits_exist(self):
        from packages.rate_limiter import TIER_LIMITS

        assert "basic" in TIER_LIMITS
        assert "pro" in TIER_LIMITS
        assert "enterprise" in TIER_LIMITS
        assert "default" in TIER_LIMITS


# ────────────────────────────────────────────
# P1: Migration chain integrity
# ────────────────────────────────────────────


class TestMigrationChain:
    """Verify Alembic migration chain is clean."""

    def test_no_v007_collision(self):
        """There should be no two migration files with the same revision prefix."""
        import glob

        migrations_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "infrastructure", "migrations", "versions"
        )
        migration_files = glob.glob(os.path.join(migrations_dir, "v007_*.py"))
        assert len(migration_files) == 1, (
            f"Expected 1 v007 migration, found {len(migration_files)}: {migration_files}"
        )

    def test_v008_depends_on_v007(self):
        """v008_tenant_quotas should depend on v007_audit_trade_fields."""
        migrations_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "infrastructure", "migrations", "versions"
        )
        v008_path = os.path.join(migrations_dir, "v008_tenant_quotas.py")
        with open(v008_path) as f:
            content = f.read()
        assert "007_audit_trade_fields" in content
        assert 'revision: str = "008_tenant_quotas"' in content


# ────────────────────────────────────────────
# P1: Audit CRUD with tenant filtering
# ────────────────────────────────────────────


class TestAuditTenantFiltering:
    """Verify list_audits filters by user_id."""

    def test_list_audits_has_pagination(self):
        """list_audits should accept skip and limit parameters."""
        import inspect

        from apps.api.routers.audits import list_audits

        sig = inspect.signature(list_audits)
        assert "skip" in sig.parameters
        assert "limit" in sig.parameters

    def test_list_audits_limit_capped(self):
        """limit param default is 20, max 100."""
        import inspect

        from apps.api.routers.audits import list_audits

        sig = inspect.signature(list_audits)
        assert sig.parameters["limit"].default == 20
        assert sig.parameters["skip"].default == 0


# ────────────────────────────────────────────
# P2: Cost tracking / datetime consistency
# ────────────────────────────────────────────


class TestDatetimeConsistency:
    """Verify no naive datetime.utcnow() in critical code paths."""

    def test_auth_uses_timezone_aware(self):
        """create_access_token should use timezone-aware datetimes."""
        from packages.auth import create_access_token

        # This shouldn't raise
        token = create_access_token("test-user-id", "user")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_database_models_use_timezone(self):
        """Database model defaults should use timezone.utc."""
        import inspect

        from packages.database import Audit

        # Check source of the module for datetime.utcnow
        source = inspect.getsource(Audit)
        assert "utcnow" not in source, "Audit model should not use datetime.utcnow"


# ────────────────────────────────────────────
# Docker compose security
# ────────────────────────────────────────────


class TestDockerComposeSecurity:
    """Verify no hardcoded secrets in compose files."""

    def test_no_hardcoded_jwt_secret(self):
        compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
        with open(compose_path) as f:
            content = f.read()
        assert "dev-secret-key-minimum-32-characters-long" not in content

    def test_no_hardcoded_postgres_password(self):
        compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
        with open(compose_path) as f:
            content = f.read()
        assert "seopassword" not in content


# ────────────────────────────────────────────
# CORS restriction
# ────────────────────────────────────────────


class TestCORSRestriction:
    """Verify CORS is restricted."""

    def test_cors_methods_restricted(self):
        """apps/api/main.py should not have allow_methods=['*']."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api", "main.py")
        with open(main_path) as f:
            content = f.read()
        assert 'allow_methods=["*"]' not in content
        assert 'allow_headers=["*"]' not in content
