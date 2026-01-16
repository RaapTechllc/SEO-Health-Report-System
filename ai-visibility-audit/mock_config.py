"""Mock config for testing."""

class MockConfig:
    def __init__(self):
        self.anthropic_model = "claude-sonnet-4-5"

def get_config():
    return MockConfig()