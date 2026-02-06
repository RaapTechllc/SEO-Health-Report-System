"""SSRF-protected HTTP client for safe external URL fetching."""

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

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


@dataclass
class FetchResult:
    url: str
    status_code: int
    content: bytes
    headers: dict[str, str]
    final_url: str


class SSRFError(Exception):
    """Raised when SSRF protection blocks a request."""

    pass


def validate_ip(ip: str) -> None:
    """Validate that an IP address is not in blocked ranges.

    Args:
        ip: IP address string to validate.

    Raises:
        SSRFError: If the IP is in a blocked range.
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError as e:
        raise SSRFError(f"Invalid IP address: {ip}") from e

    for blocked in BLOCKED_RANGES:
        if ip_obj in blocked:
            raise SSRFError(f"IP address {ip} is in blocked range {blocked}")


def resolve_dns(hostname: str) -> str:
    """Resolve hostname to IP address and validate it.

    Args:
        hostname: The hostname to resolve.

    Returns:
        The first resolved IP address.

    Raises:
        SSRFError: If DNS resolution fails or IP is blocked.
    """
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not results:
            raise SSRFError(f"DNS resolution failed for {hostname}: no results")
        ip = results[0][4][0]
        validate_ip(ip)
        return ip
    except socket.gaierror as e:
        raise SSRFError(f"DNS resolution failed for {hostname}: {e}") from e


def _validate_url(url: str) -> None:
    """Validate URL scheme and credentials.

    Args:
        url: The URL to validate.

    Raises:
        SSRFError: If URL has invalid scheme or contains credentials.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise SSRFError(f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed.")

    if parsed.username or parsed.password:
        raise SSRFError("URLs with credentials (user:pass) are not allowed")

    if not parsed.hostname:
        raise SSRFError("URL must have a hostname")


async def safe_fetch(
    url: str,
    timeout: float = 30.0,
    max_bytes: int = 10 * 1024 * 1024,
    max_redirects: int = 5,
    user_agent: str = "SEO-Health-Report/1.0",
) -> FetchResult:
    """Fetch a URL with SSRF protection.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        max_bytes: Maximum response size in bytes.
        max_redirects: Maximum number of redirects to follow.
        user_agent: User-Agent header value.

    Returns:
        FetchResult with response data.

    Raises:
        SSRFError: If the request is blocked by SSRF protection.
        httpx.HTTPError: If the request fails.
    """
    current_url = url
    redirect_count = 0

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        follow_redirects=False,
    ) as client:
        while True:
            _validate_url(current_url)

            parsed = urlparse(current_url)
            hostname = parsed.hostname
            if not hostname:
                raise SSRFError("URL must have a hostname")

            resolve_dns(hostname)

            response = await client.get(
                current_url,
                headers={"User-Agent": user_agent},
            )

            if response.status_code in (301, 302, 303, 307, 308):
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise SSRFError(f"Too many redirects (max {max_redirects})")

                location = response.headers.get("location")
                if not location:
                    raise SSRFError("Redirect response missing Location header")

                if location.startswith("/"):
                    current_url = f"{parsed.scheme}://{parsed.netloc}{location}"
                else:
                    current_url = location
                continue

            content = response.content
            if len(content) > max_bytes:
                raise SSRFError(f"Response size {len(content)} exceeds limit {max_bytes}")

            return FetchResult(
                url=url,
                status_code=response.status_code,
                content=content,
                headers=dict(response.headers),
                final_url=str(response.url),
            )
