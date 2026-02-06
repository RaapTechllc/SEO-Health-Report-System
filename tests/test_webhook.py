"""
Webhook Tests.

Tests signing, URL validation, and delivery.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.seo_health_report.scripts.safe_fetch import SSRFError
from packages.seo_health_report.scripts.webhook import (
    build_audit_webhook_payload,
    deliver_webhook,
    sign_webhook_payload,
    validate_callback_url,
    verify_webhook_signature,
)


class TestWebhookSigning:
    """Test HMAC signature generation and verification."""

    def test_sign_produces_hex_string(self):
        sig = sign_webhook_payload({"test": "data"}, "secret")
        assert isinstance(sig, str)
        assert len(sig) == 64

    def test_same_payload_same_signature(self):
        payload = {"audit_id": "123", "status": "completed"}
        sig1 = sign_webhook_payload(payload, "secret")
        sig2 = sign_webhook_payload(payload, "secret")
        assert sig1 == sig2

    def test_different_secret_different_signature(self):
        payload = {"test": "data"}
        sig1 = sign_webhook_payload(payload, "secret1")
        sig2 = sign_webhook_payload(payload, "secret2")
        assert sig1 != sig2

    def test_verify_valid_signature(self):
        payload = {"test": "data"}
        sig = sign_webhook_payload(payload, "secret")
        assert verify_webhook_signature(payload, sig, "secret")

    def test_verify_invalid_signature(self):
        payload = {"test": "data"}
        assert not verify_webhook_signature(payload, "invalid", "secret")

    def test_verify_wrong_secret(self):
        payload = {"test": "data"}
        sig = sign_webhook_payload(payload, "secret1")
        assert not verify_webhook_signature(payload, sig, "secret2")


class TestCallbackURLValidation:
    """Test callback URL SSRF protection."""

    @pytest.mark.asyncio
    async def test_blocks_localhost(self):
        with patch('packages.seo_health_report.scripts.webhook.resolve_dns') as mock_dns:
            mock_dns.return_value = "127.0.0.1"

            with patch('packages.seo_health_report.scripts.webhook.validate_ip') as mock_validate:
                mock_validate.side_effect = SSRFError("IP address 127.0.0.1 is in blocked range")

                with pytest.raises(SSRFError):
                    await validate_callback_url("http://localhost/webhook")

    @pytest.mark.asyncio
    async def test_blocks_private_ip(self):
        with patch('packages.seo_health_report.scripts.webhook.resolve_dns') as mock_dns:
            mock_dns.return_value = "192.168.1.1"

            with patch('packages.seo_health_report.scripts.webhook.validate_ip') as mock_validate:
                mock_validate.side_effect = SSRFError("IP address 192.168.1.1 is in blocked range")

                with pytest.raises(SSRFError):
                    await validate_callback_url("http://internal.example.com/webhook")

    @pytest.mark.asyncio
    async def test_allows_public_url(self):
        with patch('packages.seo_health_report.scripts.webhook.resolve_dns') as mock_dns:
            mock_dns.return_value = "93.184.216.34"

            with patch('packages.seo_health_report.scripts.webhook.validate_ip'):
                await validate_callback_url("https://example.com/webhook")

    @pytest.mark.asyncio
    async def test_rejects_invalid_scheme(self):
        with pytest.raises(ValueError, match="scheme"):
            await validate_callback_url("ftp://example.com/webhook")

    @pytest.mark.asyncio
    async def test_rejects_missing_hostname(self):
        with pytest.raises(ValueError, match="hostname"):
            await validate_callback_url("https:///webhook")


class TestWebhookDelivery:
    """Test webhook delivery with retries."""

    @pytest.mark.asyncio
    async def test_successful_delivery(self):
        with patch('packages.seo_health_report.scripts.webhook.validate_callback_url', new_callable=AsyncMock):
            with patch('packages.seo_health_report.scripts.webhook.redact_dict', return_value={"test": "data"}):
                with patch('httpx.AsyncClient') as mock_client_class:
                    mock_response = MagicMock()
                    mock_response.status_code = 200

                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(return_value=mock_response)
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_class.return_value = mock_client

                    result = await deliver_webhook(
                        "https://example.com/webhook",
                        {"test": "data"},
                        "secret"
                    )

                    assert result.success
                    assert result.attempts == 1
                    assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_url_fails_immediately(self):
        with patch('packages.seo_health_report.scripts.webhook.validate_callback_url', new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = SSRFError("Blocked")

            result = await deliver_webhook(
                "http://localhost/webhook",
                {"test": "data"},
                "secret"
            )

            assert not result.success
            assert result.attempts == 0
            assert "Invalid callback URL" in result.error

    @pytest.mark.asyncio
    async def test_client_error_no_retry(self):
        """4xx errors (except 429) should not retry."""
        with patch('packages.seo_health_report.scripts.webhook.validate_callback_url', new_callable=AsyncMock):
            with patch('packages.seo_health_report.scripts.webhook.redact_dict', return_value={"test": "data"}):
                with patch('httpx.AsyncClient') as mock_client_class:
                    mock_response = MagicMock()
                    mock_response.status_code = 400

                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(return_value=mock_response)
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_class.return_value = mock_client

                    result = await deliver_webhook(
                        "https://example.com/webhook",
                        {"test": "data"},
                        "secret",
                        max_attempts=3
                    )

                    assert not result.success
                    assert result.attempts == 1


class TestWebhookPayloadBuilder:
    """Test webhook payload construction."""

    def test_completed_audit_payload(self):
        payload = build_audit_webhook_payload(
            audit_id="test-123",
            status="completed",
            overall_score=85,
            grade="B",
            report_url="/reports/test-123.html"
        )

        assert payload["event"] == "audit.completed"
        assert payload["audit_id"] == "test-123"
        assert payload["status"] == "completed"
        assert payload["overall_score"] == 85
        assert payload["grade"] == "B"
        assert "timestamp" in payload

    def test_failed_audit_payload(self):
        payload = build_audit_webhook_payload(
            audit_id="test-456",
            status="failed",
            error_message="Connection timeout"
        )

        assert payload["event"] == "audit.failed"
        assert payload["error"] == "Connection timeout"
        assert "overall_score" not in payload
