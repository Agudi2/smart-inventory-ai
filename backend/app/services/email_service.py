"""Email service for sending notifications."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings
from app.models.alert import Alert

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self):
        """Initialize the email service with SMTP configuration."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email or settings.smtp_username
        self.from_name = settings.smtp_from_name
        self.enabled = settings.email_notifications_enabled
        
        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """
        Create and authenticate SMTP connection.
        
        Returns:
            Authenticated SMTP connection
            
        Raises:
            Exception: If connection or authentication fails
        """
        try:
            # Create SMTP connection
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
            smtp.ehlo()
            
            # Start TLS encryption
            if self.smtp_port == 587:
                smtp.starttls()
                smtp.ehlo()
            
            # Authenticate if credentials provided
            if self.smtp_username and self.smtp_password:
                smtp.login(self.smtp_username, self.smtp_password)
            
            return smtp
            
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {str(e)}")
            raise
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email to the specified recipients.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            html_body: HTML content of the email
            text_body: Plain text content (optional, falls back to HTML)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Email notifications are disabled. Skipping email send.")
            return False
        
        if not to_emails:
            logger.warning("No recipient emails provided. Skipping email send.")
            return False
        
        if not self.from_email:
            logger.error("SMTP from_email not configured. Cannot send email.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(to_emails)
            
            # Attach plain text version
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            # Attach HTML version
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Send email
            with self._create_smtp_connection() as smtp:
                smtp.sendmail(self.from_email, to_emails, msg.as_string())
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            return False
    
    def send_alert_email(
        self,
        alert: Alert,
        recipient_emails: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email notification for an alert.
        
        Args:
            alert: Alert object to send notification for
            recipient_emails: List of recipient emails (defaults to configured recipients)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Email notifications are disabled.")
            return False
        
        # Use provided recipients or fall back to configured recipients
        recipients = recipient_emails or settings.alert_recipient_emails
        
        if not recipients:
            logger.warning("No recipient emails configured for alerts.")
            return False
        
        try:
            # Determine template based on alert type
            if alert.alert_type == "low_stock":
                template_name = "low_stock_alert.html"
                subject_prefix = "Low Stock Alert"
            elif alert.alert_type == "predicted_depletion":
                template_name = "predicted_depletion_alert.html"
                subject_prefix = "Stock Depletion Prediction"
            else:
                template_name = "generic_alert.html"
                subject_prefix = "Inventory Alert"
            
            # Build subject line
            severity_emoji = "🔴" if alert.severity == "critical" else "⚠️"
            subject = f"{severity_emoji} {subject_prefix}: {alert.product.name}"
            
            # Render email template
            template = self.jinja_env.get_template(template_name)
            html_body = template.render(
                alert=alert,
                product=alert.product,
                severity_emoji=severity_emoji,
                app_name=settings.app_name
            )
            
            # Create plain text version
            text_body = self._create_text_body(alert)
            
            # Send email
            return self.send_email(
                to_emails=recipients,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}", exc_info=True)
            return False
    
    def _create_text_body(self, alert: Alert) -> str:
        """
        Create plain text version of alert email.
        
        Args:
            alert: Alert object
            
        Returns:
            Plain text email body
        """
        text = f"""
{settings.app_name}
{'=' * 50}

ALERT: {alert.alert_type.upper().replace('_', ' ')}
Severity: {alert.severity.upper()}

Product: {alert.product.name}
SKU: {alert.product.sku}
Category: {alert.product.category}
Current Stock: {alert.product.current_stock} units
Reorder Threshold: {alert.product.reorder_threshold} units

Message:
{alert.message}

Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

{'=' * 50}
This is an automated notification from {settings.app_name}.
Please log in to your dashboard to take action.
"""
        return text.strip()
    
    def test_email_configuration(self, test_email: str) -> bool:
        """
        Test email configuration by sending a test email.
        
        Args:
            test_email: Email address to send test email to
            
        Returns:
            True if test email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.error("Email notifications are disabled. Cannot send test email.")
            return False
        
        try:
            subject = f"Test Email from {settings.app_name}"
            html_body = f"""
            <html>
                <body>
                    <h2>Email Configuration Test</h2>
                    <p>This is a test email from {settings.app_name}.</p>
                    <p>If you received this email, your email configuration is working correctly.</p>
                    <hr>
                    <p><small>Sent from {settings.app_name}</small></p>
                </body>
            </html>
            """
            text_body = f"""
Email Configuration Test

This is a test email from {settings.app_name}.
If you received this email, your email configuration is working correctly.

---
Sent from {settings.app_name}
"""
            
            return self.send_email(
                to_emails=[test_email],
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Email configuration test failed: {str(e)}", exc_info=True)
            return False
