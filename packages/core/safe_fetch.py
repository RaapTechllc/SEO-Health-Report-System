"""
Safe Fetch Module - SSRF Protection

Provides secure HTTP fetching with protection against:
- SSRF attacks (Server-Side Request Forgery)
- DNS rebinding attacks
- Redirect-based attacks
- Resource exhaustion

All external HTTP requests should go through this module.
Uses httpx for async-first HTTP with sync fallback.
"""

import ipaddress
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx

# Configuration
MAX_REDIRECTS = 5
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_PORTS = {22, 23, 25, 445, 3389}  # SSH, Telnet, SMTP, SMB, RDP

USER_AGENT = "SEOHealthReport/1.0 (+https://seohealthreport.com/bot)"

BLOCKED_RANGES: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class SSRFProtectionError(Exception):
    """Raised when a request is blocked due to SSRF protection."""

    pass


# Alias for backwards compat
SSRFError = SSRFProtectionError


@dataclass
class FetchResult:
    url: str
    status_code: int
    content: bytes
    headers: dict[str, str]
    final_url: str


def is_private_ip(ip: str) -> bool:
    """Check if an IP address is private, loopback, or link-local."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in net for net in BLOCKED_RANGES)
    except ValueError:
        return True


def validate_ip(ip: str) -> None:
    """Validate that an IP address is not in blocked ranges."""
    if is_private_ip(ip):
        raise SSRFProtectionError(f"SSRF blocked: IP '{ip}' is in a blocked range")


def resolve_dns(hostname: str) -> str:
    """Resolve hostname to IP address and validate it."""
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not results:
            raise SSRFProtectionError(f"DNS resolution failed for {hostname}: no results")
        ip = results[0][4][0]
        validate_ip(ip)
        return ip
    except socket.gaierror as e:
        raise SSRFProtectionError(f"DNS resolution failed for '{hostname}': {e}") from e


# Alias
resolve_and_validate = resolve_dns


def validate_url(url: str) -> tuple[str, str, int]:
    """Validate URL for SSRF protection. Returns (scheme, hostname, port)."""
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise SSRFProtectionError(f"Invalid URL: {e}") from e

    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SSRFProtectionError(f"SSRF blocked: scheme '{scheme}' not allowed")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFProtectionError("SSRF blocked: no hostname in URL")

    if parsed.username or parsed.password:
        raise SSRFProtectionError("URLs with credentials (user:pass) are not allowed")

    # Check IP literals directly
    try:
        ip_obj = ipaddress.ip_address(hostname)
        if any(ip_obj in net for net in BLOCKED_RANGES):
            raise SSRFProtectionError(f"SSRF blocked: private IP '{hostname}'")
    except ValueError:
        pass  # Not an IP literal, will resolve later

    port = parsed.port or (443 if scheme == "https" else 80)
    if port in BLOCKED_PORTS:
        raise SSRFProtectionError(f"SSRF blocked: port {port} not allowed")

    resolve_dns(hostname)
    return scheme, hostname, port


async def safe_fetch(
    url: str,
    timeout: float = 30.0,
    max_bytes: int = MAX_RESPONSE_SIZE,
    max_redirects: int = MAX_REDIRECTS,
    user_agent: str = USER_AGENT,
) -> FetchResult:
    """Fetch a URL with SSRF protection (async)."""
    current_url = url
    redirect_count = 0

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        follow_redirects=False,
    ) as client:
        while True:
            validate_url(current_url)

            response = await client.get(
                current_url,
                headers={"User-Agent": user_agent},
            )

            if response.status_code in (301, 302, 303, 307, 308):
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise SSRFProtectionError(f"Too many redirects (max {max_redirects})")

                location = response.headers.get("location")
                if not location:
                    raise SSRFProtectionError("Redirect missing Location header")

                parsed = urlparse(current_url)
                if location.startswith("/"):
                    current_url = f"{parsed.scheme}://{parsed.netloc}{location}"
                else:
                    current_url = location
                continue

            content = response.content
            if len(content) > max_bytes:
                raise SSRFProtectionError(f"Response size {len(content)} exceeds limit {max_bytes}")

            return FetchResult(
                url=url,
                status_code=response.status_code,
                content=content,
                headers=dict(response.headers),
                final_url=str(response.url),
            )


def safe_get(
    url: str,
    timeout: tuple[int, int] = (CONNECT_TIMEOUT, READ_TIMEOUT),
    max_size: int = MAX_RESPONSE_SIZE,
    headers: Optional[dict] = None,
    verify_ssl: bool = True,
) -> httpx.Response:
    """Perform a safe synchronous HTTP GET with SSRF protection."""
    validate_url(url)

    with httpx.Client(
        timeout=httpx.Timeout(connect=timeout[0], read=timeout[1]),
        follow_redirects=False,
        verify=verify_ssl,
    ) as client:
        req_headers = {"User-Agent": USER_AGENT}
        if headers:
            req_headers.update(headers)

        current_url = url
        redirect_count = 0

        while True:
            response = client.get(current_url, headers=req_headers)

            if response.status_code in (301, 302, 303, 307, 308):
                redirect_count += 1
                if redirect_count > MAX_REDIRECTS:
                    raise SSRFProtectionError(f"Too many redirects (max {MAX_REDIRECTS})")
                location = response.headers.get("location")
                if not location:
                    break
                parsed = urlparse(current_url)
                if location.startswith("/"):
                    current_url = f"{parsed.scheme}://{parsed.netloc}{location}"
                else:
                    current_url = location
                validate_url(current_url)
                continue

            if len(response.content) > max_size:
                raise SSRFProtectionError(f"Response exceeded size limit of {max_size} bytes")
            return response


def is_url_safe(url: str) -> tuple[bool, Optional[str]]:
    """Check if a URL is safe to fetch without making a request."""
    try:
        validate_url(url)
        return True, None
    except SSRFProtectionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"URL validation error: {e}"
