"""
Webhook security utilities: HMAC signing and SSRF protection.
"""

import hashlib
import hmac
import ipaddress
import secrets
import socket
from typing import Optional
from urllib.parse import urlparse


class SSRFError(Exception):
    """Raised when a URL fails SSRF validation."""
    pass


PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local
    ipaddress.ip_network("::1/128"),  # IPv6 localhost
    ipaddress.ip_network("fc00::/7"),  # IPv6 private
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",  # AWS/GCP metadata
}


def generate_secret(length: int = 32) -> str:
    """Generate a cryptographically secure webhook secret."""
    return secrets.token_hex(length)


def sign_payload(payload: str, secret: str) -> str:
    """
    Sign a payload using HMAC-SHA256.

    Args:
        payload: JSON string to sign
        secret: Webhook secret

    Returns:
        Hex-encoded HMAC signature
    """
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify an HMAC-SHA256 signature.

    Args:
        payload: Original JSON string
        signature: Hex-encoded signature to verify
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)


def is_private_ip(ip_str: str) -> bool:
    """Check if an IP address is in a private/reserved range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in PRIVATE_IP_RANGES:
            if ip in network:
                return True
        return False
    except ValueError:
        return True  # Invalid IP, treat as blocked


def validate_webhook_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate a webhook URL for SSRF protection.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # Must be HTTPS (or HTTP for local dev)
    if parsed.scheme not in ("http", "https"):
        return False, "URL must use HTTP or HTTPS"

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must have a hostname"

    # Block known dangerous hostnames
    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES:
        return False, f"Blocked hostname: {hostname}"

    # Block internal/cloud metadata endpoints
    if "metadata" in hostname_lower or "internal" in hostname_lower:
        return False, "Internal hostnames are blocked"

    # Resolve hostname and check IP
    try:
        ip_addresses = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
        for _family, _, _, _, sockaddr in ip_addresses:
            ip_str = sockaddr[0]
            if is_private_ip(ip_str):
                return False, f"Private IP addresses are blocked: {ip_str}"
    except socket.gaierror:
        return False, f"Could not resolve hostname: {hostname}"

    # Block non-standard ports that might indicate internal services
    port = parsed.port
    if port and port not in (80, 443, 8080, 8443):
        return False, f"Non-standard port blocked: {port}"

    return True, None


def validate_webhook_url_strict(url: str) -> None:
    """
    Validate URL and raise SSRFError if invalid.

    Args:
        url: URL to validate

    Raises:
        SSRFError: If URL fails validation
    """
    is_valid, error = validate_webhook_url(url)
    if not is_valid:
        raise SSRFError(error)
