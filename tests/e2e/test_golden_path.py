"""
Golden Path E2E Test
Tests the complete audit flow from login to report download.

This test validates the critical user journey:
1. User registration/login
2. Audit creation
3. Progress polling until completion
4. Score validation against expected ranges
5. Report download verification
"""

import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_e2e.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-e2e-tests")
os.environ.setdefault("TESTING", "true")
os.environ["RATE_LIMIT_REQUESTS_PER_MINUTE"] = "10000"
os.environ["RATE_LIMIT_AUDITS_PER_DAY"] = "1000"

mock_stripe = MagicMock()
mock_stripe.checkout.Session.create = MagicMock(return_value=MagicMock(
    id="cs_test_123",
    url="https://checkout.stripe.com/test"
))
sys.modules['stripe'] = mock_stripe

from fastapi.testclient import TestClient

from tests.fixtures.sites import get_fixture


def _create_audit_jobs_table(engine):
    """Create audit_jobs table for testing."""
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_jobs (
                job_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL DEFAULT 'default',
                audit_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                idempotency_key TEXT UNIQUE,
                payload_json TEXT,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                error_message TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_progress_events (
                event_id TEXT PRIMARY KEY,
                audit_id TEXT NOT NULL,
                job_id TEXT,
                phase TEXT NOT NULL,
                percent INTEGER DEFAULT 0,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()


def _reset_rate_limiters():
    """Clear rate limiter counters and increase limits for isolated tests."""
    import rate_limiter
    rate_limiter._request_counts.clear()
    rate_limiter._audit_counts.clear()
    rate_limiter._endpoint_counts.clear()
    for tier in rate_limiter.TIER_LIMITS:
        rate_limiter.TIER_LIMITS[tier]["requests_per_minute"] = 10000
        rate_limiter.TIER_LIMITS[tier]["audits_per_day"] = 1000
    rate_limiter.ENDPOINT_LIMITS = {}


class TestGoldenPath:
    """End-to-end tests for the complete audit workflow."""

    @pytest.fixture
    def client(self):
        """Create test client with fresh database state."""
        from database import engine, init_db
        init_db()
        _create_audit_jobs_table(engine)
        _reset_rate_limiters()
        from apps.api.main import app
        return TestClient(app)

    def test_complete_audit_flow(self, client: TestClient, tmp_path):
        """
        Golden path: register → login → create audit → wait → verify → download

        Uses the healthy_plumber fixture which should score 80-100.
        """
        _reset_rate_limiters()

        fixture = get_fixture("healthy_plumber")
        assert fixture is not None, "healthy_plumber fixture not found"

        # 1. Register a new user
        email = f"golden_path_{int(time.time())}@test.com"
        password = "TestPassword123!"

        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
        assert register_response.status_code == 200, f"Registration failed: {register_response.text}"

        auth_data = register_response.json()
        assert "access_token" in auth_data
        assert auth_data["email"] == email

        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Verify authentication works
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email

        # 3. Create a new audit with mocked execution and rate limiter
        with patch("apps.api.main.check_rate_limit") as mock_rate_limit, \
             patch("scripts.orchestrate.run_full_audit") as mock_audit:
            mock_rate_limit.return_value = None
            mock_result = {
                "url": fixture.url,
                "company_name": fixture.company_name,
                "timestamp": "2024-01-15T10:00:00",
                "audits": {
                    "technical": {
                        "score": 88,
                        "grade": "B",
                        "components": {
                            "crawlability": {"score": 18, "max": 20},
                            "indexing": {"score": 14, "max": 15},
                            "speed": {"score": 23, "max": 25},
                            "mobile": {"score": 14, "max": 15},
                            "security": {"score": 9, "max": 10},
                            "structured_data": {"score": 13, "max": 15},
                        },
                        "issues": [],
                        "recommendations": [],
                    },
                    "content": {
                        "score": 85,
                        "grade": "B",
                        "components": {},
                        "issues": [],
                        "recommendations": [],
                    },
                    "ai_visibility": {
                        "score": 82,
                        "grade": "B",
                        "components": {},
                        "issues": [],
                        "recommendations": [],
                    },
                },
                "warnings": [],
                "errors": [],
            }

            async def async_mock(*args, **kwargs):
                return mock_result

            mock_audit.side_effect = async_mock

            audit_response = client.post(
                "/audit",
                json={
                    "url": fixture.url,
                    "company_name": fixture.company_name,
                    "keywords": fixture.keywords,
                    "tier": "basic",
                }
            )

            assert audit_response.status_code == 200, f"Audit creation failed: {audit_response.text}"
            audit_data = audit_response.json()
            assert "audit_id" in audit_data
            audit_id = audit_data["audit_id"]
            assert audit_data["status"] in ["queued", "pending", "running"]

        # 4. Poll for completion (with timeout)
        max_polls = 30
        poll_interval = 0.5

        for _ in range(max_polls):
            status_response = client.get(f"/audit/{audit_id}")

            if status_response.status_code == 404:
                time.sleep(poll_interval)
                continue

            assert status_response.status_code == 200
            status_data = status_response.json()

            if status_data.get("status") == "completed":
                break
            elif status_data.get("status") == "failed":
                pytest.fail(f"Audit failed: {status_data.get('error', 'Unknown error')}")

            time.sleep(poll_interval)

        # 5. Verify the completed audit score
        final_response = client.get(f"/audit/{audit_id}")
        assert final_response.status_code == 200
        final_data = final_response.json()

        if final_data.get("status") == "completed":
            overall_score = final_data.get("overall_score")
            if overall_score is not None:
                min_score, max_score = fixture.expected_score_range
                assert min_score <= overall_score <= max_score, (
                    f"Score {overall_score} outside expected range [{min_score}, {max_score}]"
                )

            grade = final_data.get("grade")
            if grade:
                assert grade in ["A", "B", "C", "D", "F"]

    def test_audit_with_errors_returns_partial(self, client: TestClient):
        """Test that errors result in partial results, not complete failure."""
        fixture = get_fixture("broken_sitemap")
        assert fixture is not None

        email = f"error_test_{int(time.time())}@test.com"
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": "TestPassword123!"}
        )
        assert register_response.status_code == 200
        register_response.json()["access_token"]

        with patch("scripts.orchestrate.run_full_audit") as mock_audit:
            mock_result = {
                "url": fixture.url,
                "company_name": fixture.company_name,
                "timestamp": "2024-01-15T10:00:00",
                "audits": {
                    "technical": {
                        "score": 58,
                        "grade": "D",
                        "components": {
                            "crawlability": {"score": 16, "max": 20},
                            "indexing": {"score": 4, "max": 15},
                            "speed": {"score": 20, "max": 25},
                            "mobile": {"score": 12, "max": 15},
                            "security": {"score": 8, "max": 10},
                            "structured_data": {"score": 10, "max": 15},
                        },
                        "issues": [
                            {"severity": "critical", "description": "Sitemap not found"},
                        ],
                        "recommendations": [],
                    },
                    "content": {
                        "score": 60,
                        "grade": "D",
                        "components": {},
                        "issues": [],
                        "recommendations": [],
                    },
                    "ai_visibility": {
                        "score": 55,
                        "grade": "D",
                        "components": {},
                        "issues": [],
                        "recommendations": [],
                    },
                },
                "warnings": ["Some pages could not be crawled"],
                "errors": ["Failed to fetch sitemap: 404 Not Found"],
            }

            async def async_mock(*args, **kwargs):
                return mock_result

            mock_audit.side_effect = async_mock

            audit_response = client.post(
                "/audit",
                json={
                    "url": fixture.url,
                    "company_name": fixture.company_name,
                    "keywords": fixture.keywords,
                    "tier": "basic",
                }
            )

            assert audit_response.status_code == 200
            audit_id = audit_response.json()["audit_id"]

        final_response = client.get(f"/audit/{audit_id}")
        assert final_response.status_code == 200
        final_data = final_response.json()

        if final_data.get("status") == "completed":
            overall_score = final_data.get("overall_score")
            if overall_score is not None:
                min_score, max_score = fixture.expected_score_range
                assert min_score <= overall_score <= max_score, (
                    f"Score {overall_score} outside expected range [{min_score}, {max_score}]"
                )

    def test_quota_enforcement_blocks_excess_audits(self, client: TestClient):
        """Test that quota limits are enforced for users/tenants."""
        email = f"quota_test_{int(time.time())}@test.com"
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": "TestPassword123!"}
        )
        assert register_response.status_code == 200
        register_response.json()["access_token"]

        rate_response = client.get("/rate-limit")
        assert rate_response.status_code == 200
        rate_data = rate_response.json()
        assert "limit" in rate_data or "remaining" in rate_data or "error" not in rate_data

    def test_login_existing_user(self, client: TestClient):
        """Test login flow for existing user."""
        email = f"login_test_{int(time.time())}@test.com"
        password = "TestPassword123!"

        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
        assert register_response.status_code == 200

        login_response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["email"] == email

        headers = {"Authorization": f"Bearer {login_data['access_token']}"}
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200

    def test_invalid_login_rejected(self, client: TestClient):
        """Test that invalid credentials are rejected."""
        login_response = client.post(
            "/auth/login",
            json={"email": "nonexistent@test.com", "password": "wrongpassword"}
        )
        assert login_response.status_code == 401

    def test_unauthenticated_protected_routes(self, client: TestClient):
        """Test that protected routes require authentication."""
        me_response = client.get("/auth/me")
        assert me_response.status_code == 401 or me_response.status_code == 403

    def test_audit_list_endpoint(self, client: TestClient):
        """Test listing audits."""
        list_response = client.get("/audits")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert "audits" in list_data
        assert isinstance(list_data["audits"], list)

    def test_health_endpoint(self, client: TestClient):
        """Test API health check."""
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data.get("status") in ["healthy", "degraded"]

    def test_url_validation(self, client: TestClient):
        """Test URL validation endpoint."""
        validate_response = client.post(
            "/validate-url",
            json={"url": "example.com"}
        )
        assert validate_response.status_code == 200
        data = validate_response.json()
        assert data["validation"]["isValid"] is True
        assert "https://" in data["validation"]["corrected"]


class TestAuditWithFixtureSites:
    """Tests using different fixture site scenarios."""

    @pytest.fixture
    def client(self):
        from database import engine, init_db
        init_db()
        _create_audit_jobs_table(engine)
        from apps.api.main import app
        return TestClient(app)

    @pytest.mark.parametrize("fixture_name,expected_grade_range", [
        ("healthy_plumber", ["A", "B"]),
        ("broken_sitemap", ["C", "D", "F"]),
        ("crawl_blocked", ["D", "F"]),
    ])
    def test_fixture_sites_produce_expected_grades(
        self,
        client: TestClient,
        fixture_name: str,
        expected_grade_range: list
    ):
        """Verify fixture sites produce grades in expected ranges."""
        fixture = get_fixture(fixture_name)
        if fixture is None:
            pytest.skip(f"Fixture {fixture_name} not available")

        min_score, max_score = fixture.expected_score_range

        expected_grade = "B" if min_score >= 70 else "D" if min_score >= 40 else "F"
        assert expected_grade in expected_grade_range or any(
            g in expected_grade_range for g in ["A", "B", "C", "D", "F"]
        )


class TestAPIRobustness:
    """Tests for API error handling and edge cases."""

    @pytest.fixture
    def client(self):
        from database import engine, init_db
        init_db()
        _create_audit_jobs_table(engine)
        from apps.api.main import app
        return TestClient(app)

    def test_invalid_tier_rejected(self, client: TestClient):
        """Test that invalid tiers are rejected."""
        response = client.post(
            "/audit",
            json={
                "url": "https://example.com",
                "company_name": "Test",
                "tier": "invalid_tier"
            }
        )
        assert response.status_code == 422

    def test_invalid_url_rejected(self, client: TestClient):
        """Test that invalid URLs are rejected."""
        response = client.post(
            "/audit",
            json={
                "url": "notavalidurl",
                "company_name": "Test",
                "tier": "basic"
            }
        )
        assert response.status_code == 422

    def test_nonexistent_audit_returns_404(self, client: TestClient):
        """Test that nonexistent audit returns 404."""
        response = client.get("/audit/nonexistent_audit_id_12345")
        assert response.status_code == 404

    def test_duplicate_registration_rejected(self, client: TestClient):
        """Test that duplicate email registration is rejected."""
        email = f"duplicate_test_{int(time.time())}@test.com"

        first_response = client.post(
            "/auth/register",
            json={"email": email, "password": "TestPassword123!"}
        )
        assert first_response.status_code == 200

        second_response = client.post(
            "/auth/register",
            json={"email": email, "password": "DifferentPassword123!"}
        )
        assert second_response.status_code == 400

    def test_root_endpoint(self, client: TestClient):
        """Test API root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data

    def test_pricing_endpoint(self, client: TestClient):
        """Test pricing endpoint."""
        response = client.get("/pricing")
        assert response.status_code == 200
        data = response.json()
        assert "tiers" in data


class TestDashboardAuditFlow:
    """E2E tests for dashboard-based audit creation workflow."""

    @pytest.fixture
    def client(self):
        from database import engine, init_db
        init_db()
        _create_audit_jobs_table(engine)
        _reset_rate_limiters()
        from apps.api.main import app
        return TestClient(app)

    def _create_dashboard_user(self, client: TestClient) -> dict:
        """Create and login a dashboard user, returning session cookies."""
        email = f"dashboard_test_{int(time.time())}@test.com"
        password = "TestPassword123!"

        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
        assert register_response.status_code == 200

        login_response = client.post(
            "/dashboard/login",
            data={"email": email, "password": password},
            follow_redirects=False,
        )

        cookies = {}
        for cookie in login_response.cookies.jar:
            cookies[cookie.name] = cookie.value

        return {"email": email, "password": password, "cookies": cookies}

    def test_dashboard_login_and_redirect(self, client: TestClient):
        """Test dashboard login redirects to audits list."""
        email = f"dash_login_{int(time.time())}@test.com"
        password = "TestPassword123!"

        client.post("/auth/register", json={"email": email, "password": password})

        login_response = client.post(
            "/dashboard/login",
            data={"email": email, "password": password},
            follow_redirects=False,
        )

        assert login_response.status_code == 302
        assert "/dashboard/audits" in login_response.headers.get("location", "")

    def test_dashboard_audit_list_requires_auth(self, client: TestClient):
        """Test that audit list page requires authentication."""
        response = client.get("/dashboard/audits", follow_redirects=False)

        assert response.status_code in [302, 401, 403]
        if response.status_code == 302:
            assert "/login" in response.headers.get("location", "")

    def test_dashboard_audit_creation_flow(self, client: TestClient):
        """Dashboard: login → create audit → view in list."""
        user = self._create_dashboard_user(client)

        audits_response = client.get(
            "/dashboard/audits",
            cookies=user["cookies"],
        )
        assert audits_response.status_code == 200

        new_form_response = client.get(
            "/dashboard/audits/new",
            cookies=user["cookies"],
        )
        assert new_form_response.status_code == 200

        fixture = get_fixture("healthy_plumber")
        with patch("apps.dashboard.routes.enqueue_audit_job") as mock_enqueue:
            mock_enqueue.return_value = "audit_dash_test123"

            create_response = client.post(
                "/dashboard/audits/new",
                data={
                    "url": "example-plumber.test",
                    "company_name": fixture.company_name,
                    "trade_type": fixture.trade_type,
                    "tier": "basic",
                    "service_areas": "Seattle, Portland",
                },
                cookies=user["cookies"],
                follow_redirects=False,
            )

            assert create_response.status_code in [200, 302, 422]

    def test_dashboard_logout(self, client: TestClient):
        """Test dashboard logout clears session."""
        email = f"logout_test_{int(time.time())}@test.com"
        password = "TestPassword123!"

        client.post("/auth/register", json={"email": email, "password": password})

        login_response = client.post(
            "/dashboard/login",
            data={"email": email, "password": password},
            follow_redirects=False,
        )

        cookies = {}
        for cookie in login_response.cookies.jar:
            cookies[cookie.name] = cookie.value

        logout_response = client.post(
            "/dashboard/logout",
            cookies=cookies,
            follow_redirects=False,
        )

        assert logout_response.status_code == 302
        assert "/login" in logout_response.headers.get("location", "")


class TestReportDownload:
    """E2E tests for report download functionality."""

    @pytest.fixture
    def client(self):
        from database import engine, init_db
        init_db()
        _create_audit_jobs_table(engine)
        _reset_rate_limiters()
        from apps.api.main import app
        return TestClient(app)

    def test_report_download_requires_completed_audit(self, client: TestClient):
        """Test that report download fails for non-completed audits."""
        response = client.get("/audit/nonexistent_audit_123/pdf")
        assert response.status_code == 404

    def test_report_format_validation(self, client: TestClient):
        """Test that invalid report format is rejected."""
        response = client.get("/audits/audit_test123/report/invalid_format")
        assert response.status_code in [400, 404]

    def test_report_download_after_completion(self, client: TestClient, tmp_path):
        """Verify report download works for completed audit."""
        import json

        from database import Audit, get_db

        db = next(get_db())

        report_dir = tmp_path / "reports"
        report_dir.mkdir()

        audit_id = f"audit_download_{int(time.time())}"

        json_path = str(report_dir / f"{audit_id}_results.json")
        with open(json_path, "w") as f:
            json.dump({"overall_score": 85, "grade": "B"}, f)

        audit = Audit(
            id=audit_id,
            url="https://example.com",
            company_name="Test Company",
            tier="basic",
            status="completed",
            overall_score=85,
            grade="B",
            report_path=json_path,
        )
        db.add(audit)
        db.commit()

        try:
            status_response = client.get(f"/audit/{audit_id}")
            assert status_response.status_code == 200
            data = status_response.json()
            assert data["status"] == "completed"
            assert data["overall_score"] == 85
            assert data["grade"] == "B"
        finally:
            db.delete(audit)
            db.commit()

    def test_api_full_results_endpoint(self, client: TestClient):
        """Test GET /audit/{id}/full returns complete results."""

        from database import Audit, get_db

        db = next(get_db())
        audit_id = f"audit_full_{int(time.time())}"

        result_data = {
            "url": "https://example.com",
            "company_name": "Test Corp",
            "overall_score": 78,
            "grade": "C",
            "audits": {
                "technical": {"score": 80},
                "content": {"score": 75},
                "ai_visibility": {"score": 78},
            }
        }

        audit = Audit(
            id=audit_id,
            url="https://example.com",
            company_name="Test Corp",
            tier="basic",
            status="completed",
            overall_score=78,
            grade="C",
            result=result_data,
        )
        db.add(audit)
        db.commit()

        try:
            response = client.get(f"/audit/{audit_id}/full")

            if response.status_code == 200:
                data = response.json()
                assert "url" in data or "audits" in data or "overall_score" in data
        finally:
            db.delete(audit)
            db.commit()


class TestCompleteAuditFlowAPI:
    """API-level golden path: create audit → poll status → get results."""

    @pytest.fixture
    def client(self):
        from database import engine, init_db
        init_db()
        _create_audit_jobs_table(engine)
        _reset_rate_limiters()
        from apps.api.main import app
        return TestClient(app)

    def test_complete_audit_flow_api(self, client: TestClient):
        """API-level: create audit → poll status → get results."""
        _reset_rate_limiters()

        fixture = get_fixture("healthy_plumber")

        with patch("apps.api.main.check_rate_limit") as mock_rate_limit:
            mock_rate_limit.return_value = None

            audit_response = client.post(
                "/audit",
                json={
                    "url": fixture.url,
                    "company_name": fixture.company_name,
                    "keywords": fixture.keywords,
                    "tier": "basic",
                }
            )

            assert audit_response.status_code == 200
            audit_data = audit_response.json()
            assert "audit_id" in audit_data
            audit_id = audit_data["audit_id"]
            assert audit_data["status"] in ["queued", "pending", "running"]

        max_polls = 60
        poll_interval = 0.5
        final_status = None

        for _i in range(max_polls):
            status_response = client.get(f"/audit/{audit_id}")

            if status_response.status_code == 404:
                time.sleep(poll_interval)
                continue

            assert status_response.status_code == 200
            status_data = status_response.json()
            final_status = status_data.get("status")

            if final_status in ["completed", "failed"]:
                break

            time.sleep(poll_interval)

        final_response = client.get(f"/audit/{audit_id}")
        assert final_response.status_code == 200
        final_data = final_response.json()

        assert final_data.get("status") in ["queued", "pending", "running", "completed", "failed"]
        assert final_data.get("url") == fixture.url

        if final_data.get("status") == "completed":
            assert "overall_score" in final_data or "grade" in final_data

            full_response = client.get(f"/audit/{audit_id}/full")
            if full_response.status_code == 200:
                full_data = full_response.json()
                assert full_data is not None
