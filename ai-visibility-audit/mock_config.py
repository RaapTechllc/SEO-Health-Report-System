"""Mock config for testing."""

class MockConfig:
    def __init__(self):
        self.anthropic_model = "claude-3-sonnet-20240229"

def get_config():
    return MockConfig()