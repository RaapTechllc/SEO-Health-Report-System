import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

# Import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from api_server import app

client = TestClient(app)

class TestSecurity:
    """Test security middleware and authentication."""
    
    def test_cors_configuration(self):
        """Test CORS is properly configured."""
        response = client.options("/")
        assert response.status_code in [200, 405]  # OPTIONS may not be implemented
    
    @patch.dict(os.environ, {"API_KEY": "test-key"})
    def test_authentication_required(self):
        """Test that endpoints require authentication."""
        # Test without auth header
        response = client.post("/audit", json={
            "url": "https://example.com",
            "company_name": "Test Co"
        })
        assert response.status_code == 403  # Should require auth
    
    @patch.dict(os.environ, {"API_KEY": "test-key"})
    def test_valid_authentication(self):
        """Test that valid API key works."""
        headers = {"Authorization": "Bearer test-key"}
        response = client.get("/", headers=headers)
        assert response.status_code == 200
    
    def test_rate_limiting_headers(self):
        """Test that rate limiting headers are present."""
        response = client.get("/")
        # Rate limiting headers should be present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
    
    def test_invalid_api_key(self):
        """Test that invalid API key is rejected."""
        headers = {"Authorization": "Bearer invalid-key"}
        response = client.get("/", headers=headers)
        assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])
