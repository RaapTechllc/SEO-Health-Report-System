"""
Check Security

Analyze HTTPS, security headers, and SSL configuration.
"""

import socket
import ssl
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse


@dataclass
class SecurityIssue:
    """A security issue found during analysis."""
    severity: str
    category: str
    description: str
    recommendation: str = ""


# Expected security headers
SECURITY_HEADERS = {
    "strict-transport-security": {
        "name": "HSTS",
        "severity": "high",
        "description": "Enables HTTP Strict Transport Security"
    },
    "content-security-policy": {
        "name": "CSP",
        "severity": "medium",
        "description": "Prevents XSS and injection attacks"
    },
    "x-frame-options": {
        "name": "X-Frame-Options",
        "severity": "medium",
        "description": "Prevents clickjacking"
    },
    "x-content-type-options": {
        "name": "X-Content-Type-Options",
        "severity": "low",
        "description": "Prevents MIME type sniffing"
    },
    "referrer-policy": {
        "name": "Referrer-Policy",
        "severity": "low",
        "description": "Controls referrer information"
    },
    "permissions-policy": {
        "name": "Permissions-Policy",
        "severity": "low",
        "description": "Controls browser features"
    }
}


def check_https(url: str) -> dict[str, Any]:
    """
    Check HTTPS implementation.

    Args:
        url: URL to check

    Returns:
        Dict with HTTPS analysis
    """
    result = {
        "uses_https": False,
        "redirects_to_https": False,
        "ssl_valid": False,
        "ssl_expiry": None,
        "ssl_issuer": None,
        "issues": [],
        "findings": []
    }

    parsed = urlparse(url)

    # Check if URL is HTTPS
    if parsed.scheme == "https":
        result["uses_https"] = True
        result["findings"].append("Site uses HTTPS")
    else:
        result["issues"].append({
            "severity": "critical",
            "category": "https",
            "description": "Site does not use HTTPS",
            "recommendation": "Implement HTTPS with a valid SSL certificate"
        })
        result["findings"].append("Site does not use HTTPS")

    # Check HTTP -> HTTPS redirect
    if parsed.scheme == "http":
        try:
            import requests

            http_url = url
            response = requests.head(http_url, allow_redirects=False, timeout=10)

            if response.status_code in [301, 302, 307, 308]:
                location = response.headers.get("Location", "")
                if location.startswith("https://"):
                    result["redirects_to_https"] = True
                    result["findings"].append("HTTP redirects to HTTPS")
        except Exception:
            pass
    elif parsed.scheme == "https":
        # Check if HTTP version redirects
        http_url = url.replace("https://", "http://")
        try:
            import requests

            response = requests.head(http_url, allow_redirects=False, timeout=10)

            if response.status_code in [301, 302, 307, 308]:
                location = response.headers.get("Location", "")
                if location.startswith("https://"):
                    result["redirects_to_https"] = True
                    result["findings"].append("HTTP redirects to HTTPS")
                else:
                    result["issues"].append({
                        "severity": "high",
                        "category": "https",
                        "description": "HTTP does not redirect to HTTPS",
                        "recommendation": "Configure server to redirect all HTTP traffic to HTTPS"
                    })
        except Exception:
            pass

    # Check SSL certificate
    if result["uses_https"] or parsed.scheme == "https":
        hostname = parsed.netloc
        if ":" in hostname:
            hostname = hostname.split(":")[0]

        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    result["ssl_valid"] = True

                    # Get expiry date
                    not_after = cert.get("notAfter")
                    if not_after:
                        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        result["ssl_expiry"] = expiry.isoformat()

                        days_until_expiry = (expiry - datetime.now()).days
                        if days_until_expiry < 0:
                            result["ssl_valid"] = False
                            result["issues"].append({
                                "severity": "critical",
                                "category": "ssl",
                                "description": "SSL certificate has expired",
                                "recommendation": "Renew SSL certificate immediately"
                            })
                        elif days_until_expiry < 30:
                            result["issues"].append({
                                "severity": "high",
                                "category": "ssl",
                                "description": f"SSL certificate expires in {days_until_expiry} days",
                                "recommendation": "Renew SSL certificate before expiry"
                            })
                        elif days_until_expiry < 90:
                            result["issues"].append({
                                "severity": "low",
                                "category": "ssl",
                                "description": f"SSL certificate expires in {days_until_expiry} days",
                                "recommendation": "Plan SSL certificate renewal"
                            })

                        result["findings"].append(f"SSL certificate valid until {expiry.strftime('%Y-%m-%d')}")

                    # Get issuer
                    issuer = cert.get("issuer")
                    if issuer:
                        issuer_dict = dict(x[0] for x in issuer)
                        result["ssl_issuer"] = issuer_dict.get("organizationName", "Unknown")
                        result["findings"].append(f"SSL issued by: {result['ssl_issuer']}")

        except ssl.SSLError as e:
            result["ssl_valid"] = False
            result["issues"].append({
                "severity": "critical",
                "category": "ssl",
                "description": f"SSL error: {str(e)}",
                "recommendation": "Fix SSL certificate configuration"
            })
        except socket.timeout:
            result["issues"].append({
                "severity": "medium",
                "category": "ssl",
                "description": "Timeout checking SSL certificate",
                "recommendation": "Verify server is responding properly"
            })
        except Exception as e:
            result["issues"].append({
                "severity": "medium",
                "category": "ssl",
                "description": f"Could not check SSL: {str(e)}"
            })

    return result


def analyze_security_headers(url: str) -> dict[str, Any]:
    """
    Analyze security headers.

    Args:
        url: URL to check

    Returns:
        Dict with security header analysis
    """
    result = {
        "headers_found": {},
        "headers_missing": [],
        "issues": [],
        "findings": [],
        "score": 0
    }

    try:
        import requests

        headers = {
            'User-Agent': 'SEO-Health-Report-Bot/1.0 (Security Audit)'
        }

        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        response_headers = {k.lower(): v for k, v in response.headers.items()}

        # Check each expected security header
        for header_key, header_info in SECURITY_HEADERS.items():
            if header_key in response_headers:
                result["headers_found"][header_info["name"]] = response_headers[header_key]
                result["findings"].append(f"{header_info['name']} header present")
            else:
                result["headers_missing"].append(header_info["name"])
                result["issues"].append({
                    "severity": header_info["severity"],
                    "category": "headers",
                    "description": f"Missing {header_info['name']} header - {header_info['description']}",
                    "recommendation": f"Add {header_key} header to server configuration"
                })

        # Check HSTS specifically
        hsts = response_headers.get("strict-transport-security", "")
        if hsts:
            if "max-age=" in hsts:
                max_age_match = hsts.split("max-age=")[1].split(";")[0]
                try:
                    max_age = int(max_age_match)
                    if max_age < 31536000:  # Less than 1 year
                        result["issues"].append({
                            "severity": "low",
                            "category": "headers",
                            "description": f"HSTS max-age is short ({max_age} seconds)",
                            "recommendation": "Increase HSTS max-age to at least 31536000 (1 year)"
                        })
                except ValueError:
                    pass

            if "includeSubDomains" in hsts:
                result["findings"].append("HSTS includes subdomains")

            if "preload" in hsts:
                result["findings"].append("HSTS preload enabled")

        # Calculate score
        total_headers = len(SECURITY_HEADERS)
        found_headers = len(result["headers_found"])
        result["score"] = int((found_headers / total_headers) * 10)

    except ImportError:
        result["issues"].append({
            "severity": "low",
            "category": "headers",
            "description": "requests package not installed - header check skipped"
        })
    except Exception as e:
        result["issues"].append({
            "severity": "low",
            "category": "headers",
            "description": f"Error checking headers: {str(e)}"
        })

    return result


def check_mixed_content(url: str) -> dict[str, Any]:
    """
    Check for mixed content issues (HTTP resources on HTTPS page).

    Args:
        url: URL to check

    Returns:
        Dict with mixed content analysis
    """
    result = {
        "has_mixed_content": False,
        "mixed_resources": [],
        "issues": [],
        "findings": []
    }

    parsed = urlparse(url)
    if parsed.scheme != "https":
        result["findings"].append("Site not using HTTPS - mixed content check not applicable")
        return result

    try:
        import re

        import requests

        headers = {
            'User-Agent': 'SEO-Health-Report-Bot/1.0 (Security Audit)'
        }

        response = requests.get(url, headers=headers, timeout=30)
        html = response.text

        # Find all HTTP resources
        http_patterns = [
            (r'src=["\']http://[^"\']+["\']', 'src'),
            (r'href=["\']http://[^"\']+\.(?:css|js)["\']', 'href'),
            (r'url\(["\']?http://[^"\')\s]+["\']?\)', 'url()'),
        ]

        for pattern, resource_type in http_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                # Extract URL from match
                url_match = re.search(r'http://[^\s"\')\]]+', match)
                if url_match:
                    resource_url = url_match.group()
                    result["mixed_resources"].append({
                        "url": resource_url,
                        "type": resource_type
                    })

        if result["mixed_resources"]:
            result["has_mixed_content"] = True
            result["issues"].append({
                "severity": "high",
                "category": "mixed_content",
                "description": f"Found {len(result['mixed_resources'])} HTTP resources on HTTPS page",
                "recommendation": "Update all resources to use HTTPS"
            })
            result["findings"].append(f"Mixed content warning: {len(result['mixed_resources'])} HTTP resources found")
        else:
            result["findings"].append("No mixed content detected")

    except ImportError:
        result["issues"].append({
            "severity": "low",
            "category": "mixed_content",
            "description": "requests package not installed - mixed content check skipped"
        })
    except Exception as e:
        result["issues"].append({
            "severity": "low",
            "category": "mixed_content",
            "description": f"Error checking mixed content: {str(e)}"
        })

    return result


def analyze_security(url: str) -> dict[str, Any]:
    """
    Complete security analysis for a URL.

    Args:
        url: URL to analyze

    Returns:
        Dict with complete security analysis (0-10 score)
    """
    result = {
        "score": 0,
        "max": 10,
        "https": {},
        "headers": {},
        "mixed_content": {},
        "issues": [],
        "findings": []
    }

    # Check HTTPS
    https_result = check_https(url)
    result["https"] = https_result
    result["issues"].extend(https_result.get("issues", []))
    result["findings"].extend(https_result.get("findings", []))

    # Check security headers
    headers_result = analyze_security_headers(url)
    result["headers"] = headers_result
    result["issues"].extend(headers_result.get("issues", []))
    result["findings"].extend(headers_result.get("findings", []))

    # Check mixed content
    mixed_result = check_mixed_content(url)
    result["mixed_content"] = mixed_result
    result["issues"].extend(mixed_result.get("issues", []))
    result["findings"].extend(mixed_result.get("findings", []))

    # Calculate total score (0-10)
    score = 10

    # HTTPS is critical (0-4 points)
    if not https_result.get("uses_https"):
        score -= 4
    elif not https_result.get("ssl_valid"):
        score -= 3

    # Headers (0-4 points based on header score)
    headers_score = headers_result.get("score", 0)
    score -= (10 - headers_score) * 0.4

    # Mixed content (0-2 points)
    if mixed_result.get("has_mixed_content"):
        score -= 2

    result["score"] = max(0, round(score))

    return result


__all__ = [
    'SecurityIssue',
    'SECURITY_HEADERS',
    'check_https',
    'analyze_security_headers',
    'check_mixed_content',
    'analyze_security'
]
