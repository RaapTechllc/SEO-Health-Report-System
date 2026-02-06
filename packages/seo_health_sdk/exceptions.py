"""Custom exceptions for the SEO Health SDK."""

from typing import Any, Optional


class SEOHealthError(Exception):
    """Base exception for SEO Health SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(SEOHealthError):
    """Raised when authentication fails (401)."""

    pass


class AuthorizationError(SEOHealthError):
    """Raised when authorization fails (403)."""

    pass


class NotFoundError(SEOHealthError):
    """Raised when a resource is not found (404)."""

    pass


class ValidationError(SEOHealthError):
    """Raised when request validation fails (422)."""

    pass


class RateLimitError(SEOHealthError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        status_code: int = 429,
        response_data: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response_data)
        self.retry_after = retry_after


class APIError(SEOHealthError):
    """Raised for general API errors (5xx)."""

    pass


def raise_for_status(
    status_code: int, response_data: dict[str, Any], headers: dict[str, str] = None
) -> None:
    """Raise appropriate exception based on status code."""
    headers = headers or {}
    message = response_data.get("detail", response_data.get("message", "Unknown error"))

    if status_code == 401:
        raise AuthenticationError(message, status_code, response_data)
    elif status_code == 403:
        raise AuthorizationError(message, status_code, response_data)
    elif status_code == 404:
        raise NotFoundError(message, status_code, response_data)
    elif status_code == 422:
        raise ValidationError(message, status_code, response_data)
    elif status_code == 429:
        retry_after = headers.get("Retry-After")
        retry_seconds = int(retry_after) if retry_after else None
        raise RateLimitError(message, retry_seconds, status_code, response_data)
    elif status_code >= 500:
        raise APIError(message, status_code, response_data)
    elif status_code >= 400:
        raise SEOHealthError(message, status_code, response_data)


__all__ = [
    "SEOHealthError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "APIError",
    "raise_for_status",
]
