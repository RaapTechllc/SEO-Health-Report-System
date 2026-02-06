"""Stress test: 20 sequential audits without manual intervention."""
import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

sys.modules.setdefault("stripe", MagicMock())


def mock_enqueue_audit_job(db, audit_id, tenant_id, url, options, job_type):
    """Mock enqueue that just returns the audit_id without touching audit_jobs table."""
    return audit_id


def mock_check_rate_limit(request, tier="default", tenant_id=None):
    """Mock rate limit that always passes and returns valid rate info."""
    return {
        "limit": 1000,
        "remaining": 999,
        "reset": 60,
    }


def mock_check_endpoint_limit(request):
    """Mock endpoint limit that always passes."""
    return None


@pytest.fixture(scope="function")
def stress_client():
    """Create test client with isolated database and mocked dependencies."""
    os.environ["DATABASE_URL"] = "sqlite:///./test_stress.db"

    import database
    database.engine.dispose()
    database.engine = database.create_engine(
        "sqlite:///./test_stress.db",
        connect_args={"check_same_thread": False},
    )
    database.SessionLocal = database.sessionmaker(
        autocommit=False, autoflush=False, bind=database.engine
    )
    database.Base.metadata.drop_all(bind=database.engine)
    database.Base.metadata.create_all(bind=database.engine)

    patches = [
        patch("apps.api.main.enqueue_audit_job", mock_enqueue_audit_job),
        patch("apps.api.main.check_rate_limit", mock_check_rate_limit),
        patch("rate_limiter.check_rate_limit", mock_check_rate_limit),
        patch("apps.api.middleware.rate_limit.check_rate_limit", mock_check_rate_limit),
        patch("apps.api.middleware.rate_limit.check_endpoint_limit", mock_check_endpoint_limit),
    ]

    for p in patches:
        p.start()

    with patch("apps.api.main.run_full_audit") as mock_audit:
        mock_audit.return_value = {
            "overall_score": 75,
            "grade": "B",
            "audits": {
                "technical": {"score": 80},
                "content": {"score": 70},
                "ai_visibility": {"score": 75},
            },
        }
        from fastapi.testclient import TestClient

        from apps.api.main import app
        yield TestClient(app)

    for p in patches:
        p.stop()

    if os.path.exists("./test_stress.db"):
        os.remove("./test_stress.db")


class TestSequentialAudits:
    """Stress tests for sequential audit creation."""

    @pytest.mark.slow
    def test_20_sequential_audits(self, stress_client):
        """Run 20 audits sequentially and verify all complete."""
        results = []
        start_time = time.time()

        for i in range(20):
            response = stress_client.post(
                "/audit",
                json={
                    "url": f"https://test-site-{i}.example.com",
                    "company_name": f"Test Company {i}",
                    "tier": ["basic", "pro"][i % 2],
                },
            )
            assert response.status_code == 200, f"Audit {i} failed: {response.text}"
            results.append(response.json())

        elapsed = time.time() - start_time

        for idx, r in enumerate(results):
            assert "audit_id" in r, f"Audit {idx} missing audit_id"
            assert r["status"] in ["queued", "pending", "running", "completed"], (
                f"Audit {idx} has invalid status: {r['status']}"
            )

        print(f"\nCreated {len(results)} audits in {elapsed:.2f}s")
        print(f"Average: {elapsed / len(results):.3f}s per audit")

    @pytest.mark.slow
    def test_no_database_deadlocks(self, stress_client):
        """Verify sequential creation doesn't cause database issues."""
        audit_ids = set()

        for i in range(10):
            response = stress_client.post(
                "/audit",
                json={
                    "url": f"https://deadlock-test-{i}.example.com",
                    "company_name": f"Deadlock Test {i}",
                    "tier": "basic",
                },
            )
            assert response.status_code == 200
            data = response.json()
            audit_id = data["audit_id"]
            assert audit_id not in audit_ids, f"Duplicate audit_id: {audit_id}"
            audit_ids.add(audit_id)

            status_response = stress_client.get(f"/audit/{audit_id}")
            assert status_response.status_code == 200

        assert len(audit_ids) == 10

    @pytest.mark.slow
    def test_varied_tiers_sequential(self, stress_client):
        """Test sequential audits with all tier types."""
        tiers = ["basic", "pro", "enterprise"]
        results_by_tier = {t: [] for t in tiers}

        for i in range(15):
            tier = tiers[i % 3]
            response = stress_client.post(
                "/audit",
                json={
                    "url": f"https://tier-test-{i}.example.com",
                    "company_name": f"Tier Test {i}",
                    "tier": tier,
                },
            )
            assert response.status_code == 200
            results_by_tier[tier].append(response.json())

        for tier, results in results_by_tier.items():
            assert len(results) == 5, f"Expected 5 {tier} audits, got {len(results)}"

    @pytest.mark.slow
    def test_audit_retrieval_after_batch(self, stress_client):
        """Verify all audits can be retrieved after batch creation."""
        created_audits = []

        for i in range(10):
            response = stress_client.post(
                "/audit",
                json={
                    "url": f"https://batch-test-{i}.example.com",
                    "company_name": f"Batch Test {i}",
                    "tier": "basic",
                },
            )
            assert response.status_code == 200
            created_audits.append(response.json()["audit_id"])

        for audit_id in created_audits:
            response = stress_client.get(f"/audit/{audit_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["audit_id"] == audit_id
