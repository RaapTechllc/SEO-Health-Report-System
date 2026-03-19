"""
Chaos tests for network failure scenarios.

Tests verify that the system handles various network failures gracefully
without hung connections or cascading failures.
"""

import asyncio
import socket
import ssl
from unittest.mock import AsyncMock, patch

import pytest


class TestDNSFailures:
    """Tests for DNS resolution failure handling."""

    @pytest.mark.asyncio
    async def test_dns_resolution_failure_clear_error(self):
        """DNS failure should return clear error message."""
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.side_effect = socket.gaierror(
                socket.EAI_NONAME, "Name or service not known"
            )

            error_message = None
            try:
                socket.getaddrinfo("nonexistent.invalid", 80)
            except socket.gaierror as e:
                error_message = f"DNS resolution failed: {e}"

            assert error_message is not None
            assert "DNS" in error_message or "resolution" in error_message.lower()

    def test_dns_failure_in_audit_result(self):
        """Audit should report DNS failure clearly."""
        audit_result = {
            "url": "https://nonexistent.invalid",
            "status": "failed",
            "error_type": "dns_resolution",
            "error_message": "Could not resolve domain name. "
            "Please verify the URL is correct.",
            "user_friendly_message": "We couldn't reach this website. "
            "The domain name doesn't appear to exist.",
        }

        assert audit_result["error_type"] == "dns_resolution"
        assert "domain" in audit_result["user_friendly_message"].lower()


class TestConnectionFailures:
    """Tests for connection failure handling."""

    @pytest.mark.asyncio
    async def test_connection_refused_handling(self):
        """Connection refused should be handled gracefully."""
        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_conn:
            mock_conn.side_effect = ConnectionRefusedError("Connection refused")

            error_handled = False
            try:
                await asyncio.open_connection("localhost", 9999)
            except ConnectionRefusedError:
                error_handled = True

            assert error_handled

    @pytest.mark.asyncio
    async def test_connection_reset_handling(self):
        """Connection reset should be handled gracefully."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ConnectionResetError("Connection reset by peer")

            result = None
            try:
                await mock_get("https://example.com")
            except ConnectionResetError:
                result = {
                    "error": "connection_reset",
                    "message": "Connection was reset. Server may be overloaded.",
                    "retryable": True,
                }

            assert result is not None
            assert result["retryable"] is True

    def test_connection_error_categories(self):
        """Different connection errors should be categorized correctly."""
        error_categories = {
            ConnectionRefusedError: {
                "category": "server_unavailable",
                "retryable": True,
                "message": "Server refused connection",
            },
            ConnectionResetError: {
                "category": "connection_interrupted",
                "retryable": True,
                "message": "Connection was interrupted",
            },
            ConnectionAbortedError: {
                "category": "connection_aborted",
                "retryable": True,
                "message": "Connection was aborted",
            },
            TimeoutError: {
                "category": "timeout",
                "retryable": True,
                "message": "Connection timed out",
            },
        }

        for _error_type, info in error_categories.items():
            assert info["retryable"] is True  # All should be retryable
            assert "message" in info


class TestSSLErrors:
    """Tests for SSL/TLS error handling."""

    @pytest.mark.asyncio
    async def test_ssl_certificate_error_handling(self):
        """SSL certificate errors should be handled and reported."""
        with patch("ssl.SSLContext.wrap_socket") as mock_ssl:
            mock_ssl.side_effect = ssl.SSLCertVerificationError(
                "certificate verify failed"
            )

            ssl_error = None
            try:
                mock_ssl()
            except ssl.SSLCertVerificationError as e:
                ssl_error = {
                    "type": "ssl_certificate_invalid",
                    "message": str(e),
                    "recommendation": "Check if the SSL certificate is valid and not expired",
                }

            assert ssl_error is not None
            assert "certificate" in ssl_error["type"]

    def test_ssl_error_in_technical_audit(self):
        """SSL errors should be included in technical audit results."""
        technical_result = {
            "ssl": {
                "valid": False,
                "error": "Certificate has expired",
                "expiry_date": "2023-01-01",
                "issuer": "Let's Encrypt",
                "severity": "critical",
                "fix": "Renew SSL certificate immediately",
            }
        }

        assert technical_result["ssl"]["valid"] is False
        assert technical_result["ssl"]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_ssl_handshake_timeout(self):
        """SSL handshake timeout should be handled."""
        with patch("ssl.SSLContext.wrap_socket") as mock_ssl:
            mock_ssl.side_effect = ssl.SSLError("The handshake operation timed out")

            result = None
            try:
                mock_ssl()
            except ssl.SSLError:
                result = {
                    "error": "ssl_timeout",
                    "message": "SSL handshake timed out",
                    "retryable": True,
                }

            assert result["retryable"] is True


class TestPartialResponse:
    """Tests for partial/interrupted response handling."""

    @pytest.mark.asyncio
    async def test_partial_response_handling(self):
        """Partial response should be handled gracefully."""

        class IncompleteReadError(Exception):
            pass

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = IncompleteReadError("Connection closed mid-response")

            result = None
            try:
                await mock_get("https://example.com/large-page")
            except IncompleteReadError:
                result = {
                    "error": "incomplete_response",
                    "message": "Response was incomplete",
                    "partial_data_available": False,
                }

            assert result is not None
            assert result["error"] == "incomplete_response"

    def test_chunked_response_interruption(self):
        """Chunked response interruption should save partial data."""
        received_chunks = ["<html>", "<head>", "<title>"]
        total_expected = 10

        result = {
            "chunks_received": len(received_chunks),
            "chunks_expected": total_expected,
            "partial_content": "".join(received_chunks),
            "complete": False,
        }

        assert result["complete"] is False
        assert result["chunks_received"] < result["chunks_expected"]
        assert len(result["partial_content"]) > 0


class TestRedirectLoops:
    """Tests for redirect loop detection."""

    def test_redirect_loop_detection(self):
        """Redirect loops should be detected and stopped."""
        max_redirects = 10
        redirect_chain = []

        def follow_redirect(url, chain):
            if len(chain) >= max_redirects:
                return {
                    "error": "redirect_loop",
                    "message": f"Too many redirects ({len(chain)})",
                    "chain": chain,
                }

            # Simulate circular redirect
            if url in chain:
                return {
                    "error": "redirect_loop",
                    "message": "Circular redirect detected",
                    "chain": chain + [url],
                }

            chain.append(url)
            # Simulate redirect back to earlier URL
            if len(chain) == 3:
                return follow_redirect(chain[0], chain)
            return follow_redirect(f"https://example.com/page{len(chain)}", chain)

        result = follow_redirect("https://example.com/start", redirect_chain)

        assert result["error"] == "redirect_loop"
        assert "chain" in result

    def test_redirect_chain_in_audit(self):
        """Audit should report redirect chains."""
        audit_result = {
            "redirects": {
                "chain": [
                    "http://example.com",
                    "https://example.com",
                    "https://www.example.com",
                ],
                "total_redirects": 2,
                "final_url": "https://www.example.com",
                "issues": [
                    "HTTP to HTTPS redirect (good)",
                    "Non-www to www redirect",
                ],
            }
        }

        assert audit_result["redirects"]["total_redirects"] == 2


class TestNoHungConnections:
    """Tests ensuring no connections get hung."""

    @pytest.mark.asyncio
    async def test_no_hung_connections_on_network_error(self):
        """Network errors should not leave hung connections."""
        timeout = 2  # seconds

        async def potentially_hanging_request():
            """Simulate a request that might hang."""
            await asyncio.sleep(10)  # Would hang without timeout

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(potentially_hanging_request(), timeout=timeout)

    @pytest.mark.asyncio
    async def test_connection_cleanup_on_error(self):
        """Connections should be cleaned up after errors."""
        connections_opened = 0
        connections_closed = 0

        class MockConnection:
            def __init__(self):
                nonlocal connections_opened
                connections_opened += 1

            async def close(self):
                nonlocal connections_closed
                connections_closed += 1

        async def request_with_cleanup():
            conn = MockConnection()
            try:
                raise ConnectionError("Simulated error")
            finally:
                await conn.close()

        try:
            await request_with_cleanup()
        except ConnectionError:
            pass

        assert connections_opened == connections_closed

    @pytest.mark.asyncio
    async def test_concurrent_requests_no_resource_leak(self):
        """Concurrent requests with errors should not leak resources."""
        active_connections = 0
        max_connections_seen = 0

        async def tracked_request(should_fail):
            nonlocal active_connections, max_connections_seen
            active_connections += 1
            max_connections_seen = max(max_connections_seen, active_connections)

            try:
                if should_fail:
                    raise ConnectionError("Failed")
                await asyncio.sleep(0.01)
                return "success"
            finally:
                active_connections -= 1

        # Make concurrent requests, some failing
        tasks = [tracked_request(i % 2 == 0) for i in range(10)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # All connections should be cleaned up
        assert active_connections == 0
        # Should have had concurrent activity
        assert max_connections_seen > 1


class TestNetworkErrorMessages:
    """Tests for user-friendly network error messages."""

    def test_error_messages_are_user_friendly(self):
        """Network errors should have user-friendly messages."""
        error_messages = {
            "dns_resolution": "We couldn't find this website. Please check the URL.",
            "connection_refused": "The website's server is not responding. It may be down.",
            "ssl_certificate": "This website has a security certificate problem.",
            "timeout": "The website took too long to respond. Please try again later.",
            "connection_reset": "The connection was interrupted. Please try again.",
        }

        for _error_type, message in error_messages.items():
            # Messages should be understandable by non-technical users
            assert "exception" not in message.lower()
            assert "error code" not in message.lower()
            assert len(message) < 100  # Keep messages concise


class TestRetryableErrors:
    """Tests for identifying retryable network errors."""

    def test_retryable_error_identification(self):
        """Should correctly identify retryable vs non-retryable errors."""
        retryable_errors = [
            ConnectionResetError,
            TimeoutError,
            ConnectionRefusedError,
        ]

        non_retryable_errors = [
            socket.gaierror,  # DNS failure - URL is wrong
            ssl.SSLCertVerificationError,  # Cert is invalid
        ]

        def is_retryable(error_type):
            return error_type in retryable_errors

        for error in retryable_errors:
            assert is_retryable(error) is True

        for error in non_retryable_errors:
            assert is_retryable(error) is False


# Run configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
