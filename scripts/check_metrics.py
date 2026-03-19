#!/usr/bin/env python3
"""
Post-deployment metrics checker.

Fetches and analyzes metrics from the /metrics endpoint to detect issues.

Usage:
    python scripts/check_metrics.py --url https://api.example.com
    python scripts/check_metrics.py --url https://api.example.com --error-threshold 3
    python scripts/check_metrics.py --url https://api.example.com --json
    python scripts/check_metrics.py --url https://api.example.com --alert
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MetricsSummary:
    """Summary of collected metrics."""

    timestamp: str
    url: str
    healthy: bool
    total_requests: int
    error_requests: int
    error_rate: float
    error_rate_threshold: float
    error_rate_ok: bool
    active_audits: int
    audit_completed: int
    audit_failed: int
    webhook_delivered: int
    webhook_failed: int
    issues: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_url(url: str, timeout: int = 10) -> tuple[str, int]:
    """Fetch URL content with error handling."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PostDeployMonitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8"), response.status
    except urllib.error.HTTPError as e:
        return "", e.code
    except urllib.error.URLError:
        return "", 0
    except Exception:
        return "", 0


def parse_prometheus_metrics(content: str) -> dict[str, dict[str, float]]:
    """Parse Prometheus format metrics into a dictionary."""
    metrics: dict[str, dict[str, float]] = {}

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse metric line: name{labels} value or name value
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)(\{[^}]*\})?\s+([0-9.eE+-]+)$", line)
        if match:
            name = match.group(1)
            labels = match.group(2) or ""
            value = float(match.group(3))

            if name not in metrics:
                metrics[name] = {}

            metrics[name][labels] = value

    return metrics


def extract_label_value(labels: str, key: str) -> Optional[str]:
    """Extract a label value from Prometheus label string."""
    match = re.search(rf'{key}="([^"]*)"', labels)
    return match.group(1) if match else None


def check_health(base_url: str) -> tuple[bool, str]:
    """Check health endpoint."""
    content, status = fetch_url(f"{base_url}/health")
    if status != 200:
        return False, f"Health check returned status {status}"

    try:
        data = json.loads(content)
        if data.get("status") == "healthy":
            return True, "Healthy"
        return False, f"Health status: {data.get('status', 'unknown')}"
    except json.JSONDecodeError:
        return False, "Invalid health response"


def analyze_metrics(base_url: str, error_threshold: float = 5.0) -> MetricsSummary:
    """Analyze metrics and generate summary."""
    issues: list[str] = []

    # Check health first
    healthy, health_msg = check_health(base_url)
    if not healthy:
        issues.append(f"Health check failed: {health_msg}")

    # Fetch metrics
    content, status = fetch_url(f"{base_url}/metrics")
    if status != 200:
        issues.append(f"Metrics endpoint returned status {status}")
        return MetricsSummary(
            timestamp=datetime.utcnow().isoformat() + "Z",
            url=base_url,
            healthy=healthy,
            total_requests=0,
            error_requests=0,
            error_rate=0.0,
            error_rate_threshold=error_threshold,
            error_rate_ok=False,
            active_audits=0,
            audit_completed=0,
            audit_failed=0,
            webhook_delivered=0,
            webhook_failed=0,
            issues=issues,
        )

    metrics = parse_prometheus_metrics(content)

    # Calculate HTTP request stats
    total_requests = 0
    error_requests = 0

    http_requests = metrics.get("http_requests_total", {})
    for labels, count in http_requests.items():
        total_requests += int(count)
        status = extract_label_value(labels, "status")
        if status and status.startswith("5"):
            error_requests += int(count)

    error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0.0
    error_rate_ok = error_rate <= error_threshold

    if not error_rate_ok:
        issues.append(f"Error rate {error_rate:.2f}% exceeds threshold {error_threshold}%")

    # Get active audits
    active_audits = 0
    for _labels, value in metrics.get("active_audits", {}).items():
        active_audits += int(value)

    # Get audit counts
    audit_completed = 0
    audit_failed = 0
    audit_total = metrics.get("audit_total", {})
    for labels, count in audit_total.items():
        status = extract_label_value(labels, "status")
        if status == "completed":
            audit_completed += int(count)
        elif status == "failed":
            audit_failed += int(count)

    # Check audit failure rate
    total_audits = audit_completed + audit_failed
    if total_audits > 10:
        audit_fail_rate = audit_failed / total_audits * 100
        if audit_fail_rate > 20:
            issues.append(f"Audit failure rate {audit_fail_rate:.1f}% is high")

    # Get webhook counts
    webhook_delivered = 0
    webhook_failed = 0
    webhook_total = metrics.get("webhook_deliveries_total", {})
    for labels, count in webhook_total.items():
        status = extract_label_value(labels, "status")
        if status == "delivered":
            webhook_delivered += int(count)
        elif status == "failed":
            webhook_failed += int(count)

    return MetricsSummary(
        timestamp=datetime.utcnow().isoformat() + "Z",
        url=base_url,
        healthy=healthy,
        total_requests=total_requests,
        error_requests=error_requests,
        error_rate=round(error_rate, 2),
        error_rate_threshold=error_threshold,
        error_rate_ok=error_rate_ok,
        active_audits=active_audits,
        audit_completed=audit_completed,
        audit_failed=audit_failed,
        webhook_delivered=webhook_delivered,
        webhook_failed=webhook_failed,
        issues=issues,
    )


def send_slack_alert(webhook_url: str, summary: MetricsSummary) -> bool:
    """Send alert to Slack."""
    color = "#00ff00" if not summary.issues else "#ff0000"
    status = "✅ Healthy" if not summary.issues else "❌ Issues Detected"

    fields = [
        {"title": "Status", "value": status, "short": True},
        {"title": "Error Rate", "value": f"{summary.error_rate:.2f}%", "short": True},
        {"title": "Total Requests", "value": str(summary.total_requests), "short": True},
        {"title": "Active Audits", "value": str(summary.active_audits), "short": True},
    ]

    if summary.issues:
        fields.append({
            "title": "Issues",
            "value": "\n".join(f"• {issue}" for issue in summary.issues),
            "short": False,
        })

    payload = {
        "attachments": [{
            "color": color,
            "title": "Post-Deploy Metrics Check",
            "title_link": summary.url,
            "fields": fields,
            "footer": "Post-Deploy Monitor",
            "ts": int(datetime.utcnow().timestamp()),
        }]
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception:
        return False


def send_discord_alert(webhook_url: str, summary: MetricsSummary) -> bool:
    """Send alert to Discord."""
    color = 65280 if not summary.issues else 16711680
    status = "✅ Healthy" if not summary.issues else "❌ Issues Detected"

    fields = [
        {"name": "Status", "value": status, "inline": True},
        {"name": "Error Rate", "value": f"{summary.error_rate:.2f}%", "inline": True},
        {"name": "Total Requests", "value": str(summary.total_requests), "inline": True},
        {"name": "Active Audits", "value": str(summary.active_audits), "inline": True},
    ]

    if summary.issues:
        fields.append({
            "name": "Issues",
            "value": "\n".join(f"• {issue}" for issue in summary.issues),
            "inline": False,
        })

    payload = {
        "embeds": [{
            "title": "Post-Deploy Metrics Check",
            "url": summary.url,
            "color": color,
            "fields": fields,
            "footer": {"text": "Post-Deploy Monitor"},
            "timestamp": summary.timestamp,
        }]
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status in (200, 204)
    except Exception:
        return False


def print_summary(summary: MetricsSummary, use_color: bool = True) -> None:
    """Print human-readable summary."""
    GREEN = "\033[92m" if use_color else ""
    RED = "\033[91m" if use_color else ""
    BLUE = "\033[94m" if use_color else ""
    RESET = "\033[0m" if use_color else ""

    print(f"\n{BLUE}{'=' * 50}")
    print(" Post-Deployment Metrics Summary")
    print(f"{'=' * 50}{RESET}\n")

    print(f"  URL: {summary.url}")
    print(f"  Timestamp: {summary.timestamp}")
    print()

    # Health status
    health_status = f"{GREEN}✓ Healthy{RESET}" if summary.healthy else f"{RED}✗ Unhealthy{RESET}"
    print(f"  Health: {health_status}")

    # Error rate
    error_status = f"{GREEN}✓{RESET}" if summary.error_rate_ok else f"{RED}✗{RESET}"
    print(f"  Error Rate: {summary.error_rate:.2f}% {error_status} (threshold: {summary.error_rate_threshold}%)")
    print(f"  Total Requests: {summary.total_requests}")
    print(f"  Error Requests (5xx): {summary.error_requests}")
    print()

    # Audit stats
    print(f"  Active Audits: {summary.active_audits}")
    print(f"  Completed Audits: {summary.audit_completed}")
    print(f"  Failed Audits: {summary.audit_failed}")
    print()

    # Webhook stats
    print(f"  Webhooks Delivered: {summary.webhook_delivered}")
    print(f"  Webhooks Failed: {summary.webhook_failed}")

    # Issues
    if summary.issues:
        print(f"\n{RED}Issues:{RESET}")
        for issue in summary.issues:
            print(f"  {RED}✗{RESET} {issue}")

    print(f"\n{BLUE}{'=' * 50}{RESET}")

    # Final verdict
    if summary.issues:
        print(f"{RED}METRICS CHECK FAILED{RESET}")
    else:
        print(f"{GREEN}METRICS CHECK PASSED{RESET}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Post-deployment metrics checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_metrics.py --url https://api.example.com
  python check_metrics.py --url https://api.example.com --error-threshold 3
  python check_metrics.py --url https://api.example.com --json
  python check_metrics.py --url https://api.example.com --alert

Environment Variables:
  SLACK_WEBHOOK_URL     Slack webhook for alerts
  DISCORD_WEBHOOK_URL   Discord webhook for alerts
  ERROR_RATE_THRESHOLD  Default error rate threshold (default: 5.0)
        """
    )

    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of the API (e.g., https://api.example.com)",
    )
    parser.add_argument(
        "--error-threshold",
        type=float,
        default=float(os.environ.get("ERROR_RATE_THRESHOLD", "5.0")),
        help="Error rate threshold percentage (default: 5.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--alert",
        action="store_true",
        help="Send alerts to configured webhooks",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        default=True,
        help="Exit with non-zero code if issues detected (default: True)",
    )

    args = parser.parse_args()

    # Clean up URL
    url = args.url.rstrip("/")

    # Analyze metrics
    summary = analyze_metrics(url, args.error_threshold)

    # Output
    if args.json:
        print(json.dumps(summary.to_dict(), indent=2))
    else:
        print_summary(summary, use_color=not args.no_color)

    # Send alerts if requested and there are issues
    if args.alert:
        slack_url = os.environ.get("SLACK_WEBHOOK_URL")
        discord_url = os.environ.get("DISCORD_WEBHOOK_URL")

        if summary.issues or not summary.healthy:
            if slack_url:
                if send_slack_alert(slack_url, summary):
                    print("Sent Slack alert")
                else:
                    print("Failed to send Slack alert", file=sys.stderr)

            if discord_url:
                if send_discord_alert(discord_url, summary):
                    print("Sent Discord alert")
                else:
                    print("Failed to send Discord alert", file=sys.stderr)

    # Exit code
    if args.fail_on_issues and summary.issues:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
