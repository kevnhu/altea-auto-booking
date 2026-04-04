"""
Main orchestrator for Altea Auto-Booking System

This script:
1. Monitors email for waitlist notifications (checks every 1 second)
2. When notification arrives, attempts to book the class
3. Retries up to MAX_RETRIES times
4. Sends email notifications on success/failure
5. Continues monitoring for next notification
"""
import sys
import time
from pathlib import Path
from typing import Dict
from loguru import logger

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from email_monitor import EmailMonitor
from booking_bot import BookingBot, AlreadyWaitlistedError
from notifier import Notifier


class AleaAutoBooker:
    """Main orchestrator for the auto-booking system"""

    def __init__(self):
        self.email_monitor = EmailMonitor()
        self.notifier = Notifier()

    def setup_logging(self):
        """Configure logging"""
        logger.remove()

        # Console logging - colorful and informative
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="INFO"
        )

        # File logging - detailed for debugging
        log_file = Config.LOGS_DIR / f"altea_booking_{time.strftime('%Y%m%d')}.log"
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="DEBUG",
            rotation="1 day",
            retention="30 days"
        )

        logger.info(f"Logging to: {log_file}")

    def try_booking_with_retries(self, class_info: Dict) -> bool:
        """
        Attempt to book a class with retry logic

        Args:
            class_info: Class details from email

        Returns:
            True if booking succeeded, False if all attempts failed
        """
        max_retries = Config.MAX_RETRIES

        for attempt in range(1, max_retries + 1):
            logger.info(f"═══ Booking Attempt {attempt}/{max_retries} ═══")

            bot = BookingBot()

            try:
                # Start browser
                if not bot.start_browser(headless=False):
                    logger.error(f"Failed to start browser on attempt {attempt}")
                    continue

                # Attempt booking
                success = bot.attempt_booking(class_info)

                if success:
                    logger.success(f"🎉 Booking successful on attempt {attempt}!")
                    self.notifier.notify_booking_success(class_info, attempt, bot.last_screenshot_path)
                    return True
                else:
                    logger.warning(f"Booking failed on attempt {attempt}")

            except AlreadyWaitlistedError:
                logger.info("Already waitlisted — spot was taken, no point retrying")
                self.notifier.notify_booking_failure(class_info, attempt)
                return False

            except Exception as e:
                logger.error(f"Error during booking attempt {attempt}: {e}")

            finally:
                # Always stop browser
                bot.stop_browser()

            # Wait a moment before retrying (if not last attempt)
            if attempt < max_retries:
                logger.info(f"Waiting 2 seconds before retry...")
                time.sleep(2)

        # All attempts failed
        logger.error(f"❌ All {max_retries} booking attempts failed")
        self.notifier.notify_booking_failure(class_info, max_retries)
        return False

    def handle_notification(self, class_info: Dict):
        """
        Handle a waitlist notification

        Args:
            class_info: Class details extracted from email
        """
        logger.info("=" * 60)
        logger.info("🔔 WAITLIST NOTIFICATION RECEIVED")
        logger.info("=" * 60)
        logger.info(f"Class: {class_info.get('class_name', 'Unknown')}")
        logger.info(f"Date: {class_info.get('date', 'Unknown')}")
        logger.info(f"Time: {class_info.get('time', 'Unknown')}")
        logger.info(f"Instructor: {class_info.get('instructor', 'Unknown')}")
        logger.info("=" * 60)

        # Attempt booking with retries
        success = self.try_booking_with_retries(class_info)

        if success:
            logger.success("✅ Booking completed successfully!")
        else:
            logger.warning("⚠️  Booking failed after all retries")

        logger.info("Resuming email monitoring...")
        logger.info("")

    def run(self):
        """Main entry point - start the auto-booking system"""
        try:
            # Validate configuration
            Config.validate()

            # Setup logging
            self.setup_logging()

            logger.info("=" * 60)
            logger.info("🏋️  ALTEA AUTO-BOOKING SYSTEM STARTING")
            logger.info("=" * 60)
            logger.info(f"Email: {Config.EMAIL_ADDRESS}")
            logger.info(f"Altea URL: {Config.ALTEA_URL}")
            logger.info(f"Poll interval: {Config.POLL_INTERVAL_SECONDS} second(s)")
            logger.info(f"Max retries: {Config.MAX_RETRIES}")
            logger.info(f"Notifications: {'Enabled' if Config.SEND_NOTIFICATIONS else 'Disabled'}")
            logger.info("=" * 60)
            logger.info("")

            # Start monitoring
            self.email_monitor.start_monitoring(self.handle_notification)

        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down gracefully...")
            sys.exit(0)
        except Exception as e:
            logger.exception(f"Fatal error: {e}")
            sys.exit(1)


if __name__ == '__main__':
    booker = AleaAutoBooker()
    booker.run()
