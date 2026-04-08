"""
Email Monitor for Altea Auto-Booking System
Monitors Gmail inbox for waitlist notifications using IMAP
"""
import time
import re
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import unquote
from imap_tools import MailBox, AND
from loguru import logger

from config import Config


class EmailMonitor:
    """Monitors email inbox for Altea waitlist notifications"""

    def __init__(self):
        self.mailbox = None
        self.last_reconnect_time = 0
        self.reconnect_interval = 60 * 10  # Reconnect every 10 minutes

    def connect(self):
        """Connect to Gmail via IMAP"""
        try:
            logger.info(f"Connecting to {Config.IMAP_SERVER}...")
            self.mailbox = MailBox(Config.IMAP_SERVER)
            self.mailbox.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
            logger.success("✓ Connected to email successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email: {e}")
            return False

    def disconnect(self):
        """Disconnect from email server"""
        if self.mailbox:
            try:
                self.mailbox.logout()
                logger.info("Disconnected from email")
            except:
                pass

    def extract_class_info(self, email_body: str, email_subject: str, email_html: str = None) -> Dict[str, str]:
        """
        Extract class information from Altea waitlist notification email

        Altea emails contain:
        - Event name (e.g., "Underground Ride")
        - Date (e.g., "Tuesday January 20th")
        - Time (e.g., "7:30PM")
        - Direct booking URL (e.g., https://myaltea.club/workouts/evt_xxx)

        Returns dict with class_url, class_name, date, time
        """
        info = {
            'class_url': None,
            'class_name': None,
            'date': None,
            'time': None,
            'raw_body': email_body,
            'subject': email_subject
        }

        # Use HTML version if available (more reliable for links)
        content = email_html or email_body

        # Extract the booking URL from the email
        # Altea emails wrap links in AWS tracking redirects, e.g.:
        # https://xxx.r.us-east-1.awstrack.me/L0/https:%2F%2Fmyaltea.app%2Fbooking%2Fevt_xxx/...
        # First try to find the URL-encoded booking URL inside a tracking link
        tracking_match = re.search(r'https://[^"]*awstrack\.me/[^"]*?(https:%2F%2Fmyaltea\.app%2Fbooking%2F[^/"]+)', content)
        if tracking_match:
            info['class_url'] = unquote(tracking_match.group(1))
            logger.info(f"   Extracted class URL from tracking link: {info['class_url']}")
        else:
            # Fallback: try direct URL match
            url_match = re.search(r'https://myaltea\.app/booking/[^\s"<>]+', content)
            if url_match:
                info['class_url'] = url_match.group(0)
                # Clean up any trailing characters (>, ", etc.)
                info['class_url'] = re.sub(r'[">)\s]+$', '', info['class_url'])
                logger.info(f"   Extracted class URL: {info['class_url']}")
            else:
                logger.warning("   Could not extract class URL from email!")

        # Extract event name from subject line
        # Altea subjects look like: "A Spot Has Opened Up in LF3 | Tread & Turf!"
        subject_match = re.search(r'Opened Up in (.+?)!?\s*$', email_subject)
        if subject_match:
            info['class_name'] = subject_match.group(1).strip()
        else:
            # Fallback: "A spot in Underground Ride is available!"
            subject_match = re.search(r'spot in (.+?) is available', email_subject, re.IGNORECASE)
            if subject_match:
                info['class_name'] = subject_match.group(1).strip()
            else:
                # Fallback: "Event: XXX" in email body
                event_match = re.search(r'Event:\s*([^\n]+)', content, re.IGNORECASE)
                if event_match:
                    info['class_name'] = event_match.group(1).strip()

        # Extract date - looks for patterns like "Date: Tuesday January 20th"
        date_match = re.search(r'Date:\s*(.+?)(?:\n|Time:|Location:)', content, re.IGNORECASE)
        if date_match:
            info['date'] = date_match.group(1).strip()

        # Extract time - looks for patterns like "Time: 7:30PM"
        time_match = re.search(r'Time:\s*(\d{1,2}:\d{2}\s*[AP]M)', content, re.IGNORECASE)
        if time_match:
            info['time'] = time_match.group(1).strip()

        return info

    def check_for_notifications(self) -> Optional[Dict]:
        """
        Check inbox for new waitlist notifications
        Returns class info dict if found, None otherwise
        """
        try:
            # Ping the server to verify connection is alive
            # A stale connection returns empty results silently
            self.mailbox.client.noop()

            # Search for unread emails matching our filters
            criteria = AND(seen=False)

            messages = list(self.mailbox.fetch(criteria, mark_seen=False, limit=10, reverse=True))

            for msg in messages:
                # Check if email is from Altea
                if Config.EMAIL_FROM_FILTER.lower() not in msg.from_.lower():
                    continue

                # Check if subject contains waitlist keyword
                if Config.EMAIL_SUBJECT_FILTER.lower() not in msg.subject.lower():
                    continue

                logger.info(f"📧 New waitlist notification found!")
                logger.info(f"   From: {msg.from_}")
                logger.info(f"   Subject: {msg.subject}")
                logger.info(f"   Date: {msg.date}")

                # Extract class information (prefer HTML for better link extraction)
                class_info = self.extract_class_info(
                    email_body=msg.text or "",
                    email_subject=msg.subject,
                    email_html=msg.html
                )

                # Mark as read immediately so it's never processed again
                self.mailbox.flag(msg.uid, ['\\Seen'], True)
                logger.info(f"   Marked email as read")

                # Skip — mark-as-read above prevents reprocessing

                return class_info

            return None

        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            # Reconnect on connection errors
            logger.info("Reconnecting to email server...")
            try:
                self.disconnect()
            except:
                pass
            if self.connect():
                self.last_reconnect_time = time.time()
            return None

    def start_monitoring(self, callback):
        """
        Start monitoring emails in a loop
        Calls callback function when notification is found

        Args:
            callback: Function to call with class_info when notification found
        """
        logger.info(f"🔍 Starting email monitor (checking every {Config.POLL_INTERVAL_SECONDS}s)")
        logger.info(f"   Looking for emails from: {Config.EMAIL_FROM_FILTER}")
        logger.info(f"   With subject containing: {Config.EMAIL_SUBJECT_FILTER}")

        if not self.connect():
            logger.error("Failed to start monitoring - could not connect to email")
            return

        self.last_reconnect_time = time.time()

        try:
            while True:
                # Proactively reconnect every 20 minutes before Gmail drops the connection
                if time.time() - self.last_reconnect_time >= self.reconnect_interval:
                    logger.info("Proactive reconnect to keep IMAP connection alive...")
                    self.disconnect()
                    if not self.connect():
                        logger.error("Failed to reconnect, retrying next cycle...")
                        time.sleep(Config.POLL_INTERVAL_SECONDS)
                        continue
                    self.last_reconnect_time = time.time()

                class_info = self.check_for_notifications()

                if class_info:
                    logger.success("✓ Notification detected! Triggering booking bot...")
                    callback(class_info)
                    # Reconnect after booking — connection likely went stale during the attempt
                    self.disconnect()
                    if self.connect():
                        self.last_reconnect_time = time.time()

                # Wait before next check
                time.sleep(Config.POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("Stopping email monitor...")
        except Exception as e:
            logger.error(f"Email monitor crashed: {e}")
        finally:
            self.disconnect()


if __name__ == '__main__':
    # Test the email monitor
    from loguru import logger
    import sys

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    def test_callback(class_info):
        print(f"\n🎯 Would trigger booking for: {class_info}")

    monitor = EmailMonitor()
    monitor.start_monitoring(test_callback)
