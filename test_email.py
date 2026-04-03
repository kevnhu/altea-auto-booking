#!/usr/bin/env python3
"""
Test script to verify email monitoring is working

This script will:
1. Connect to your Gmail
2. Look for recent Altea emails
3. Show you what emails it finds
4. Test parsing of email content

Run this to verify your Gmail credentials and email filtering settings.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from loguru import logger
from config import Config
from email_monitor import EmailMonitor

logger.remove()
logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")


def main():
    print("=" * 60)
    print("  ALTEA EMAIL MONITOR TEST")
    print("=" * 60)
    print()

    try:
        # Validate config
        Config.validate()

        print(f"Email: {Config.EMAIL_ADDRESS}")
        print(f"Looking for emails from: {Config.EMAIL_FROM_FILTER}")
        print(f"With subject containing: {Config.EMAIL_SUBJECT_FILTER}")
        print()
        print("Connecting to Gmail...")
        print()

        monitor = EmailMonitor()

        if not monitor.connect():
            logger.error("Failed to connect to Gmail")
            print()
            print("Please check:")
            print("1. EMAIL_ADDRESS is correct in .env")
            print("2. EMAIL_PASSWORD is your App Password (not regular password)")
            print("3. You've enabled 2-Step Verification on your Google account")
            print("4. You've created an App Password at https://myaccount.google.com/apppasswords")
            return

        logger.success("✓ Connected to Gmail successfully!")
        print()

        # Look for recent Altea emails (including read ones for testing)
        logger.info("Searching for recent Altea emails...")

        try:
            from imap_tools import AND
            # Search for any emails from Altea (both read and unread)
            criteria = AND(from_=Config.EMAIL_FROM_FILTER)
            messages = list(monitor.mailbox.fetch(criteria, mark_seen=False, limit=5, reverse=True))

            if not messages:
                logger.warning(f"No emails found from '{Config.EMAIL_FROM_FILTER}'")
                print()
                print("This could mean:")
                print(f"1. You haven't received any emails from Altea yet")
                print(f"2. EMAIL_FROM_FILTER might be wrong (currently: {Config.EMAIL_FROM_FILTER})")
                print()
                print("Check your Gmail inbox and find an Altea email.")
                print("Look at the 'From' address and update EMAIL_FROM_FILTER in .env if needed.")
            else:
                logger.success(f"✓ Found {len(messages)} recent Altea email(s)!")
                print()

                for i, msg in enumerate(messages, 1):
                    print(f"Email {i}:")
                    print(f"  From: {msg.from_}")
                    print(f"  Subject: {msg.subject}")
                    print(f"  Date: {msg.date}")

                    # Try to parse it
                    class_info = monitor.extract_class_info(
                        email_body=msg.text or "",
                        email_subject=msg.subject,
                        email_html=msg.html
                    )

                    if class_info.get('class_url'):
                        print(f"  ✓ Class URL: {class_info['class_url']}")
                        print(f"  ✓ Class Name: {class_info.get('class_name', 'Unknown')}")
                        print(f"  ✓ Date: {class_info.get('date', 'Unknown')}")
                        print(f"  ✓ Time: {class_info.get('time', 'Unknown')}")
                    else:
                        print(f"  ⚠️  Could not extract class URL from this email")

                    print()

        except Exception as e:
            logger.error(f"Error searching emails: {e}")

        monitor.disconnect()

        print("=" * 60)
        print("  TEST COMPLETE")
        print("=" * 60)
        print()
        print("If the test found your emails and extracted the class URL,")
        print("you're ready to run the full booking system!")
        print()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print()
        print("Please set up your .env file first:")
        print("  cp .env.example .env")
        print("  nano .env")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
