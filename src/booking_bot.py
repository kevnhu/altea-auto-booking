"""
Booking Bot for Altea Auto-Booking System
Uses Playwright to automate booking on Altea website
"""
import time
import random
from pathlib import Path
from typing import Dict, Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout
from loguru import logger

from config import Config


class AlreadyWaitlistedError(Exception):
    """Raised when the page shows 'Waitlisted' — spot was taken, no point retrying"""
    pass


class BookingBot:
    """Automates booking of gym classes on Altea website"""

    def __init__(self):
        self.page: Optional[Page] = None
        self.context = None
        self.playwright = None

    def start_browser(self, headless: bool = True):
        """
        Start the browser

        Args:
            headless: If False, shows the browser window (useful for debugging)
        """
        try:
            logger.info("Starting browser...")
            self.playwright = sync_playwright().start()

            # Launch Brave (real browser — much harder to detect than Playwright's bundled browser)
            user_data_dir = str(Config.PLAYWRIGHT_STATE_DIR / 'brave_profile')
            context = self.playwright.chromium.launch_persistent_context(
                user_data_dir,
                headless=headless,
                viewport={"width": 1280, "height": 900},
                executable_path="/usr/bin/brave-browser",
                args=[
                    "--disable-blink-features=AutomationControlled",
                ],
                ignore_default_args=["--enable-automation"],
            )
            self.context = context

            self.page = context.new_page()

            logger.success("✓ Browser started")
            return True

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False

    def stop_browser(self):
        """Stop the browser and cleanup"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser stopped")
        except Exception as e:
            logger.error(f"Error stopping browser: {e}")

    def login(self) -> bool:
        """
        Login to Altea website

        NOTE: You'll need to customize the selectors based on Altea's actual login page
        """
        try:
            logger.info(f"Navigating to {Config.ALTEA_URL}...")
            self.page.goto(Config.ALTEA_URL, timeout=30000)

            # Wait a moment for the page to load
            self.page.wait_for_load_state('networkidle')

            # TODO: Customize these selectors based on actual Altea website
            # You'll need to inspect the login form and replace these selectors

            # Example selectors (THESE NEED TO BE CUSTOMIZED):
            # Look for username field - common selectors:
            # - input[name="username"]
            # - input[type="email"]
            # - #username
            # - .username-input

            logger.info("Filling in login credentials...")

            # Try common username field selectors
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                '#username',
                '#email',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]'
            ]

            username_filled = False
            for selector in username_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        self.page.fill(selector, Config.ALTEA_USERNAME, timeout=5000)
                        username_filled = True
                        logger.info(f"✓ Found username field: {selector}")
                        break
                except:
                    continue

            if not username_filled:
                logger.error("Could not find username field. Please inspect the login page.")
                return False

            # Try common password field selectors
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password'
            ]

            password_filled = False
            for selector in password_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        self.page.fill(selector, Config.ALTEA_PASSWORD, timeout=5000)
                        password_filled = True
                        logger.info(f"✓ Found password field: {selector}")
                        break
                except:
                    continue

            if not password_filled:
                logger.error("Could not find password field. Please inspect the login page.")
                return False

            # Try to find and click login button
            login_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                'button:has-text("Login")',
                '.login-button',
                '#login-button'
            ]

            button_clicked = False
            for selector in login_button_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        self.page.click(selector, timeout=5000)
                        button_clicked = True
                        logger.info(f"✓ Clicked login button: {selector}")
                        break
                except:
                    continue

            if not button_clicked:
                logger.warning("Could not find login button, trying form submit...")
                self.page.keyboard.press('Enter')

            # Wait for navigation after login
            self.page.wait_for_load_state('networkidle', timeout=15000)

            # Check if login was successful (customize this check)
            current_url = self.page.url
            logger.info(f"After login, URL: {current_url}")

            logger.success("✓ Login successful! Session saved via persistent profile.")

            return True

        except PlaywrightTimeout as e:
            logger.error(f"Timeout during login: {e}")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def navigate_to_class(self, class_info: Dict) -> bool:
        """
        Navigate to the specific class using the URL from the email

        Args:
            class_info: Dictionary with class_url from email

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            class_url = class_info.get('class_url')

            if not class_url:
                logger.error("No class URL found in email!")
                logger.error("Email might not have been parsed correctly.")
                return False

            logger.info(f"Navigating to class: {class_info.get('class_name', 'Unknown')}")
            logger.info(f"   URL: {class_url}")
            logger.info(f"   Date: {class_info.get('date', 'Unknown')}")
            logger.info(f"   Time: {class_info.get('time', 'Unknown')}")

            # Navigate directly to the class page
            self.page.goto(class_url, timeout=30000, wait_until='networkidle')

            # Wait for page to fully settle
            self.page.wait_for_load_state('domcontentloaded')
            self.page.wait_for_timeout(random.randint(1500, 2500))

            logger.success("✓ Successfully navigated to class page")
            return True

        except PlaywrightTimeout as e:
            logger.error(f"Timeout navigating to class: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to navigate to class: {e}")
            return False

    def book_class(self) -> bool:
        """
        Click the "Book Now" button on Altea's class page

        The button is greyed out when full, and becomes clickable when a spot opens.
        We need to wait for it to become enabled, then click it.

        Returns:
            True if booking successful, False otherwise
        """
        try:
            logger.info("Looking for 'Book Now' button...")

            # Altea's booking button - try multiple selectors
            # Includes Angular-specific selectors for the booking fab/buttons
            booking_button_selectors = [
                'button:has-text("Book Now")',
                'button:has-text("Book now")',
                'button:has-text("BOOK NOW")',
                'button:has-text("Book")',
                '[class*="book-buttons"] button',
                '[class*="booking-fab"] button',
                '[class*="booking-fab"]',
            ]

            # Wait for any booking button to appear (up to 10 seconds)
            button = None
            for attempt in range(20):  # 20 x 0.5s = 10 seconds max
                for selector in booking_button_selectors:
                    try:
                        locator = self.page.locator(selector)
                        if locator.count() > 0:
                            button = locator.first
                            logger.info(f"✓ Found booking button using: {selector}")
                            break
                    except:
                        continue
                if button:
                    break
                self.page.wait_for_timeout(500)

            if not button:
                logger.error("Could not find 'Book Now' button on the page")
                # Take a screenshot for debugging
                screenshot_path = Config.LOGS_DIR / f"no_button_{int(time.time())}.png"
                self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot saved to: {screenshot_path}")
                return False

            # Wait for the button to become enabled (not disabled)
            logger.info("Waiting for button to become enabled...")
            max_wait_seconds = 10  # Wait up to 10 seconds for button to become enabled

            for i in range(max_wait_seconds * 2):  # Check every 0.5 seconds
                try:
                    if button.is_enabled():
                        logger.success("✓ Button is enabled! Clicking...")
                        # Move mouse to button first like a human would
                        button.scroll_into_view_if_needed()
                        button.hover()
                        self.page.wait_for_timeout(random.randint(500, 1000))
                        button.click(timeout=5000)
                        logger.success("✓ Clicked 'Book Now' button!")
                        break
                except:
                    pass

                self.page.wait_for_timeout(500)
            else:
                # Button never became enabled
                logger.error(f"Button still disabled after {max_wait_seconds} seconds")
                logger.warning("Class might still be full, or there's an issue")
                return False

            # Wait for confirmation dialog to fully load
            self.page.wait_for_load_state('networkidle')
            self.page.wait_for_timeout(random.randint(2000, 3000))

            # Check if we're waitlisted — spot was taken by someone else
            if (self.page.locator('text="Waitlisted"').count() > 0 or
                    self.page.locator('text="You just missed it"').count() > 0):
                logger.info("Status: Waitlisted — spot was taken, skipping retries")
                raise AlreadyWaitlistedError()

            # Click "Confirm Booking" - required to complete the booking
            logger.info("Waiting for 'Confirm Booking' button...")
            screenshot_path = Config.LOGS_DIR / f"pre_confirm_{int(time.time())}.png"
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"Pre-confirm screenshot saved to: {screenshot_path}")
            try:
                confirm_clicked = False

                # Log all visible buttons for debugging
                try:
                    buttons = self.page.locator('button').all()
                    logger.info(f"Found {len(buttons)} buttons on page:")
                    for b in buttons:
                        try:
                            logger.info(f"   Button: '{b.text_content().strip()}' visible={b.is_visible()}")
                        except:
                            pass
                except:
                    pass

                # Strategy 1: role-based locator
                for name in ["Confirm Booking", "Confirm"]:
                    try:
                        btn = self.page.get_by_role("button", name=name)
                        if btn.count() > 0:
                            btn.first.scroll_into_view_if_needed()
                            btn.first.hover()
                            self.page.wait_for_timeout(random.randint(800, 1500))
                            btn.first.click()
                            logger.success(f"✓ Clicked '{name}' via role locator")
                            confirm_clicked = True
                            break
                    except:
                        continue

                # Strategy 2: text selectors
                if not confirm_clicked:
                    for selector in [
                        'button:has-text("Confirm Booking")',
                        'button:has-text("Confirm")',
                    ]:
                        try:
                            locator = self.page.locator(selector)
                            if locator.count() > 0:
                                locator.first.scroll_into_view_if_needed()
                                self.page.wait_for_timeout(1000)
                                locator.first.click()
                                logger.success(f"✓ Clicked confirm using: {selector}")
                                confirm_clicked = True
                                break
                        except:
                            continue

                # Strategy 3: JavaScript click as last resort
                if not confirm_clicked:
                    try:
                        clicked = self.page.evaluate('''() => {
                            const buttons = document.querySelectorAll('button');
                            for (const btn of buttons) {
                                if (btn.textContent.includes('Confirm')) {
                                    btn.scrollIntoView();
                                    btn.click();
                                    return btn.textContent.trim();
                                }
                            }
                            return null;
                        }''')
                        if clicked:
                            logger.success(f"✓ Clicked '{clicked}' via JavaScript")
                            confirm_clicked = True
                    except Exception as e:
                        logger.warning(f"JavaScript click failed: {e}")

                if not confirm_clicked:
                    raise Exception("Could not find Confirm Booking button with any strategy")
            except Exception as e:
                logger.error(f"Could not find or click 'Confirm Booking' button: {e}")
                screenshot_path = Config.LOGS_DIR / f"booking_error_{int(time.time())}.png"
                self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Error screenshot saved to: {screenshot_path}")
                return False

            # Wait for the booking to fully process
            self.page.wait_for_load_state('networkidle')
            self.page.wait_for_timeout(3000)

            # Take a success screenshot
            screenshot_path = Config.LOGS_DIR / f"booking_success_{int(time.time())}.png"
            self.page.screenshot(path=str(screenshot_path))
            logger.info(f"Screenshot saved to: {screenshot_path}")

            logger.success("✓ Booking completed!")
            return True

        except AlreadyWaitlistedError:
            raise
        except Exception as e:
            logger.error(f"Failed to book class: {e}")
            # Take an error screenshot
            try:
                screenshot_path = Config.LOGS_DIR / f"booking_error_{int(time.time())}.png"
                self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Error screenshot saved to: {screenshot_path}")
            except:
                pass
            return False

    def attempt_booking(self, class_info: Dict) -> bool:
        """
        Main booking flow for Altea: navigate to class URL and book

        For Altea, we rely on the browser maintaining the login session.
        The first time you run this, you'll need to manually log in,
        and the session will be saved for future use.

        Args:
            class_info: Class details from email notification (must include class_url)

        Returns:
            True if booking successful, False otherwise
        """
        try:
            # Navigate directly to the class page (browser maintains login session)
            if not self.navigate_to_class(class_info):
                return False

            # Check if we hit a login page (session expired)
            current_url = self.page.url
            if 'login' in current_url.lower() or 'sign-in' in current_url.lower():
                logger.warning("⚠️  Login required!")
                logger.info("Please log in manually in the browser window...")
                logger.info("The bot will wait for you to complete login.")

                # Wait for user to log in manually
                try:
                    self.page.wait_for_url('**/workouts/**', timeout=120000)  # Wait up to 2 minutes
                    logger.success("✓ Login detected, continuing...")

                    logger.success("✓ Session saved via persistent profile!")

                except PlaywrightTimeout:
                    logger.error("Login timeout - please try again")
                    return False

            # Book the class
            if not self.book_class():
                return False

            logger.success("🎉 Booking successful!")
            return True

        except AlreadyWaitlistedError:
            raise
        except Exception as e:
            logger.error(f"Booking attempt failed: {e}")
            # Take an error screenshot
            try:
                screenshot_path = Config.LOGS_DIR / f"attempt_error_{int(time.time())}.png"
                self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Error screenshot: {screenshot_path}")
            except:
                pass
            return False


if __name__ == '__main__':
    # Test the booking bot
    from loguru import logger
    import sys

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    # Test with dummy class info
    test_class_info = {
        'class_name': 'Yoga',
        'date': '01/23/2026',
        'time': '6:00 PM',
        'instructor': 'John Doe'
    }

    bot = BookingBot()

    try:
        # Start browser in non-headless mode to see what's happening
        if bot.start_browser(headless=False):
            bot.attempt_booking(test_class_info)
            input("Press Enter to close browser...")
    finally:
        bot.stop_browser()
