"""Tests for webhook security: HMAC signing and SSRF protection."""

import pytest

from packages.seo_health_report.webhooks.security import (
    SSRFError,
    generate_secret,
    is_private_ip,
    sign_payload,
    validate_webhook_url,
    validate_webhook_url_strict,
    verify_signature,
)


class TestHMACSigning:
    """Tests for HMAC-SHA256 signing."""

    def test_sign_payload_returns_hex(self):
        signature = sign_payload('{"test": "data"}', "secret123")
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

    def test_sign_payload_deterministic(self):
        payload = '{"foo": "bar"}'
        secret = "my_secret"
        sig1 = sign_payload(payload, secret)
        sig2 = sign_payload(payload, secret)
        assert sig1 == sig2

    def test_sign_payload_different_secrets(self):
        payload = '{"test": true}'
        sig1 = sign_payload(payload, "secret1")
        sig2 = sign_payload(payload, "secret2")
        assert sig1 != sig2

    def test_sign_payload_different_payloads(self):
        secret = "shared_secret"
        sig1 = sign_payload('{"a": 1}', secret)
        sig2 = sign_payload('{"a": 2}', secret)
        assert sig1 != sig2

    def test_verify_signature_valid(self):
        payload = '{"event": "test"}'
        secret = "webhook_secret"
        signature = sign_payload(payload, secret)
        assert verify_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        payload = '{"event": "test"}'
        secret = "webhook_secret"
        assert verify_signature(payload, "invalid_signature", secret) is False

    def test_verify_signature_wrong_secret(self):
        payload = '{"event": "test"}'
        signature = sign_payload(payload, "correct_secret")
        assert verify_signature(payload, signature, "wrong_secret") is False

    def test_verify_signature_modified_payload(self):
        secret = "webhook_secret"
        original = '{"event": "test"}'
        signature = sign_payload(original, secret)
        modified = '{"event": "modified"}'
        assert verify_signature(modified, signature, secret) is False


class TestSecretGeneration:
    """Tests for secret generation."""

    def test_generate_secret_default_length(self):
        secret = generate_secret()
        assert len(secret) == 64  # 32 bytes = 64 hex chars

    def test_generate_secret_custom_length(self):
        secret = generate_secret(16)
        assert len(secret) == 32  # 16 bytes = 32 hex chars

    def test_generate_secret_unique(self):
        secrets = {generate_secret() for _ in range(100)}
        assert len(secrets) == 100


class TestPrivateIPDetection:
    """Tests for private IP detection."""

    @pytest.mark.parametrize("ip", [
        "10.0.0.1",
        "10.255.255.255",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.0.1",
        "192.168.255.255",
        "127.0.0.1",
        "127.0.0.2",
        "169.254.169.254",  # AWS metadata
    ])
    def test_private_ipv4_detected(self, ip):
        assert is_private_ip(ip) is True

    @pytest.mark.parametrize("ip", [
        "8.8.8.8",
        "1.1.1.1",
        "93.184.216.34",
        "203.0.113.50",
    ])
    def test_public_ipv4_allowed(self, ip):
        assert is_private_ip(ip) is False

    def test_ipv6_localhost_detected(self):
        assert is_private_ip("::1") is True

    def test_invalid_ip_blocked(self):
        assert is_private_ip("not-an-ip") is True


class TestSSRFProtection:
    """Tests for URL validation and SSRF protection."""

    def test_valid_https_url(self):
        is_valid, error = validate_webhook_url("https://example.com/webhook")
        assert is_valid is True
        assert error is None

    def test_valid_http_url(self):
        is_valid, error = validate_webhook_url("http://example.com/webhook")
        assert is_valid is True
        assert error is None

    def test_invalid_scheme_ftp(self):
        is_valid, error = validate_webhook_url("ftp://example.com/file")
        assert is_valid is False
        assert "HTTP or HTTPS" in error

    def test_invalid_scheme_file(self):
        is_valid, error = validate_webhook_url("file:///etc/passwd")
        assert is_valid is False

    def test_localhost_blocked(self):
        is_valid, error = validate_webhook_url("http://localhost/webhook")
        assert is_valid is False
        assert "localhost" in error.lower() or "private" in error.lower()

    def test_127_0_0_1_blocked(self):
        is_valid, error = validate_webhook_url("http://127.0.0.1/webhook")
        assert is_valid is False

    def test_metadata_endpoint_blocked(self):
        is_valid, error = validate_webhook_url("http://169.254.169.254/latest/meta-data/")
        assert is_valid is False

    def test_internal_hostname_blocked(self):
        is_valid, error = validate_webhook_url("http://metadata.google.internal/")
        assert is_valid is False
        assert "internal" in error.lower() or "blocked" in error.lower()

    def test_missing_hostname(self):
        is_valid, error = validate_webhook_url("https:///path")
        assert is_valid is False
        assert "hostname" in error.lower()

    def test_nonstandard_port_blocked(self):
        is_valid, error = validate_webhook_url("https://example.com:9999/webhook")
        assert is_valid is False
        assert "port" in error.lower()

    def test_allowed_ports(self):
        for port in [80, 443, 8080, 8443]:
            is_valid, _ = validate_webhook_url(f"https://example.com:{port}/webhook")
            assert is_valid is True, f"Port {port} should be allowed"

    def test_strict_validation_raises(self):
        with pytest.raises(SSRFError):
            validate_webhook_url_strict("http://localhost/")

    def test_strict_validation_passes(self):
        validate_webhook_url_strict("https://example.com/webhook")
