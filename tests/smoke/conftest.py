import os
import sys

import pytest

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

@pytest.fixture
def sample_url():
    """Sample URL for testing."""
    return "https://example.com"

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "company_name": "Test Corp",
        "primary_keywords": ["test keyword"],
        "output_format": "json"
    }
