"""
Notification system for Altea Auto-Booking
Sends email notifications about booking attempts
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
from typing import Dict, Optional
from loguru import logger

from config import Config


class Notifier:
    """Sends email notifications about booking attempts"""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, subject: str, body: str, screenshot_path: Optional[str] = None) -> bool:
        """
        Send an email notification

        Args:
            subject: Email subject
            body: Email body (plain text)
            screenshot_path: Optional path to a screenshot to attach

        Returns:
            True if sent successfully, False otherwise
        """
        if not Config.SEND_NOTIFICATIONS:
            logger.info("Notifications disabled, skipping email")
            return False

        try:
            # Create message
            msg = MIMEMultipart('mixed')
            msg['From'] = Config.EMAIL_ADDRESS
            msg['To'] = Config.NOTIFICATION_EMAIL
            msg['Subject'] = subject

            # Add plain text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Attach screenshot if provided
            if screenshot_path and Path(screenshot_path).exists():
                with open(screenshot_path, 'rb') as f:
                    img = MIMEImage(f.read(), name=Path(screenshot_path).name)
                    msg.attach(img)
                logger.info(f"Attached screenshot: {screenshot_path}")

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

    def notify_booking_success(self, class_info: Dict, screenshot_path: Optional[str] = None):
        """Send notification when booking succeeds"""
        class_name = class_info.get('class_name', 'Unknown Class')
        self.send_email(f"✓ Auto Booked - {class_name}", "Booking Successful!", screenshot_path=screenshot_path)

    def notify_booking_failure(self, class_info: Dict, reason: str = "Unknown", screenshot_path: Optional[str] = None):
        """Send notification when booking fails, with reason in subject and screenshot attached"""
        class_name = class_info.get('class_name', 'Unknown Class')
        self.send_email(f"✗ Booking Failed ({reason}) - {class_name}", f"Booking Failed: {reason}", screenshot_path=screenshot_path)


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
    notifier.notify_booking_success(test_class_info)

    print("\n2. Testing failure notification...")
    notifier.notify_booking_failure(test_class_info, "Could not find booking button")
