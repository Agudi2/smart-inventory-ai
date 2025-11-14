"""Test script for email notification functionality."""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.email_service import EmailService


def test_email_configuration():
    """Test email configuration and send a test email."""
    
    print("=" * 60)
    print("Email Notification System Test")
    print("=" * 60)
    print()
    
    # Display current configuration
    print("Current Email Configuration:")
    print(f"  Email Notifications Enabled: {settings.email_notifications_enabled}")
    print(f"  SMTP Host: {settings.smtp_host}")
    print(f"  SMTP Port: {settings.smtp_port}")
    print(f"  SMTP Username: {settings.smtp_username or '(not set)'}")
    print(f"  SMTP Password: {'*' * 8 if settings.smtp_password else '(not set)'}")
    print(f"  From Email: {settings.smtp_from_email or settings.smtp_username or '(not set)'}")
    print(f"  From Name: {settings.smtp_from_name}")
    print(f"  Alert Recipients: {', '.join(settings.alert_recipient_emails) if settings.alert_recipient_emails else '(none configured)'}")
    print()
    
    # Check if email is enabled
    if not settings.email_notifications_enabled:
        print("⚠️  Email notifications are DISABLED")
        print("   To enable, set EMAIL_NOTIFICATIONS_ENABLED=True in your .env file")
        print()
        return False
    
    # Check if SMTP credentials are configured
    if not settings.smtp_username or not settings.smtp_password:
        print("❌ SMTP credentials not configured")
        print("   Please set SMTP_USERNAME and SMTP_PASSWORD in your .env file")
        print()
        return False
    
    # Initialize email service
    email_service = EmailService()
    
    # Prompt for test email address
    print("Enter a test email address to send a test notification:")
    test_email = input("Email: ").strip()
    
    if not test_email:
        print("❌ No email address provided")
        return False
    
    print()
    print(f"Sending test email to {test_email}...")
    
    # Send test email
    try:
        success = email_service.test_email_configuration(test_email)
        
        if success:
            print("✅ Test email sent successfully!")
            print(f"   Check {test_email} for the test message")
            print()
            return True
        else:
            print("❌ Failed to send test email")
            print("   Check the logs for error details")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        print()
        return False


def display_setup_instructions():
    """Display setup instructions for different email providers."""
    
    print()
    print("=" * 60)
    print("Email Setup Instructions")
    print("=" * 60)
    print()
    
    print("📧 Gmail Setup:")
    print("   1. Enable 2-Factor Authentication on your Google account")
    print("   2. Generate an App Password:")
    print("      - Go to: https://myaccount.google.com/apppasswords")
    print("      - Select 'Mail' and your device")
    print("      - Copy the generated 16-character password")
    print("   3. Set in .env file:")
    print("      SMTP_HOST=smtp.gmail.com")
    print("      SMTP_PORT=587")
    print("      SMTP_USERNAME=your-email@gmail.com")
    print("      SMTP_PASSWORD=your-app-password")
    print("      SMTP_FROM_EMAIL=your-email@gmail.com")
    print()
    
    print("📧 SendGrid Setup:")
    print("   1. Create a SendGrid account: https://sendgrid.com")
    print("   2. Generate an API key in Settings > API Keys")
    print("   3. Set in .env file:")
    print("      SMTP_HOST=smtp.sendgrid.net")
    print("      SMTP_PORT=587")
    print("      SMTP_USERNAME=apikey")
    print("      SMTP_PASSWORD=your-sendgrid-api-key")
    print("      SMTP_FROM_EMAIL=your-verified-sender@yourdomain.com")
    print()
    
    print("📧 AWS SES Setup:")
    print("   1. Set up AWS SES and verify your domain/email")
    print("   2. Create SMTP credentials in SES console")
    print("   3. Set in .env file:")
    print("      SMTP_HOST=email-smtp.us-east-1.amazonaws.com")
    print("      SMTP_PORT=587")
    print("      SMTP_USERNAME=your-ses-smtp-username")
    print("      SMTP_PASSWORD=your-ses-smtp-password")
    print("      SMTP_FROM_EMAIL=your-verified-email@yourdomain.com")
    print()
    
    print("📧 Generic SMTP Setup:")
    print("   Set in .env file:")
    print("      SMTP_HOST=your-smtp-server.com")
    print("      SMTP_PORT=587")
    print("      SMTP_USERNAME=your-username")
    print("      SMTP_PASSWORD=your-password")
    print("      SMTP_FROM_EMAIL=your-email@domain.com")
    print()
    
    print("After configuration, enable email notifications:")
    print("   EMAIL_NOTIFICATIONS_ENABLED=True")
    print("   ALERT_RECIPIENT_EMAILS=[\"admin@example.com\",\"manager@example.com\"]")
    print()


if __name__ == "__main__":
    print()
    
    # Run test
    success = test_email_configuration()
    
    # Show setup instructions if test failed
    if not success:
        display_setup_instructions()
    
    print("=" * 60)
    print()
