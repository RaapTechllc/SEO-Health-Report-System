"""
Sensitive Data Redaction Utility

Provides utilities to strip secrets from strings before logging/storage.
"""

import re

REDACTION_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)(api[_-]?key|token|secret|password|auth)['\"]?\s*[:=]\s*['\"]?[\w\-\.]+", "[REDACTED]"),
    (r"(?i)authorization:\s*bearer\s+[\w\-\.]+", "Authorization: Bearer [REDACTED]"),
    (r"(?i)cookie:\s*.+", "Cookie: [REDACTED]"),
    (r"(?i)set-cookie:\s*.+", "Set-Cookie: [REDACTED]"),
]

SENSITIVE_KEYS = {"api_key", "token", "secret", "password", "authorization", "cookie", "api-key"}


def redact_sensitive(text: str) -> str:
    """Remove secrets from text before logging/storing.

    Args:
        text: Input string that may contain sensitive data.

    Returns:
        String with sensitive patterns replaced by [REDACTED].
    """
    if not isinstance(text, str):
        return text

    result = text
    for pattern, replacement in REDACTION_PATTERNS:
        result = re.sub(pattern, replacement, result)

    return result


def redact_dict(data: dict) -> dict:
    """Recursively redact sensitive values in nested dict.

    Args:
        data: Dictionary that may contain sensitive values.

    Returns:
        New dictionary with sensitive values redacted.
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        normalized_key = str(key).lower().replace("-", "_")

        if normalized_key in SENSITIVE_KEYS or any(sk in normalized_key for sk in SENSITIVE_KEYS):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, list):
            result[key] = [
                redact_dict(item) if isinstance(item, dict) else redact_sensitive(item) if isinstance(item, str) else item
                for item in value
            ]
        elif isinstance(value, str):
            result[key] = redact_sensitive(value)
        else:
            result[key] = value

    return result
