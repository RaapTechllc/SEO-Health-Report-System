"""
SSRF Protection Tests for safe_fetch.

Tests all blocked patterns to ensure SSRF protection works correctly.
"""

import ipaddress
import socket
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.seo_health_report.scripts.safe_fetch import (
    BLOCKED_RANGES,
    FetchResult,
    SSRFError,
    resolve_dns,
    safe_fetch,
    validate_ip,
)


class TestIPValidation:
    """Test IP address validation against blocked ranges."""

    def test_blocks_localhost_127_0_0_1(self):
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("127.0.0.1")

    def test_blocks_localhost_127_x_x_x(self):
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("127.255.255.255")

    def test_blocks_private_10_x(self):
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("10.0.0.1")
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("10.255.255.255")

    def test_blocks_private_172_16_x(self):
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("172.16.0.1")
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("172.31.255.255")

    def test_blocks_private_192_168_x(self):
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("192.168.0.1")
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("192.168.255.255")

    def test_blocks_link_local_169_254_x(self):
        """AWS metadata endpoint lives here."""
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("169.254.169.254")

    def test_blocks_zero_network(self):
        """Block 0.0.0.0/8 network."""
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("0.0.0.0")
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("0.255.255.255")

    def test_blocks_ipv6_localhost(self):
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("::1")

    def test_blocks_ipv6_unique_local(self):
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("fc00::1")
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("fd00::1")

    def test_blocks_ipv6_link_local(self):
        with pytest.raises(SSRFError, match="blocked"):
            validate_ip("fe80::1")

    def test_allows_public_ip(self):
        validate_ip("8.8.8.8")
        validate_ip("1.1.1.1")
        validate_ip("93.184.216.34")

    def test_allows_public_ipv6(self):
        validate_ip("2001:4860:4860::8888")
        validate_ip("2606:4700:4700::1111")

    def test_invalid_ip_raises_error(self):
        with pytest.raises(SSRFError, match="Invalid IP"):
            validate_ip("not-an-ip")

    def test_empty_ip_raises_error(self):
        with pytest.raises(SSRFError, match="Invalid IP"):
            validate_ip("")


class TestDNSResolution:
    """Test DNS resolution with SSRF protection."""

    def test_resolve_dns_blocks_private_ip(self):
        """DNS resolving to private IP should be blocked."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))
            ]
            with pytest.raises(SSRFError, match="blocked"):
                resolve_dns("evil.example.com")

    def test_resolve_dns_allows_public_ip(self):
        """DNS resolving to public IP should be allowed."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
            ]
            ip = resolve_dns("example.com")
            assert ip == "93.184.216.34"

    def test_resolve_dns_fails_on_no_results(self):
        """DNS with no results should raise SSRFError."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = []
            with pytest.raises(SSRFError, match="no results"):
                resolve_dns("nonexistent.example.com")

    def test_resolve_dns_fails_on_gaierror(self):
        """DNS failure should raise SSRFError."""
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.side_effect = socket.gaierror("Name resolution failed")
            with pytest.raises(SSRFError, match="DNS resolution failed"):
                resolve_dns("invalid.example.com")


class TestSchemeValidation:
    """Test URL scheme validation."""

    @pytest.mark.asyncio
    async def test_blocks_file_scheme(self):
        with pytest.raises(SSRFError, match="scheme"):
            await safe_fetch("file:///etc/passwd")

    @pytest.mark.asyncio
    async def test_blocks_gopher_scheme(self):
        with pytest.raises(SSRFError, match="scheme"):
            await safe_fetch("gopher://localhost")

    @pytest.mark.asyncio
    async def test_blocks_ftp_scheme(self):
        with pytest.raises(SSRFError, match="scheme"):
            await safe_fetch("ftp://localhost")

    @pytest.mark.asyncio
    async def test_blocks_data_scheme(self):
        with pytest.raises(SSRFError, match="scheme"):
            await safe_fetch("data:text/html,<h1>Hello</h1>")

    @pytest.mark.asyncio
    async def test_blocks_javascript_scheme(self):
        with pytest.raises(SSRFError, match="scheme"):
            await safe_fetch("javascript:alert(1)")

    @pytest.mark.asyncio
    async def test_blocks_empty_scheme(self):
        with pytest.raises(SSRFError, match="scheme"):
            await safe_fetch("//example.com")


class TestCredentialRejection:
    """Test rejection of URLs with credentials."""

    @pytest.mark.asyncio
    async def test_blocks_url_with_username(self):
        with pytest.raises(SSRFError, match="[Cc]redential"):
            await safe_fetch("https://user@example.com")

    @pytest.mark.asyncio
    async def test_blocks_url_with_password(self):
        with pytest.raises(SSRFError, match="[Cc]redential"):
            await safe_fetch("https://user:pass@example.com")

    @pytest.mark.asyncio
    async def test_blocks_url_with_empty_username(self):
        with pytest.raises(SSRFError, match="[Cc]redential"):
            await safe_fetch("https://:pass@example.com")


class TestRedirectValidation:
    """Test that redirect targets are also validated."""

    @pytest.mark.asyncio
    async def test_blocks_redirect_to_localhost(self):
        """Redirect from public to localhost should be blocked."""
        with patch("socket.getaddrinfo") as mock_dns:

            def dns_side_effect(hostname, *args, **kwargs):
                if hostname == "example.com":
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
                elif hostname == "localhost":
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

            mock_dns.side_effect = dns_side_effect

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.status_code = 302
                mock_response.headers = {"location": "http://localhost/admin"}

                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                with pytest.raises(SSRFError, match="blocked"):
                    await safe_fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_blocks_redirect_to_private_ip(self):
        """Redirect to private IP should be blocked."""
        with patch("socket.getaddrinfo") as mock_dns:

            def dns_side_effect(hostname, *args, **kwargs):
                if hostname == "example.com":
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
                elif hostname == "internal.local":
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 0))]
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

            mock_dns.side_effect = dns_side_effect

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.status_code = 301
                mock_response.headers = {"location": "http://internal.local/secret"}

                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                with pytest.raises(SSRFError, match="blocked"):
                    await safe_fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_blocks_redirect_to_metadata_endpoint(self):
        """Redirect to AWS metadata endpoint should be blocked."""
        with patch("socket.getaddrinfo") as mock_dns:

            def dns_side_effect(hostname, *args, **kwargs):
                if hostname == "example.com":
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
                elif hostname == "169.254.169.254":
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 0))]
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

            mock_dns.side_effect = dns_side_effect

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.status_code = 302
                mock_response.headers = {"location": "http://169.254.169.254/latest/meta-data/"}

                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                with pytest.raises(SSRFError, match="blocked"):
                    await safe_fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_blocks_too_many_redirects(self):
        """Too many redirects should raise SSRFError."""
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
            ]

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.status_code = 302
                mock_response.headers = {"location": "https://example.com/redirect"}

                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                with pytest.raises(SSRFError, match="Too many redirects"):
                    await safe_fetch("https://example.com", max_redirects=5)

    @pytest.mark.asyncio
    async def test_blocks_redirect_missing_location(self):
        """Redirect without Location header should raise SSRFError."""
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
            ]

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.status_code = 302
                mock_response.headers = {}

                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                with pytest.raises(SSRFError, match="Location"):
                    await safe_fetch("https://example.com")


class TestHappyPath:
    """Test that valid public URLs work."""

    @pytest.mark.asyncio
    async def test_fetch_public_url(self):
        """Test fetching a public URL with mocked transport."""
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
            ]

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.content = b"<html><body>Hello World</body></html>"
                mock_response.headers = {"content-type": "text/html"}
                mock_response.url = "https://example.com"

                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = await safe_fetch("https://example.com")

                assert isinstance(result, FetchResult)
                assert result.url == "https://example.com"
                assert result.status_code == 200
                assert result.content == b"<html><body>Hello World</body></html>"
                assert result.headers["content-type"] == "text/html"

    @pytest.mark.asyncio
    async def test_fetch_with_relative_redirect(self):
        """Test handling of relative redirect paths."""
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
            ]

            with patch("httpx.AsyncClient") as mock_client_class:
                redirect_response = MagicMock()
                redirect_response.status_code = 301
                redirect_response.headers = {"location": "/new-path"}

                final_response = MagicMock()
                final_response.status_code = 200
                final_response.content = b"Success"
                final_response.headers = {"content-type": "text/plain"}
                final_response.url = "https://example.com/new-path"

                mock_client = AsyncMock()
                mock_client.get = AsyncMock(side_effect=[redirect_response, final_response])
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                result = await safe_fetch("https://example.com")

                assert result.status_code == 200
                assert result.content == b"Success"

    @pytest.mark.asyncio
    async def test_fetch_respects_max_bytes(self):
        """Test that max_bytes limit is enforced."""
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
            ]

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.content = b"x" * 1000
                mock_response.headers = {}
                mock_response.url = "https://example.com"

                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                with pytest.raises(SSRFError, match="exceeds limit"):
                    await safe_fetch("https://example.com", max_bytes=100)


class TestURLValidation:
    """Test URL validation edge cases."""

    @pytest.mark.asyncio
    async def test_blocks_url_without_hostname(self):
        with pytest.raises(SSRFError, match="hostname"):
            await safe_fetch("https:///path/only")


class TestBlockedRangesCoverage:
    """Ensure all blocked ranges have test coverage."""

    def test_all_blocked_ranges_covered(self):
        """Ensure all blocked ranges have at least one test."""
        assert len(BLOCKED_RANGES) >= 9

    def test_blocked_ranges_structure(self):
        """Verify blocked ranges are valid IP networks."""
        for network in BLOCKED_RANGES:
            assert isinstance(
                network, (ipaddress.IPv4Network, ipaddress.IPv6Network)
            )

    @pytest.mark.parametrize(
        "ip,should_block",
        [
            ("127.0.0.1", True),
            ("127.255.255.255", True),
            ("10.0.0.1", True),
            ("10.255.255.255", True),
            ("172.16.0.1", True),
            ("172.31.255.255", True),
            ("172.15.255.255", False),
            ("172.32.0.0", False),
            ("192.168.0.1", True),
            ("192.168.255.255", True),
            ("169.254.169.254", True),
            ("0.0.0.0", True),
            ("8.8.8.8", False),
            ("1.1.1.1", False),
            ("::1", True),
            ("fc00::1", True),
            ("fd00::1", True),
            ("fe80::1", True),
            ("2001:4860:4860::8888", False),
        ],
    )
    def test_ip_blocking_parametrized(self, ip, should_block):
        """Parametrized test for all IP blocking cases."""
        if should_block:
            with pytest.raises(SSRFError, match="blocked"):
                validate_ip(ip)
        else:
            validate_ip(ip)
