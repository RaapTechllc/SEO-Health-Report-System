"""
Webhook Delivery Utilities.

Provides secure webhook delivery with signing, URL validation, and retries.
"""

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from packages.seo_health_report.scripts.redaction import redact_dict
from packages.seo_health_report.scripts.safe_fetch import SSRFError, resolve_dns, validate_ip


@dataclass
class WebhookResult:
    """Result of webhook delivery attempt."""
    success: bool
    attempts: int
    status_code: Optional[int] = None
    error: Optional[str] = None


def sign_webhook_payload(payload: dict, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.

    Args:
        payload: JSON-serializable payload
        secret: Signing secret

    Returns:
        Hex-encoded signature
    """
    body = json.dumps(payload, sort_keys=True, default=str)
    signature = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    )
    return signature.hexdigest()


def verify_webhook_signature(payload: dict, signature: str, secret: str) -> bool:
    """
    Verify webhook signature.

    Args:
        payload: Received payload
        signature: Received signature
        secret: Expected secret

    Returns:
        True if signature is valid
    """
    expected = sign_webhook_payload(payload, secret)
    return hmac.compare_digest(expected, signature)


async def validate_callback_url(url: str) -> None:
    """
    Validate callback URL is safe (not private IP).

    Raises:
        SSRFError: If URL points to private/internal IP
        ValueError: If URL is malformed
    """
    parsed = urlparse(url)

    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Invalid scheme: {parsed.scheme}")

    if not parsed.hostname:
        raise ValueError("Missing hostname")

    ip = resolve_dns(parsed.hostname)
    validate_ip(ip)


def calculate_backoff(attempt: int, base: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff with jitter."""
    import random
    delay = min(base * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


async def deliver_webhook(
    callback_url: str,
    payload: dict[str, Any],
    secret: str,
    max_attempts: int = 5,
    timeout: float = 10.0
) -> WebhookResult:
    """
    Deliver webhook with signing and retries.

    Args:
        callback_url: URL to POST to
        payload: JSON payload (will be redacted for sensitive data)
        secret: Signing secret
        max_attempts: Maximum delivery attempts
        timeout: Request timeout in seconds

    Returns:
        WebhookResult with success status and details
    """
    try:
        await validate_callback_url(callback_url)
    except (SSRFError, ValueError) as e:
        return WebhookResult(
            success=False,
            attempts=0,
            error=f"Invalid callback URL: {e}"
        )

    safe_payload = redact_dict(payload)

    signature = sign_webhook_payload(safe_payload, secret)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "User-Agent": "SEOHealthReport-Webhook/1.0"
    }

    last_error = None
    last_status = None

    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    callback_url,
                    json=safe_payload,
                    headers=headers
                )
                last_status = response.status_code

                if 200 <= response.status_code < 300:
                    return WebhookResult(
                        success=True,
                        attempts=attempt + 1,
                        status_code=response.status_code
                    )

                if 400 <= response.status_code < 500 and response.status_code != 429:
                    return WebhookResult(
                        success=False,
                        attempts=attempt + 1,
                        status_code=response.status_code,
                        error=f"Client error: {response.status_code}"
                    )

                last_error = f"HTTP {response.status_code}"

        except httpx.TimeoutException:
            last_error = "Timeout"
        except httpx.RequestError as e:
            last_error = f"Request error: {type(e).__name__}"
        except Exception as e:
            last_error = f"Unexpected error: {type(e).__name__}"

        if attempt < max_attempts - 1:
            await asyncio.sleep(calculate_backoff(attempt))

    return WebhookResult(
        success=False,
        attempts=max_attempts,
        status_code=last_status,
        error=last_error
    )


def build_audit_webhook_payload(
    audit_id: str,
    status: str,
    overall_score: Optional[int] = None,
    grade: Optional[str] = None,
    report_url: Optional[str] = None,
    error_message: Optional[str] = None
) -> dict[str, Any]:
    """
    Build standard webhook payload for audit completion.

    Args:
        audit_id: Audit identifier
        status: Audit status (completed, failed)
        overall_score: Overall score (0-100)
        grade: Letter grade (A-F)
        report_url: URL to download report
        error_message: Error message if failed

    Returns:
        Webhook payload dict
    """
    from datetime import datetime

    payload = {
        "event": "audit.completed" if status == "completed" else "audit.failed",
        "audit_id": audit_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if overall_score is not None:
        payload["overall_score"] = overall_score
    if grade:
        payload["grade"] = grade
    if report_url:
        payload["report_url"] = report_url
    if error_message:
        payload["error"] = error_message

    return payload
