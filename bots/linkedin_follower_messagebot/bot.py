"""
LinkedIn Follower Message Bot

Checks company page followers and messages new ones
Uses LinkedIn's message history to avoid duplicates (no database needed)
"""

import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class LinkedInFollowerMessageBot:
    """
    Bot that messages new company page followers on LinkedIn
    """

    def __init__(self, config, humanizer, email_logger):
        """
        Initialize the follower message bot

        Args:
            config: Bot configuration dictionary
            humanizer: Humanizer instance for delays
            email_logger: Email logger for notifications
        """
        self.config = config
        self.humanizer = humanizer
        self.email_logger = email_logger
        self.logger = logging.getLogger(__name__)

        self.driver = None
        self.stats = {
            'followers_checked': 0,
            'messages_sent': 0,
            'already_messaged': 0,
            'errors': 0,
            'messaged_profiles': []
        }

    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        self.logger.info("Setting up Chrome driver...")

        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        chrome_options.add_argument('--virtual-time-budget=10000')  # Limit rendering time
        chrome_options.add_argument('--run-all-compositor-stages-before-draw')
        chrome_options.add_argument('--disable-gpu-compositing')
        chrome_options.add_argument('--software-rasterizer')

        # Add user agent to look more human
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Use Chrome that's already installed (same as Like Bot)
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()

        self.logger.info("Chrome driver setup complete")

    def login(self):
        """Login to LinkedIn"""
        self.logger.info("Logging into LinkedIn...")

        try:
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(self.humanizer.random_action_delay())

            # Enter credentials
            email_field = self.driver.find_element(By.ID, 'username')
            email_field.send_keys(self.config['linkedin_credentials']['email'])

            time.sleep(self.humanizer.random_action_delay())

            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.config['linkedin_credentials']['password'])

            time.sleep(self.humanizer.random_action_delay())

            # Click login
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()

            time.sleep(3)  # Wait for login to complete

            self.logger.info("Login successful")

        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise

    def get_recent_followers(self):
        """
        Navigate to company followers page and get recent follower profile URLs

        Returns:
            list: List of follower profile URLs
        """
        self.logger.info("Fetching recent followers...")

        try:
            # Navigate to company followers page
            followers_url = self.config['company_followers_url']
            self.driver.get(followers_url)
            time.sleep(5)  # Wait for page to load

            # Wait for follower list to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/in/"]'))
            )

            # Find all profile links
            # LinkedIn shows followers with links like: /in/username/
            profile_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')

            # Extract unique profile URLs
            profile_urls = []
            seen_urls = set()

            for element in profile_elements:
                url = element.get_attribute('href')
                if url and '/in/' in url and url not in seen_urls:
                    # Clean URL (remove query parameters)
                    clean_url = url.split('?')[0]
                    if clean_url.endswith('/'):
                        clean_url = clean_url[:-1]

                    profile_urls.append(clean_url)
                    seen_urls.add(clean_url)

                    # Limit to 10 most recent
                    if len(profile_urls) >= 10:
                        break

            self.logger.info(f"Found {len(profile_urls)} recent followers")
            return profile_urls

        except Exception as e:
            self.logger.error(f"Failed to get followers: {e}")
            return []

    def check_if_already_messaged(self, profile_url):
        """
        Check if we already have a message conversation with this person

        Args:
            profile_url: LinkedIn profile URL

        Returns:
            bool: True if already messaged, False if not
        """
        try:
            # Navigate to profile
            self.driver.get(profile_url)
            time.sleep(3)  # Wait for profile to load

            # Find and click "Message" button
            # Try multiple selectors as LinkedIn UI changes
            message_button = None
            selectors = [
                '//button[contains(@aria-label, "bericht sturen")]',
                '//button[.//span[contains(text(), "Message")]]',
                '//button[contains(@aria-label, "Message")]',
                '//button[contains(@class, "artdeco-button")]//span[contains(text(), "Bericht") or contains(text(), "Message")]/..'
            ]

            for selector in selectors:
                try:
                    message_button = self.driver.find_element(By.XPATH, selector)
                    break
                except NoSuchElementException:
                    continue

            if not message_button:
                self.logger.warning(f"Message button not found for {profile_url}")
                return True  # Assume messaged to be safe

            self.driver.execute_script("arguments[0].scrollIntoView(true);", message_button)
            time.sleep(1)

            try:
                # Wait until button is clickable
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(message_button)
                )
                message_button.click()
            except:
                # Fallback: JavaScript click
                self.driver.execute_script("arguments[0].click();", message_button)

            time.sleep(3)

            # Check if there's existing conversation history
            # LinkedIn shows previous messages in the conversation thread
            conversation_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                '.msg-s-message-list-content, .msg-s-event-listitem, [class*="message-list"]'
            )

            if conversation_elements:
                # Found message history - already messaged
                self.logger.debug(f"Existing conversation found for {profile_url}")
                return True
            else:
                # No message history - new conversation
                self.logger.debug(f"No previous messages for {profile_url}")
                return False

        except Exception as e:
            self.logger.error(f"Error checking message status for {profile_url}: {e}")
            return True  # Assume messaged to be safe on error

    def send_message(self, profile_url, message_text):
        """
        Send a message to a LinkedIn profile

        Args:
            profile_url: LinkedIn profile URL
            message_text: Message text to send

        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Find message box
            # Try multiple selectors
            message_box = None
            selectors = [
                'div[role="textbox"]',
                '.msg-form__contenteditable',
                '[data-control-name="message_compose"]'
            ]

            for selector in selectors:
                try:
                    message_box = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not message_box:
                self.logger.error("Could not find message box")
                return False

            # Get first name from profile URL for personalization
            # Extract name from URL: /in/firstname-lastname/
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, 'a.msg-compose__profile-link')
                full_name = name_element.text.strip()
                first_name = full_name.split()[0]  # Get first word as first name
                self.logger.debug(f"Extracted name: {full_name} (first: {first_name})")
            except:
                # Fallback to URL if name element not found
                name_part = profile_url.split('/in/')[-1].replace('/', '')
                first_name = name_part.split('-')[0].capitalize()
                self.logger.warning(f"Could not find name element, using URL: {first_name}")

            # Format message with first name
            formatted_message = message_text.replace('{first_name}', first_name)

            # Type message with human-like delay
            message_box.click()
            time.sleep(0.5)
            message_box.send_keys(formatted_message)

            time.sleep(self.humanizer.random_action_delay())

            # Find and click Send button
            send_button = None
            # Find and click Send button
            try:
                send_button = self.driver.find_element(By.CSS_SELECTOR, 'button.msg-form__send-btn')
                send_button.click()
            except NoSuchElementException:
                self.logger.error("Could not find Send button")
                return False

            send_button.click()
            time.sleep(2)  # Wait for message to send

            self.logger.info(f"Message sent to {profile_url}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send message to {profile_url}: {e}")
            return False

    def close_message_window(self):
        """Close the message window"""
        try:
            close_button = self.driver.find_element(
                By.CSS_SELECTOR,
                'button.msg-overlay-bubble-header__control[class*="artdeco-button--circle"] svg[data-test-icon="close-small"]'
            )
            # Click parent button
            close_button.find_element(By.XPATH, '..').click()
            time.sleep(1)
            self.logger.debug("Closed message window")
        except:
            self.logger.warning("Could not close message window")

    def process_followers(self):
        """
        Main processing loop - check followers and message new ones
        """
        self.logger.info("Starting follower processing...")

        # Get recent followers
        followers = self.get_recent_followers()
        self.stats['followers_checked'] = len(followers)

        if not followers:
            self.logger.warning("No followers found")
            return

        # Get message template
        message_template = self.config.get('message_template', '')
        if not message_template:
            self.logger.error("No message template configured")
            return

        # Get max messages limit
        max_messages = self.config.get('max_messages_per_run', 5)
        messages_sent_count = 0

        # Process each follower
        for idx, profile_url in enumerate(followers, 1):
            self.logger.info(f"Processing follower {idx}/{len(followers)}: {profile_url}")

            try:
                # Check if we already messaged this person
                already_messaged = self.check_if_already_messaged(profile_url)

                if already_messaged:
                    self.logger.info(f"Already messaged {profile_url}, skipping")
                    self.stats['already_messaged'] += 1
                    self.close_message_window()
                else:
                    # Check if we've hit the max messages limit
                    if messages_sent_count >= max_messages:
                        self.logger.info(f"Reached max messages limit ({max_messages}), stopping")
                        break

                    # Send message
                    success = self.send_message(profile_url, message_template)

                    if success:
                        self.stats['messages_sent'] += 1
                        self.stats['messaged_profiles'].append(profile_url)
                        messages_sent_count += 1
                        self.logger.info(f"Successfully messaged {profile_url}")
                    else:
                        self.stats['errors'] += 1
                        self.logger.error(f"Failed to message {profile_url}")
                    self.close_message_window()

                # Random delay between followers (2-5 minutes)
                if idx < len(followers):  # Don't delay after last follower
                    self.humanizer.wait_random(2, 5)

            except Exception as e:
                self.logger.error(f"Error processing {profile_url}: {e}")
                self.stats['errors'] += 1
                continue

        self.logger.info("Follower processing complete")

    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up...")
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def run(self):
        """
        Main entry point for the bot
        """
        start_time = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info("LinkedIn Follower Message Bot - Starting")
        self.logger.info("=" * 60)

        try:
            # Setup
            self.setup_driver()
            self.login()

            # Wait before starting (use config random_delay_minutes)
            # delay_config = self.config.get('random_delay_minutes', {'min': 10, 'max': 35})
            # self.logger.info(f"Waiting {delay_config['min']}-{delay_config['max']} minutes before starting...")
            # self.humanizer.wait_random(delay_config['min'], delay_config['max'])

            # Process followers
            self.process_followers()

            # Calculate duration
            end_time = datetime.now()
            duration = end_time - start_time

            # Send success email
            self.send_summary_email(duration)

        except Exception as e:
            self.logger.error(f"Bot execution failed: {e}", exc_info=True)
            self.email_logger.notify_error('LinkedIn Follower Message Bot', e)

        finally:
            self.cleanup()
            self.logger.info("Bot execution complete")

    def send_summary_email(self, duration):
        """
        Send email summary of bot execution

        Args:
            duration: Execution duration (timedelta)
        """
        # Format messaged profiles list
        messaged_list = "\n".join([
            f"{idx}. {url}"
            for idx, url in enumerate(self.stats['messaged_profiles'], 1)
        ]) if self.stats['messaged_profiles'] else "None"

        message = f"""LinkedIn Follower Message Bot - Daily Report

Run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Summary:
- Followers checked: {self.stats['followers_checked']}
- New messages sent: {self.stats['messages_sent']}
- Already messaged (skipped): {self.stats['already_messaged']}
- Errors: {self.stats['errors']}

✉️ Messaged:
{messaged_list}

Duration: {duration.seconds // 60} minutes {duration.seconds % 60} seconds
"""

        self.email_logger.notify_success('LinkedIn Follower Message Bot', message)
        self.logger.info("Summary email sent")


# Function that will be called by the scheduler
def run_follower_message_bot(config, humanizer, email_logger):
    """
    Entry point for the scheduler to run the follower message bot

    Args:
        config: Bot configuration dictionary
        humanizer: Humanizer instance
        email_logger: EmailLogger instance
    """
    bot = LinkedInFollowerMessageBot(config, humanizer, email_logger)
    bot.run()
