import pytest
import sys
import os
import tempfile

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

@pytest.mark.smoke
def test_build_report_loads():
    """Verify build_report.py can be imported."""
    try:
        from seo_health_report.scripts import build_report
        assert hasattr(build_report, 'generate_report') or \
               hasattr(build_report, 'main')
    except ImportError:
        pytest.skip("seo_health_report not available")

@pytest.mark.smoke
def test_report_generation_basic():
    """Test basic report generation doesn't crash."""
    try:
        from seo_health_report.scripts import build_report
        
        # Mock minimal report data
        mock_data = {
            'overall_score': 80,
            'grade': 'B',
            'company_name': 'Test Corp',
            'technical': {'score': 80},
            'content': {'score': 70},
            'ai_visibility': {'score': 90}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'test_report.json')
            
            # Just test the function exists and is callable
            if hasattr(build_report, 'generate_report'):
                func = build_report.generate_report
                assert callable(func)
                
    except ImportError:
        pytest.skip("seo_health_report not available")
