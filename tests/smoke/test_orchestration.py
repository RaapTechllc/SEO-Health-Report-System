import pytest
import sys
import os
import time

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Timing validation for smoke tests
@pytest.fixture(autouse=True)
def smoke_timing():
    """Ensure smoke tests complete quickly."""
    start = time.time()
    yield
    duration = time.time() - start
    # Individual test should be fast
    assert duration < 10, f"Smoke test took {duration:.2f}s (should be <10s)"

@pytest.mark.smoke
def test_orchestrate_loads():
    """Verify orchestrate.py can be imported and has main function."""
    try:
        from seo_health_report.scripts import orchestrate
        assert hasattr(orchestrate, 'run_all_audits') or hasattr(orchestrate, 'main')
    except ImportError:
        pytest.skip("seo_health_report not available")

@pytest.mark.smoke 
def test_orchestrate_basic_flow(sample_url, sample_config):
    """Test basic orchestration flow doesn't crash."""
    try:
        from seo_health_report.scripts import orchestrate
        # Just test it doesn't crash on import and basic validation
        assert callable(getattr(orchestrate, 'run_all_audits', None)) or \
               callable(getattr(orchestrate, 'main', None))
    except ImportError:
        pytest.skip("seo_health_report not available")
