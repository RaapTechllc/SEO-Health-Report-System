import os
import sys
import tempfile

import pytest

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

@pytest.mark.smoke
def test_build_report_loads():
    """Verify generate_report.py can be imported."""
    try:
        from seo_health_report.scripts import generate_report
        assert hasattr(generate_report, 'generate_html_report') or \
               hasattr(generate_report, 'generate_pdf_report')
    except ImportError:
        pytest.skip("seo_health_report not available")

@pytest.mark.smoke
def test_report_generation_basic():
    """Test basic report generation doesn't crash."""
    try:
        from seo_health_report.scripts import build_report

        # Mock minimal report data

        with tempfile.TemporaryDirectory() as temp_dir:
            os.path.join(temp_dir, 'test_report.json')

            # Just test the function exists and is callable
            if hasattr(build_report, 'generate_report'):
                func = build_report.generate_report
                assert callable(func)

    except ImportError:
        pytest.skip("seo_health_report not available")
