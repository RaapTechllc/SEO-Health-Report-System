import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime

from storage import CompetitorStorage
from models import AlertEvent

class AlertSystem:
    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 587):
        self.logger = logging.getLogger(__name__)
        self.storage = CompetitorStorage()
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        
    def send_score_change_alert(self, alert: AlertEvent, recipients: List[str] = None):
        """Send alert for score changes."""
        if recipients is None:
            recipients = ["admin@company.com"]  # Default recipient
            
        try:
            # Create email content
            subject = f"🚨 Competitor Alert: {alert.competitor_url}"
            
            if alert.score_change > 0:
                emoji = "📈"
                direction = "increased"
                color = "green"
            else:
                emoji = "📉"
                direction = "decreased"
                color = "red"
                
            body = f"""
{emoji} Competitor Score Alert

URL: {alert.competitor_url}
Score Change: {alert.score_change} points
Previous Score: {alert.previous_score}/100
Current Score: {alert.current_score}/100
Direction: Score {direction}

Trigger Reason: {alert.trigger_reason}
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
            
    def _send_email(self, subject: str, body: str, recipients: List[str]):
        """Send email alert (may fail in development environments)."""
        try:
            msg = MIMEMultipart()
            msg['From'] = "competitive-monitor@company.com"
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
            
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
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
