
import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.getcwd())

import packages.ai_visibility_audit.scripts.query_ai_systems as query_ai
from packages.seo_health_report.tier_config import load_tier_config


class TestTierConfiguration(unittest.TestCase):
    """
    Integration tests for Tier Configuration system.
    Verifies that loading tiers correctly updates environment variables
    and that downstream modules pick up these changes dynamically.
    """

    def setUp(self):
        # Save original env
        self.original_env = os.environ.copy()

    def tearDown(self):
        # Restore original env
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_load_tier_config_sets_env_vars(self):
        """Test that load_tier_config sets the expected environment variables."""
        # Load LOW tier
        load_tier_config("low")
        self.assertEqual(os.environ.get("REPORT_TIER"), "low")
        self.assertIn("gpt-5-nano", os.environ.get("OPENAI_MODEL", ""))

        # Load HIGH tier
        load_tier_config("high")
        self.assertEqual(os.environ.get("REPORT_TIER"), "high")
        # Assuming HIGH uses a better model, or at least consistent with config
        # We don't hardcode the model here as config might change, but we check key presence
        self.assertIsNotNone(os.environ.get("ANTHROPIC_MODEL"))

    def test_query_modules_use_dynamic_config(self):
        """
        Verify that AI query modules read from os.environ at runtime,
        not just at import time. This prevents 'stale config' bugs.
        """
        async def run_test():
            # Mock the Anthropic client to capture the model passed
            with patch("anthropic.Anthropic") as MockAnthropic:
                mock_client = MagicMock()
                MockAnthropic.return_value = mock_client
                mock_messages = MagicMock()
                mock_client.messages = mock_messages

                # Mock response
                mock_msg = MagicMock()
                mock_msg.content = [MagicMock(text="Response")]
                mock_messages.create.return_value = mock_msg

                # 1. Test LOW Tier
                load_tier_config("low")
                expected_low = os.environ.get("ANTHROPIC_MODEL")

                # Call the function
                await query_ai.query_claude("test", "brand", api_key="test")

                # Verify arg
                args_low = mock_messages.create.call_args.kwargs
                self.assertEqual(args_low.get("model"), expected_low,
                                f"Detailed check: Expected {expected_low}, got {args_low.get('model')}")

                # 2. Test HIGH Tier
                load_tier_config("high")
                expected_high = os.environ.get("ANTHROPIC_MODEL")

                # Call again
                await query_ai.query_claude("test", "brand", api_key="test")

                # Verify arg
                args_high = mock_messages.create.call_args.kwargs
                self.assertEqual(args_high.get("model"), expected_high,
                                f"Detailed check: Expected {expected_high}, got {args_high.get('model')}")

        # Run async test
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(run_test())
        finally:
            loop.close()

if __name__ == "__main__":
    unittest.main()
