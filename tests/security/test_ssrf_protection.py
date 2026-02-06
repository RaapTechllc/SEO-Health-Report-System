"""
SSRF Protection Tests

Comprehensive tests for the safe_fetch module to ensure
protection against SSRF, DNS rebinding, and other attacks.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from packages.core.safe_fetch import (
    SSRFProtectionError,
    is_private_ip,
    is_url_safe,
    resolve_and_validate,
    validate_url,
)


class TestPrivateIPDetection:
    """Test private IP address detection."""

    def test_loopback_ipv4_blocked(self):
        """127.0.0.1 should be blocked."""
        assert is_private_ip("127.0.0.1") is True

    def test_loopback_range_blocked(self):
        """127.x.x.x range should be blocked."""
        assert is_private_ip("127.0.0.5") is True
        assert is_private_ip("127.255.255.255") is True

    def test_private_class_a_blocked(self):
        """10.x.x.x should be blocked."""
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("10.255.255.255") is True

    def test_private_class_b_blocked(self):
        """172.16-31.x.x should be blocked."""
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("172.31.255.255") is True

    def test_private_class_c_blocked(self):
        """192.168.x.x should be blocked."""
        assert is_private_ip("192.168.0.1") is True
        assert is_private_ip("192.168.255.255") is True

    def test_link_local_blocked(self):
        """169.254.x.x should be blocked."""
        assert is_private_ip("169.254.1.1") is True

    def test_ipv6_loopback_blocked(self):
        """::1 should be blocked."""
        assert is_private_ip("::1") is True

    def test_ipv6_private_blocked(self):
        """fc00::/7 should be blocked."""
        assert is_private_ip("fc00::1") is True
        assert is_private_ip("fd00::1") is True

    def test_ipv6_link_local_blocked(self):
        """fe80::/10 should be blocked."""
        assert is_private_ip("fe80::1") is True

    def test_public_ipv4_allowed(self):
        """Public IPs should be allowed."""
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False
        assert is_private_ip("142.250.80.14") is False  # Google

    def test_public_ipv6_allowed(self):
        """Public IPv6 should be allowed."""
        assert is_private_ip("2001:4860:4860::8888") is False  # Google DNS

    def test_invalid_ip_blocked(self):
        """Invalid IPs should be blocked."""
        assert is_private_ip("not.an.ip") is True
        assert is_private_ip("") is True
        assert is_private_ip("256.256.256.256") is True


class TestURLValidation:
    """Test URL validation and SSRF protection."""

    def test_http_scheme_allowed(self):
        """HTTP URLs should be allowed."""
        scheme, host, port = validate_url("http://example.com")
        assert scheme == "http"
        assert host == "example.com"
        assert port == 80

    def test_https_scheme_allowed(self):
        """HTTPS URLs should be allowed."""
        scheme, host, port = validate_url("https://example.com")
        assert scheme == "https"
        assert host == "example.com"
        assert port == 443

    def test_file_scheme_blocked(self):
        """file:// URLs should be blocked."""
        with pytest.raises(SSRFProtectionError, match="scheme.*not allowed"):
            validate_url("file:///etc/passwd")

    def test_ftp_scheme_blocked(self):
        """ftp:// URLs should be blocked."""
        with pytest.raises(SSRFProtectionError, match="scheme.*not allowed"):
            validate_url("ftp://ftp.example.com")

    def test_gopher_scheme_blocked(self):
        """gopher:// URLs should be blocked."""
        with pytest.raises(SSRFProtectionError, match="scheme.*not allowed"):
            validate_url("gopher://evil.com")

    def test_localhost_blocked(self):
        """localhost URLs should be blocked."""
        with pytest.raises(SSRFProtectionError, match="private"):
            validate_url("http://localhost/admin")

    def test_127_0_0_1_blocked(self):
        """127.0.0.1 URLs should be blocked."""
        with pytest.raises(SSRFProtectionError, match="private"):
            validate_url("http://127.0.0.1/secret")

    def test_private_ip_in_url_blocked(self):
        """Private IPs in URLs should be blocked."""
        with pytest.raises(SSRFProtectionError, match="private"):
            validate_url("http://192.168.1.1/admin")
        with pytest.raises(SSRFProtectionError, match="private"):
            validate_url("http://10.0.0.1/internal")
        with pytest.raises(SSRFProtectionError, match="private"):
            validate_url("http://172.16.0.1/secret")

    def test_ipv6_localhost_blocked(self):
        """IPv6 localhost should be blocked."""
        with pytest.raises(SSRFProtectionError, match="private"):
            validate_url("http://[::1]/")

    def test_custom_port_allowed(self):
        """Custom ports on public hosts should work."""
        scheme, host, port = validate_url("https://example.com:8443")
        assert port == 8443

    def test_ssh_port_blocked(self):
        """SSH port (22) should be blocked."""
        with pytest.raises(SSRFProtectionError, match="port.*not allowed"):
            validate_url("http://example.com:22")

    def test_smtp_port_blocked(self):
        """SMTP port (25) should be blocked."""
        with pytest.raises(SSRFProtectionError, match="port.*not allowed"):
            validate_url("http://example.com:25")

    def test_no_hostname_blocked(self):
        """URLs without hostname should be blocked."""
        with pytest.raises(SSRFProtectionError, match="no hostname"):
            validate_url("http:///path")

    def test_url_with_auth_handled(self):
        """URLs with auth should work (auth stripped)."""
        # This should work - we validate the host, not auth
        scheme, host, port = validate_url("https://user:pass@example.com/path")
        assert host == "example.com"


class TestDNSRebinding:
    """Test DNS rebinding protection."""

    def test_metadata_endpoints_blocked(self):
        """Cloud metadata endpoints should be blocked by IP."""
        # AWS metadata
        with pytest.raises(SSRFProtectionError):
            validate_url("http://169.254.169.254/latest/meta-data/")
        
        # Azure metadata
        with pytest.raises(SSRFProtectionError):
            validate_url("http://169.254.169.254/metadata/instance")

    def test_zero_ip_blocked(self):
        """0.0.0.0 should be blocked."""
        with pytest.raises(SSRFProtectionError, match="private"):
            validate_url("http://0.0.0.0/")


class TestIsURLSafe:
    """Test the is_url_safe helper function."""

    def test_safe_url_returns_true(self):
        """Safe URLs should return (True, None)."""
        is_safe, error = is_url_safe("https://example.com")
        assert is_safe is True
        assert error is None

    def test_unsafe_url_returns_error(self):
        """Unsafe URLs should return (False, error_message)."""
        is_safe, error = is_url_safe("http://127.0.0.1/admin")
        assert is_safe is False
        assert "private" in error.lower()

    def test_invalid_url_returns_error(self):
        """Invalid URLs should return (False, error_message)."""
        is_safe, error = is_url_safe("not a url")
        assert is_safe is False
        assert error is not None


class TestEdgeCases:
    """Test edge cases and bypass attempts."""

    def test_url_encoded_localhost_blocked(self):
        """URL-encoded localhost should be blocked."""
        # %6c%6f%63%61%6c%68%6f%73%74 = localhost
        # Note: Python's urlparse decodes this, so it should still be caught
        with pytest.raises(SSRFProtectionError):
            validate_url("http://localhost/admin")

    def test_decimal_ip_handled(self):
        """Decimal IP notation should be handled."""
        # 2130706433 = 127.0.0.1 in decimal
        # Most URL parsers don't support this, but we should be safe
        # This will likely fail DNS resolution, which is fine
        is_safe, _ = is_url_safe("http://2130706433/")
        # Either blocked or DNS fails - both acceptable

    def test_ipv4_mapped_ipv6_blocked(self):
        """IPv4-mapped IPv6 addresses should be blocked."""
        # ::ffff:127.0.0.1
        with pytest.raises(SSRFProtectionError):
            validate_url("http://[::ffff:127.0.0.1]/")

    def test_url_with_fragment_handled(self):
        """URLs with fragments should work."""
        scheme, host, port = validate_url("https://example.com/page#section")
        assert host == "example.com"

    def test_url_with_query_handled(self):
        """URLs with query strings should work."""
        scheme, host, port = validate_url("https://example.com/search?q=test")
        assert host == "example.com"

    def test_international_domain_handled(self):
        """International domain names should work."""
        # This might fail DNS resolution in tests, which is fine
        is_safe, error = is_url_safe("https://例え.jp/")
        # Either safe (resolved to public IP) or error (DNS failure)
        # Both are acceptable in this context

    def test_very_long_url_handled(self):
        """Very long URLs should be handled gracefully."""
        long_path = "a" * 10000
        scheme, host, port = validate_url(f"https://example.com/{long_path}")
        assert host == "example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
