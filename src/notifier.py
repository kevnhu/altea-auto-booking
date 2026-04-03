"""
Notification system for Altea Auto-Booking
Sends email notifications about booking attempts
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from config import Config


class Notifier:
    """Sends email notifications about booking attempts"""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, subject: str, body: str) -> bool:
        """
        Send an email notification

        Args:
            subject: Email subject
            body: Email body (plain text)

        Returns:
            True if sent successfully, False otherwise
        """
        if not Config.SEND_NOTIFICATIONS:
            logger.info("Notifications disabled, skipping email")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = Config.EMAIL_ADDRESS
            msg['To'] = Config.NOTIFICATION_EMAIL
            msg['Subject'] = subject

            # Add plain text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Connect to Gmail's SMTP server
            logger.info(f"Sending notification email to {Config.NOTIFICATION_EMAIL}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
                server.send_message(msg)

            logger.success("✓ Notification email sent")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification email: {e}")
            return False

    def notify_booking_success(self, class_info: Dict, attempt_number: int):
        """Send notification when booking succeeds"""
        class_name = class_info.get('class_name', 'Unknown Class')

        subject = f"✓ Auto Booked - {class_name}"

        body = f"""Booking Successful!"""

        self.send_email(subject, body)

    def notify_booking_failure(self, class_info: Dict, total_attempts: int, error: Optional[str] = None):
        """Send notification when all booking attempts fail"""
        class_name = class_info.get('class_name', 'Unknown Class')

        subject = f"✗ Auto Booking Failed - {class_name}"

        body = "Booking Failed"

        if error:
            body += f"\n\nError: {error}"

        self.send_email(subject, body)

    def notify_booking_attempt(self, class_info: Dict, attempt_number: int):
        """Send notification for each booking attempt (optional, might be too many emails)"""
        class_name = class_info.get('class_name', 'Unknown Class')

        subject = f"⏳ Booking Attempt {attempt_number} - {class_name}"

        body = f"Booking attempt {attempt_number} in progress."

        self.send_email(subject, body)


if __name__ == '__main__':
    # Test notifications
    from loguru import logger
    import sys

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    test_class_info = {
        'class_name': 'Yoga',
        'date': '01/23/2026',
        'time': '6:00 PM',
        'instructor': 'John Doe'
    }

    notifier = Notifier()

    print("\n1. Testing success notification...")
    notifier.notify_booking_success(test_class_info, 1)

    print("\n2. Testing failure notification...")
    notifier.notify_booking_failure(test_class_info, 2, "Could not find booking button")
