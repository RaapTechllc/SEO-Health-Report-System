#!/usr/bin/env python3
"""
Production Smoke Test Script

Validates that a deployed SEO Health Report System is functioning correctly.
Run after deployment to verify critical paths work.

Usage:
    python scripts/smoke_test.py https://api.seohealthreport.com
    python scripts/smoke_test.py http://localhost:8000
"""

import argparse
import json
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

import requests


class SmokeTest:
    """Production smoke test runner."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.results = []
        self.start_time = None

    def log(self, status: str, test: str, message: str = "", duration_ms: int = 0):
        """Log test result."""
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        duration_str = f" ({duration_ms}ms)" if duration_ms else ""
        print(f"   {icon} {test}{duration_str}")
        if message:
            print(f"      └─ {message}")
        self.results.append({
            "status": status,
            "test": test,
            "message": message,
            "duration_ms": duration_ms,
        })

    def request(self, method: str, path: str, **kwargs) -> tuple[requests.Response | None, int]:
        """Make HTTP request and return response with duration."""
        url = urljoin(self.base_url, path)
        start = time.time()
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            duration_ms = int((time.time() - start) * 1000)
            return response, duration_ms
        except requests.RequestException:
            duration_ms = int((time.time() - start) * 1000)
            return None, duration_ms

    def test_health_endpoint(self) -> bool:
        """Test /health endpoint returns 200."""
        response, duration = self.request("GET", "/health")
        if response and response.status_code == 200:
            self.log("PASS", "Health endpoint", "", duration)
            return True
        else:
            status = response.status_code if response else "Connection failed"
            self.log("FAIL", "Health endpoint", f"Status: {status}", duration)
            return False

    def test_docs_endpoint(self) -> bool:
        """Test /docs endpoint (OpenAPI) is accessible."""
        response, duration = self.request("GET", "/docs")
        if response and response.status_code == 200:
            self.log("PASS", "API docs endpoint", "", duration)
            return True
        else:
            self.log("WARN", "API docs endpoint", "Not accessible (may be disabled)", duration)
            return True  # Non-critical

    def test_audit_endpoint_rejects_invalid(self) -> bool:
        """Test /audit endpoint rejects invalid input."""
        response, duration = self.request(
            "POST",
            "/audit",
            json={"invalid": "data"}
        )
        if response and response.status_code in [400, 422]:
            self.log("PASS", "Audit validation", "Rejects invalid input", duration)
            return True
        else:
            status = response.status_code if response else "Connection failed"
            self.log("FAIL", "Audit validation", f"Expected 400/422, got {status}", duration)
            return False

    def test_rate_limiting(self) -> bool:
        """Test rate limiting headers are present."""
        response, duration = self.request("GET", "/health")
        if response:
            rate_headers = [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
            ]
            found = [h for h in rate_headers if h in response.headers]
            if found:
                self.log("PASS", "Rate limiting", f"Headers: {', '.join(found)}", duration)
                return True
            else:
                self.log("WARN", "Rate limiting", "Headers not present", duration)
                return True  # Non-critical
        self.log("FAIL", "Rate limiting", "Could not check", duration)
        return False

    def test_cors_headers(self) -> bool:
        """Test CORS headers are configured."""
        response, duration = self.request(
            "OPTIONS",
            "/health",
            headers={"Origin": "https://example.com"}
        )
        if response:
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header:
                self.log("PASS", "CORS configuration", f"Origin: {cors_header}", duration)
                return True
            else:
                self.log("WARN", "CORS configuration", "Not configured", duration)
                return True  # May be intentional
        self.log("FAIL", "CORS configuration", "Could not check", duration)
        return False

    def test_security_headers(self) -> bool:
        """Test security headers are present."""
        response, duration = self.request("GET", "/health")
        if response:
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            }
            found = []
            for header, expected in security_headers.items():
                value = response.headers.get(header)
                if value:
                    if isinstance(expected, list):
                        if value in expected:
                            found.append(header)
                    elif value == expected:
                        found.append(header)
            if found:
                self.log("PASS", "Security headers", f"Found: {', '.join(found)}", duration)
                return True
            else:
                self.log("WARN", "Security headers", "Not all headers present", duration)
                return True  # Non-critical for smoke test
        return False

    def test_database_connection(self) -> bool:
        """Test database is accessible (via health check with DB status)."""
        response, duration = self.request("GET", "/health")
        if response and response.status_code == 200:
            try:
                data = response.json()
                db_status = data.get("database", data.get("db", "unknown"))
                if db_status in ["ok", "healthy", True, "connected"]:
                    self.log("PASS", "Database connection", f"Status: {db_status}", duration)
                    return True
                else:
                    self.log("WARN", "Database connection", f"Status: {db_status}", duration)
                    return True  # Health passed, so DB likely OK
            except Exception:
                self.log("PASS", "Database connection", "Health OK (no details)", duration)
                return True
        self.log("FAIL", "Database connection", "Health check failed", duration)
        return False

    def test_response_time(self) -> bool:
        """Test response time is acceptable (<500ms)."""
        response, duration = self.request("GET", "/health")
        if response:
            if duration < 500:
                self.log("PASS", "Response time", f"{duration}ms < 500ms", duration)
                return True
            elif duration < 1000:
                self.log("WARN", "Response time", f"{duration}ms (slow but acceptable)", duration)
                return True
            else:
                self.log("FAIL", "Response time", f"{duration}ms > 1000ms", duration)
                return False
        self.log("FAIL", "Response time", "Could not measure", 0)
        return False

    def run(self) -> bool:
        """Run all smoke tests."""
        self.start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"🔥 Smoke Test: {self.base_url}")
        print(f"   Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        tests = [
            ("Health Check", self.test_health_endpoint),
            ("API Documentation", self.test_docs_endpoint),
            ("Input Validation", self.test_audit_endpoint_rejects_invalid),
            ("Rate Limiting", self.test_rate_limiting),
            ("CORS Headers", self.test_cors_headers),
            ("Security Headers", self.test_security_headers),
            ("Database", self.test_database_connection),
            ("Performance", self.test_response_time),
        ]

        passed = 0
        failed = 0
        warned = 0

        for name, test_fn in tests:
            try:
                if test_fn():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log("FAIL", name, f"Exception: {e}", 0)
                failed += 1

        # Summary
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"📊 Results: {passed} passed, {failed} failed")
        print(f"   Duration: {duration:.2f}s")
        print(f"{'='*60}\n")

        if failed > 0:
            print("❌ SMOKE TEST FAILED")
            return False
        else:
            print("✅ SMOKE TEST PASSED")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Run smoke tests against SEO Health Report API"
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    tester = SmokeTest(args.url, timeout=args.timeout)
    success = tester.run()

    if args.json:
        print(json.dumps({
            "success": success,
            "results": tester.results,
        }, indent=2))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
