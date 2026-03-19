import html
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from models import AlertEvent
from storage import CompetitorStorage

# SMTP configuration from environment variables
SMTP_FROM = os.environ.get("ALERT_SMTP_FROM", "competitive_monitor@company.com")
SMTP_DEFAULT_RECIPIENTS = os.environ.get("ALERT_DEFAULT_RECIPIENTS", "").split(",")


class AlertSystem:
    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 587):
        self.logger = logging.getLogger(__name__)
        self.storage = CompetitorStorage()
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_score_change_alert(self, alert: AlertEvent, recipients: list[str] = None):
        """Send alert for score changes."""
        if recipients is None:
            recipients = [r.strip() for r in SMTP_DEFAULT_RECIPIENTS if r.strip()]
        if not recipients:
            self.logger.warning("No alert recipients configured. Set ALERT_DEFAULT_RECIPIENTS.")
            return

        try:
            # Create email content
            subject = f"🚨 Competitor Alert: {alert.competitor_url}"

            if alert.score_change > 0:
                emoji = "📈"
                direction = "increased"
            else:
                emoji = "📉"
                direction = "decreased"

            # Sanitize user-controlled fields for safe inclusion in email
            safe_url = html.escape(str(alert.competitor_url))
            safe_reason = html.escape(str(alert.trigger_reason))

            body = f"""\
{emoji} Competitor Score Alert

URL: {safe_url}
Score Change: {alert.score_change} points
Previous Score: {alert.previous_score}/100
Current Score: {alert.current_score}/100
Direction: Score {direction}

Trigger Reason: {safe_reason}
Timestamp: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

This alert was triggered because the score change exceeded the configured threshold.
Please review the competitor's recent changes and consider adjusting your strategy.
"""

            # Log the alert (always)
            self.logger.warning(f"COMPETITOR ALERT: {alert.competitor_url} score {direction} by {abs(alert.score_change)} points")

            # Try to send email (may fail in development)
            try:
                self._send_email(subject, body, recipients)
                self.logger.info(f"Alert email sent to {len(recipients)} recipients")
            except Exception as e:
                self.logger.warning(f"Failed to send email alert: {e}")

        except Exception as e:
            self.logger.error(f"Failed to process alert: {e}")

    def _send_email(self, subject: str, body: str, recipients: list[str]):
        """Send email alert (may fail in development environments)."""
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_FROM
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Try to connect to SMTP server
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            for recipient in recipients:
                msg['To'] = recipient
                server.send_message(msg)

            server.quit()

        except Exception as e:
            # Don't fail the whole alert system if email fails
            raise Exception(f"SMTP error: {e}")

    def get_recent_alerts(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get recent alerts for dashboard display."""
        try:
            # This would query the database for recent alerts
            # For now, return empty list as we don't have the query implemented
            return []
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
            return []

# Global alert system
alert_system = AlertSystem()
