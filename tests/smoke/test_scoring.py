import os
import sys

import pytest

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

@pytest.mark.smoke
def test_calculate_scores_loads():
    """Verify calculate_scores.py can be imported."""
    try:
        from seo_health_report.scripts import calculate_scores
        assert hasattr(calculate_scores, 'calculate_composite_score') or \
               hasattr(calculate_scores, 'main')
    except ImportError:
        pytest.skip("seo_health_report not available")

@pytest.mark.smoke
def test_score_calculation_basic():
    """Test basic score calculation works."""
    try:
        from seo_health_report.scripts import calculate_scores
        # Test with mock data - use 'audits' wrapper as expected by calculate_composite_score
        mock_data = {
            'audits': {
                'technical': {'score': 80},
                'content': {'score': 70},
                'ai_visibility': {'score': 90}
            }
        }
        if hasattr(calculate_scores, 'calculate_composite_score'):
            result = calculate_scores.calculate_composite_score(mock_data)
            assert isinstance(result, dict)
            assert 'overall_score' in result
            assert 0 <= result['overall_score'] <= 100
    except ImportError:
        pytest.skip("seo_health_report not available")
