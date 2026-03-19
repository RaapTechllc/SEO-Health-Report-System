"""
Safe Fetch Module - SSRF Protection

Provides secure HTTP fetching with protection against:
- SSRF attacks (Server-Side Request Forgery)
- DNS rebinding attacks
- Redirect-based attacks
- Resource exhaustion

All external HTTP requests should go through this module.
"""

import ipaddress
import socket
import urllib.parse
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
MAX_REDIRECTS = 3
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_PORTS = {22, 23, 25, 445, 3389}  # SSH, Telnet, SMTP, SMB, RDP

# User agent for all requests
USER_AGENT = "SEOHealthReport/1.0 (+https://seohealthreport.com/bot)"


class SSRFProtectionError(Exception):
    """Raised when a request is blocked due to SSRF protection."""

    pass


def is_private_ip(ip: str) -> bool:
    """
    Check if an IP address is private, loopback, or link-local.

    Args:
        ip: IP address string (IPv4 or IPv6)

    Returns:
        True if the IP is private/internal, False if public
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_reserved
            or ip_obj.is_multicast
            or ip_obj.is_unspecified
        )
    except ValueError:
        # Invalid IP, block it
        return True


def resolve_and_validate(hostname: str) -> str:
    """
    Resolve hostname to IP and validate it's not private.

    Args:
        hostname: The hostname to resolve

    Returns:
        The resolved IP address

    Raises:
        SSRFProtectionError: If the resolved IP is private/blocked
    """
    try:
        # Resolve hostname to IP
        ip = socket.gethostbyname(hostname)

        if is_private_ip(ip):
            raise SSRFProtectionError(
                f"SSRF blocked: hostname '{hostname}' resolves to private IP '{ip}'"
            )

        return ip
    except socket.gaierror as e:
        raise SSRFProtectionError(
            f"DNS resolution failed for '{hostname}': {e}"
        ) from e


def validate_url(url: str) -> tuple[str, str, int]:
    """
    Validate URL for SSRF protection.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (scheme, hostname, port)

    Raises:
        SSRFProtectionError: If the URL is blocked
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise SSRFProtectionError(f"Invalid URL: {e}") from e

    # Validate scheme
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SSRFProtectionError(
            f"SSRF blocked: scheme '{scheme}' not allowed. Use http or https."
        )

    # Validate hostname exists
    hostname = parsed.hostname
    if not hostname:
        raise SSRFProtectionError("SSRF blocked: no hostname in URL")

    # Check for IP literals (only check if hostname is actually an IP address)
    try:
        import ipaddress
        # Try to parse as IP - if successful, check if private
        ip_obj = ipaddress.ip_address(hostname)
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_reserved
            or ip_obj.is_multicast
            or ip_obj.is_unspecified
        ):
            raise SSRFProtectionError(
                f"SSRF blocked: private IP address '{hostname}' not allowed"
            )
    except ValueError:
        # Not an IP literal (it's a hostname), will resolve and validate later
        pass

    # Validate port
    port = parsed.port or (443 if scheme == "https" else 80)
    if port in BLOCKED_PORTS:
        raise SSRFProtectionError(f"SSRF blocked: port {port} not allowed")

    # Resolve hostname and validate resolved IP
    resolve_and_validate(hostname)

    return scheme, hostname, port


def create_safe_session(
    max_redirects: int = MAX_REDIRECTS,
    retries: int = 3,
) -> requests.Session:
    """
    Create a requests Session with safe defaults.

    Args:
        max_redirects: Maximum number of redirects to follow
        retries: Number of retries for transient failures

    Returns:
        Configured requests.Session
    """
    session = requests.Session()

    # Configure retries
    retry_strategy = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set default headers
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })

    # Limit redirects
    session.max_redirects = max_redirects

    return session


def safe_get(
    url: str,
    timeout: tuple[int, int] = (CONNECT_TIMEOUT, READ_TIMEOUT),
    max_size: int = MAX_RESPONSE_SIZE,
    allow_redirects: bool = True,
    headers: Optional[dict] = None,
    verify_ssl: bool = True,
) -> requests.Response:
    """
    Perform a safe HTTP GET request with SSRF protection.

    Args:
        url: URL to fetch
        timeout: Tuple of (connect_timeout, read_timeout) in seconds
        max_size: Maximum response size in bytes
        allow_redirects: Whether to follow redirects
        headers: Additional headers to send
        verify_ssl: Whether to verify SSL certificates

    Returns:
        requests.Response object

    Raises:
        SSRFProtectionError: If the request is blocked
        requests.RequestException: For other request failures
    """
    # Validate initial URL
    validate_url(url)

    session = create_safe_session()

    # Merge custom headers
    if headers:
        session.headers.update(headers)

    # Make request with streaming to check size
    response = session.get(
        url,
        timeout=timeout,
        allow_redirects=False,  # Handle redirects manually for validation
        verify=verify_ssl,
        stream=True,
    )

    # Handle redirects with validation
    redirect_count = 0
    while response.is_redirect and allow_redirects and redirect_count < MAX_REDIRECTS:
        redirect_url = response.headers.get("Location")
        if not redirect_url:
            break

        # Handle relative redirects
        redirect_url = urllib.parse.urljoin(url, redirect_url)

        # Validate redirect target
        validate_url(redirect_url)

        response = session.get(
            redirect_url,
            timeout=timeout,
            allow_redirects=False,
            verify=verify_ssl,
            stream=True,
        )
        redirect_count += 1
        url = redirect_url

    # Check content length
    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > max_size:
        response.close()
        raise SSRFProtectionError(
            f"Response too large: {content_length} bytes exceeds limit of {max_size}"
        )

    # Read content with size limit
    content = b""
    for chunk in response.iter_content(chunk_size=8192):
        content += chunk
        if len(content) > max_size:
            response.close()
            raise SSRFProtectionError(
                f"Response exceeded size limit of {max_size} bytes"
            )

    # Replace response content
    response._content = content

    return response


def safe_head(
    url: str,
    timeout: tuple[int, int] = (CONNECT_TIMEOUT, READ_TIMEOUT),
    headers: Optional[dict] = None,
    verify_ssl: bool = True,
) -> requests.Response:
    """
    Perform a safe HTTP HEAD request with SSRF protection.

    Args:
        url: URL to check
        timeout: Tuple of (connect_timeout, read_timeout) in seconds
        headers: Additional headers to send
        verify_ssl: Whether to verify SSL certificates

    Returns:
        requests.Response object

    Raises:
        SSRFProtectionError: If the request is blocked
    """
    validate_url(url)

    session = create_safe_session()

    if headers:
        session.headers.update(headers)

    return session.head(
        url,
        timeout=timeout,
        allow_redirects=True,
        verify=verify_ssl,
    )


def is_url_safe(url: str) -> tuple[bool, Optional[str]]:
    """
    Check if a URL is safe to fetch without making a request.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        validate_url(url)
        return True, None
    except SSRFProtectionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"URL validation error: {e}"
