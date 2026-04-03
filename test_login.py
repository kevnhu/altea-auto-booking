#!/usr/bin/env python3
"""
Test script to set up your Altea login session

This script will:
1. Open a browser window (visible)
2. Navigate to myaltea.club
3. Wait for you to log in manually
4. Save your login session for the booking bot to use

Run this ONCE before running the main booking system.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from playwright.sync_api import sync_playwright
from loguru import logger
from config import Config

logger.remove()
logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")


def main():
    print("=" * 60)
    print("  ALTEA LOGIN SESSION SETUP")
    print("=" * 60)
    print()
    print("This will open a browser window where you can log in to Altea.")
    print("Once you're logged in, the session will be saved for automatic booking.")
    print()
    input("Press Enter to continue...")
    print()

    try:
        # Validate config
        Config.validate()

        logger.info("Starting Brave (visible mode)...")
        playwright = sync_playwright().start()
        user_data_dir = str(Config.PLAYWRIGHT_STATE_DIR / 'brave_profile')
        context = playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 900},
            executable_path="/usr/bin/brave-browser",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        page = context.new_page()

        logger.info(f"Navigating to {Config.ALTEA_URL}...")
        page.goto(Config.ALTEA_URL, timeout=30000)
        page.wait_for_load_state('networkidle')

        print()
        print("=" * 60)
        print("  PLEASE LOG IN TO ALTEA IN THE BROWSER WINDOW")
        print("=" * 60)
        print()
        print("1. If you're not already logged in, click the login button")
        print("2. Enter your Altea credentials")
        print("3. Complete the login process")
        print("4. Once you see your Altea homepage/workouts, come back here")
        print()
        input("Press Enter once you're logged in...")
        print()

        # Session is saved automatically in the persistent profile
        logger.info("Saving login session...")

        logger.success("✓ Login session saved successfully!")
        logger.info(f"   Saved to: {user_data_dir}")
        print()
        print("=" * 60)
        print("  SUCCESS! Setup complete.")
        print("=" * 60)
        print()
        print("Your login session has been saved.")
        print("The booking bot will now be able to book classes automatically")
        print("without needing to log in each time.")
        print()
        print("Next steps:")
        print("1. Configure your .env file with Gmail settings")
        print("2. Run: python3 src/main.py")
        print()

        # Clean up
        context.close()
        playwright.stop()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print()
        print("Please set up your .env file first:")
        print("  cp .env.example .env")
        print("  nano .env")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
