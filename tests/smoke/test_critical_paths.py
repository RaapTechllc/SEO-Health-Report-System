import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.mark.smoke
class TestSmokeTests:
    """Critical path smoke tests."""
    
    def test_imports_work(self):
        """Test that core modules can be imported."""
        try:
            from seo_health_report.scripts import orchestrate
            from seo_health_report.scripts import calculate_scores
            assert True
        except ImportError as e:
            pytest.fail(f"Core imports failed: {e}")
    
    def test_api_server_starts(self):
        """Test that API server can be imported and configured."""
        try:
            from api_server import app
            assert app is not None
            assert app.title == "SEO Health Report API"
        except Exception as e:
            pytest.fail(f"API server startup failed: {e}")
    
    def test_business_profiles_load(self):
        """Test that business profiles can be loaded."""
        try:
            from seo_health_report.business_profiles import list_available_profiles
            profiles = list_available_profiles()
            assert len(profiles) > 0
            assert any(p["name"] == "mechanical_trades" for p in profiles)
        except Exception as e:
            pytest.fail(f"Business profiles loading failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
