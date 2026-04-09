"""
Configuration module for Altea Auto-Booking System
Loads settings from environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """Configuration class for the booking system"""

    # Email Configuration
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))

    # Altea Website Configuration
    ALTEA_URL = os.getenv('ALTEA_URL')
    ALTEA_USERNAME = os.getenv('ALTEA_USERNAME')
    ALTEA_PASSWORD = os.getenv('ALTEA_PASSWORD')

    # Email Filter Settings
    EMAIL_FROM_FILTER = os.getenv('EMAIL_FROM_FILTER', 'altea')
    EMAIL_SUBJECT_FILTER = os.getenv('EMAIL_SUBJECT_FILTER', 'waitlist')

    # Booking Configuration
    POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', '1'))

    # Notification Settings
    SEND_NOTIFICATIONS = os.getenv('SEND_NOTIFICATIONS', 'true').lower() == 'true'
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', EMAIL_ADDRESS)

    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    LOGS_DIR = PROJECT_ROOT / 'logs'
    PLAYWRIGHT_STATE_DIR = PROJECT_ROOT / 'playwright-state'

    @classmethod
    def validate(cls):
        """Validate that all required settings are present"""
        required = [
            ('EMAIL_ADDRESS', cls.EMAIL_ADDRESS),
            ('EMAIL_PASSWORD', cls.EMAIL_PASSWORD),
            ('ALTEA_URL', cls.ALTEA_URL),
            ('ALTEA_USERNAME', cls.ALTEA_USERNAME),
            ('ALTEA_PASSWORD', cls.ALTEA_PASSWORD),
        ]

        missing = [name for name, value in required if not value]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please copy .env.example to .env and fill in your details."
            )

        # Create necessary directories
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.PLAYWRIGHT_STATE_DIR.mkdir(exist_ok=True)

        return True


if __name__ == '__main__':
    # Test configuration
    try:
        Config.validate()
        print("✓ Configuration is valid!")
        print(f"Email: {Config.EMAIL_ADDRESS}")
        print(f"Altea URL: {Config.ALTEA_URL}")
        print(f"Poll interval: {Config.POLL_INTERVAL_SECONDS}s")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
