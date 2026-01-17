import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import sys

# Import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from api_server import app

client = TestClient(app)

class TestAPIIntegration:
    """Test full API workflow integration."""
    
    @patch.dict(os.environ, {"API_KEY": "test-key"})
    @patch('scripts.orchestrate.run_full_audit')
    def test_full_audit_workflow(self, mock_audit):
        """Test complete audit workflow."""
        # Mock audit response
        mock_audit.return_value = {
            "overall_score": 85,
            "grade": "B",
            "component_scores": {
                "technical": 80,
                "content": 85,
                "ai_visibility": 90
            }
        }
        
        headers = {"Authorization": "Bearer test-key"}
        response = client.post("/audit", 
            headers=headers,
            json={
                "url": "https://example.com",
                "company_name": "Test Company",
                "keywords": ["test", "seo"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "audit_id" in data
        assert data["status"] == "started"
    
    @patch.dict(os.environ, {"API_KEY": "test-key"})
    def test_business_profiles_endpoint(self):
        """Test business profiles endpoint."""
        headers = {"Authorization": "Bearer test-key"}
        response = client.get("/business-profiles", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
        assert len(data["profiles"]) > 0

if __name__ == "__main__":
    pytest.main([__file__])
