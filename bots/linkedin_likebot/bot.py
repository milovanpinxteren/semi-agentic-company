"""
LinkedIn Like Bot Implementation
Integrated with semi-agentic company framework
"""
import logging
import time
import random
import urllib.parse
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from langdetect import detect
import os
# Import configuration data
from .config_data import KEYWORDS, EXCLUDEWORDS, INTERESTING_PEOPLE


class LinkedInLikeBot:
    """
    Bot that automatically likes posts on LinkedIn
    Integrated with humanizer for delays and email_logger for notifications
    """

    def __init__(self, config: dict, humanizer, email_logger):
        """
        Initialize the LinkedIn Like Bot

        Args:
            config: Bot configuration from config.yaml
            humanizer: Humanizer instance for random delays
            email_logger: EmailLogger instance for notifications
        """
        self.config = config
        self.humanizer = humanizer
        self.email_logger = email_logger
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.max_actions = config.get('max_actions_per_run', 20)
        self.random_delay_config = config.get('random_delay_minutes', {'min': 1, 'max': 10})

        # LinkedIn credentials
        creds = config.get('linkedin_credentials', {})
        self.email = creds.get('email')
        self.password = creds.get('password')
        self.xpath_label = creds.get('xpath_label')

        # Interesting people settings
        people_config = config.get('interesting_people', {})
        self.max_people = people_config.get('max_people_per_run', 25)
        self.max_likes_per_person = people_config.get('max_likes_per_person', 3)

        # Keywords and filters
        self.keywords = KEYWORDS.copy()
        random.shuffle(self.keywords)  # Randomize search order
        self.excludewords = [word.lower() for word in EXCLUDEWORDS]
        self.interesting_people = INTERESTING_PEOPLE.copy()

        # Tracking
        self.liked_count = 0
        self.liked_from_people = 0
        self.liked_from_search = 0
        self.errors = []

        # Driver
        self.driver: Optional[webdriver.Chrome] = None

    def is_relevant(self, post_text: str) -> bool:
        """
        Check if post is relevant (Dutch language, no exclude words)
        """
        try:
            # Add debug logging
            self.logger.info(f"DEBUG: Checking relevance for text: '{post_text[:100]}...'")
            self.logger.info(f"DEBUG: Text length: {len(post_text)}")

            # Check if text is empty or too short
            if not post_text or len(post_text.strip()) < 10:
                self.logger.info("Text too short or empty, skipping")
                return False

            lower_text = post_text.lower()

            # Check for exclude words
            found_words = [word for word in self.excludewords if word in lower_text]
            if found_words:
                self.logger.info(f"Excludeword(s) found: {found_words}")
                return False

            # Check language (Dutch only)
            lang_code = detect(post_text)
            if lang_code != 'nl':
                self.logger.info(f"Post not in Dutch (detected: {lang_code})")
                return False

            return True

        except Exception as e:
            self.logger.info(f"Error in relevance check: {e}")
            self.logger.info(f"DEBUG: Failed text was: '{post_text[:50]}...'")  # Add this line
            return False

    def setup(self):
        """Setup the bot - initialize browser and login"""
        self.logger.info("Setting up LinkedIn Like Bot...")

        # Verify credentials
        if not self.email or not self.password or not self.xpath_label:
            raise ValueError("LinkedIn credentials not configured in config.yaml")

        # Setup Chrome driver - force 64-bit on Windows
        # Setup Chrome driver
        import platform
        if platform.system() == 'Windows':
            # Use manual chromedriver on Windows (webdriver-manager has win32/win64 issues)
            chromedriver_path = os.path.join(os.path.dirname(__file__), '..', '..', 'chromedriver.exe')
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                self.logger.info(f"Using manual ChromeDriver: {chromedriver_path}")
            else:
                self.logger.info(f"ChromeDriver not found at: {chromedriver_path}")
                raise FileNotFoundError(f"Please download chromedriver.exe to: {chromedriver_path}")
        else:
            # Linux/Mac - use automatic download
            service = Service(ChromeDriverManager().install())
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-renderer-backgrounding')

        options.add_argument('--force-device-scale-factor=1')
        options.add_argument('--enable-font-antialiasing')
        options.add_argument('--disable-lcd-text')
        options.add_argument('--enable-accelerated-2d-canvas=false')
        options.add_argument('--disable-gpu-sandbox')

        options.add_experimental_option("detach", False)
        options.page_load_strategy = 'normal'

        options.add_argument('--virtual-time-budget=10000')  # Limit rendering time
        options.add_argument('--run-all-compositor-stages-before-draw')
        options.add_argument('--disable-gpu-compositing')
        options.add_argument('--software-rasterizer')

        self.logger.info("Initializing Chrome driver...")
        self.driver = webdriver.Chrome(service=service, options=options)

        # Login to LinkedIn
        self.login()

    def login(self):
        """Login to LinkedIn"""
        self.logger.info("Logging in to LinkedIn...")

        try:
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(3)

            # Enter credentials
            username_field = self.driver.find_element(By.ID, 'username')
            password_field = self.driver.find_element(By.ID, 'password')

            username_field.send_keys(self.email)
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)

            time.sleep(25)
            self.logger.info("Logged in to LinkedIn")

        except Exception as e:
            self.logger.info(f"Failed to login: {e}")
            raise

    def like_posts_from_interesting_people(self):
        """Visit LinkedIn activity pages of selected people and like recent posts"""
        if not self.interesting_people:
            self.logger.info("⚠️ No INTERESTING_PEOPLE configured")
            return

        # Select random subset of people
        selected_people = random.sample(
            self.interesting_people,
            min(self.max_people, len(self.interesting_people))
        )

        self.logger.info(f"Visiting {len(selected_people)} interesting people...")

        for profile_url in selected_people:
            if self.liked_count >= self.max_actions:
                self.logger.info("Max actions reached, stopping")
                break

            original_window = self.driver.current_window_handle
            person_likes = 0

            try:
                activity_url = profile_url.rstrip("/") + "/recent-activity/all/"
                self.logger.info(f"Visiting: {activity_url}")
                self.driver.get(activity_url)
                time.sleep(self.humanizer.random_action_delay())

                # Scroll to load posts
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Find posts
                posts = self.driver.find_elements(By.CSS_SELECTOR, '[data-view-name="feed-full-update"]')
                self.logger.info(f"Found {len(posts)} posts")

                for post in posts:
                    if person_likes >= self.max_likes_per_person:
                        self.logger.info(f"Max likes per person reached ({self.max_likes_per_person})")
                        break

                    if self.liked_count >= self.max_actions:
                        break

                    try:
                        # Check post age
                        age_element = post.find_element(
                            By.CSS_SELECTOR,
                            'span.update-components-actor__sub-description'
                        )
                        age_text = age_element.text.lower()
                        if any(term in age_text for term in ["maanden geleden", "jaar geleden", "jaren geleden"]):
                            self.logger.info(f"Post too old ({age_text}), skipping user")
                            break
                    except Exception:
                        pass  # Continue if age can't be determined

                    try:
                        # Extract post URN
                        post_div = post.find_element(By.CSS_SELECTOR, 'div.feed-shared-update-v2[data-urn]')
                        urn = post_div.get_attribute("data-urn")

                        if not urn or not urn.startswith("urn:li:activity:"):
                            continue

                        activity_id = urn.split(":")[-1]
                        post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/"

                        # Open post in new tab
                        self.driver.execute_script(f"window.open('{post_url}', '_blank');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(self.humanizer.random_action_delay())

                        # Switch identity and like
                        if self._switch_identity_and_like():
                            self.liked_count += 1
                            self.liked_from_people += 1
                            person_likes += 1
                            self.logger.info(f"👍 Liked post {self.liked_count} from {profile_url}")

                        # Take break if needed
                        if self.humanizer.should_take_break(self.liked_count):
                            self.humanizer.take_break()

                    except Exception as e:
                        self.logger.warning(f"Could not process post: {e}")
                        self.errors.append(f"Post processing error: {str(e)[:100]}")
                    finally:
                        # Close tab and return to original window
                        if len(self.driver.window_handles) > 1:
                            time.sleep(2)
                            self.driver.close()
                            self.driver.switch_to.window(original_window)

            except Exception as e:
                self.logger.info(f"Failed to process {profile_url}: {e}")
                self.errors.append(f"Profile error: {str(e)[:100]}")

    def like_posts_from_search(self):
        """Search for keywords and like relevant posts"""
        self.logger.info(f"Searching for posts with {len(self.keywords)} keywords...")

        for keyword in self.keywords:
            if self.liked_count >= self.max_actions:
                self.logger.info("Max actions reached, stopping")
                break

            try:
                encoded_keyword = urllib.parse.quote(keyword)
                search_url = f'https://www.linkedin.com/search/results/content/?keywords={encoded_keyword}&origin=FACETED_SEARCH&sid=%3B%3BW&sortBy="date_posted"'

                self.logger.info(f"Searching for: {keyword}")
                self.driver.get(search_url)
                time.sleep(self.humanizer.random_action_delay())

                # Scroll to load more posts
                for _ in range(2):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(3, 5))

                # Find posts
                search_posts = self.driver.find_elements(By.CLASS_NAME, 'artdeco-card')
                self.logger.info(f"Found {len(search_posts)} posts for keyword: {keyword}")

                for post in search_posts:
                    if self.liked_count >= self.max_actions:
                        break

                    try:
                        try:
                            # Method 1: Standard text extraction
                            text = post.text
                            self.logger.debug(f"Method 1 - post.text: '{text[:50]}...' (len: {len(text)})")

                            # Method 2: Specific LinkedIn elements
                            if not text or len(text.strip()) < 10:
                                text_elements = post.find_elements(By.CSS_SELECTOR,
                                                                   '.feed-shared-text, .feed-shared-update-v2__description, .attributed-text-segment-list__content')
                                if text_elements:
                                    text = ' '.join([elem.text for elem in text_elements if elem.text])
                                    self.logger.debug(f"Method 2 - CSS selectors: '{text[:50]}...' (len: {len(text)})")

                            # Method 3: More specific selectors
                            if not text or len(text.strip()) < 10:
                                more_selectors = [
                                    'span[dir="ltr"]',
                                    '.break-words span',
                                    '.feed-shared-text__text-view span',
                                    '.attributed-text-segment-list__content span'
                                ]
                                for selector in more_selectors:
                                    elements = post.find_elements(By.CSS_SELECTOR, selector)
                                    if elements:
                                        text = ' '.join([elem.text for elem in elements if elem.text.strip()])
                                        if text.strip():
                                            self.logger.debug(
                                                f"Method 3 - {selector}: '{text[:50]}...' (len: {len(text)})")
                                            break

                            # Method 4: JavaScript extraction
                            if not text or len(text.strip()) < 10:
                                try:
                                    text = self.driver.execute_script("""
                                        const post = arguments[0];
                                        let allText = '';

                                        // Try multiple approaches to get text
                                        const textSelectors = [
                                            '.feed-shared-text span',
                                            'span[dir="ltr"]', 
                                            '.attributed-text-segment-list__content span',
                                            '.break-words'
                                        ];

                                        for (const selector of textSelectors) {
                                            const elements = post.querySelectorAll(selector);
                                            for (const el of elements) {
                                                if (el.textContent && el.textContent.trim() && !el.textContent.includes('Like') && !el.textContent.includes('Comment')) {
                                                    allText += el.textContent.trim() + ' ';
                                                }
                                            }
                                            if (allText.trim()) break;
                                        }

                                        return allText.trim();
                                    """, post)
                                    self.logger.debug(f"Method 4 - JavaScript: '{text[:50]}...' (len: {len(text)})")
                                except Exception as js_error:
                                    self.logger.debug(f"JavaScript extraction failed: {js_error}")

                            # Method 5: Raw textContent with cleaning
                            if not text or len(text.strip()) < 10:
                                raw_text = post.get_attribute('textContent') or ''
                                # Clean out UI elements
                                import re
                                cleaned = re.sub(r'\b(Like|Comment|Share|See more|Show translation)\b', '', raw_text,
                                                 flags=re.IGNORECASE)
                                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                                if len(cleaned) > 20:  # Only use if we got substantial content
                                    text = cleaned
                                    self.logger.debug(
                                        f"Method 5 - cleaned textContent: '{text[:50]}...' (len: {len(text)})")

                            self.logger.debug(f"FINAL extracted text length: {len(text)} characters")

                        except Exception as e:
                            self.logger.warning(f"Error extracting text from post: {e}")
                            text = ""

                        # Check relevance
                        if not self.is_relevant(text):
                            continue

                        self.logger.info(f"✅ Relevant post found: {text.strip()[:50]}...")
                        time.sleep(self.humanizer.random_action_delay())

                        # Switch identity and like
                        if self._switch_identity_and_like_in_feed(post):
                            self.liked_count += 1
                            self.liked_from_search += 1
                            self.logger.info(f"👍 Liked post {self.liked_count} from search")

                        # Take break if needed
                        if self.humanizer.should_take_break(self.liked_count):
                            self.humanizer.take_break()

                    except Exception as e:
                        self.logger.warning(f"Error processing search post: {e}")
                        self.errors.append(f"Search post error: {str(e)[:100]}")
                        continue

            except Exception as e:
                self.logger.info(f"Error searching keyword '{keyword}': {e}")
                self.errors.append(f"Keyword search error: {str(e)[:100]}")

    def _switch_identity_and_like(self) -> bool:
        """
        Switch to company identity and like post (from individual post page)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Click identity toggle
            identity_button = self.driver.find_element(
                By.CLASS_NAME,
                "content-admin-identity-toggle-button"
            )
            identity_button.click()
            time.sleep(1)

            # Select company identity
            label = self.driver.find_element(By.XPATH, self.xpath_label)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", label)
            self.driver.execute_script("arguments[0].click();", label)
            time.sleep(1)

            # Save selection
            self.driver.find_element(
                By.CSS_SELECTOR,
                'button[aria-label="Selectie opslaan"]'
            ).click()
            time.sleep(1)

            # Click like button
            like_button = self.driver.find_element(
                By.CSS_SELECTOR,
                'button[aria-label="Reageren met interessant"]'
            )
            like_button.click()
            time.sleep(random.uniform(1, 3))

            return True

        except Exception as e:
            self.logger.warning(f"Failed to switch identity and like: {e}")
            return False

    def _switch_identity_and_like_in_feed(self, post_element) -> bool:
        """
        Switch to company identity and like post (from search feed)

        Args:
            post_element: Selenium element of the post

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Click identity toggle in feed
            identity_button = post_element.find_element(
                By.CSS_SELECTOR,
                'button[aria-label^="Menu voor schakelen naar een andere identiteit openen"]'
            )
            identity_button.click()
            time.sleep(1)

            # Select company identity
            label = self.driver.find_element(By.XPATH, self.xpath_label)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", label)
            self.driver.execute_script("arguments[0].click();", label)
            time.sleep(2)

            # Save selection
            self.driver.find_element(
                By.CSS_SELECTOR,
                'button[aria-label="Selectie opslaan"]'
            ).click()
            time.sleep(1)

            # Click like button
            like_button = post_element.find_element(
                By.CSS_SELECTOR,
                'button[aria-label="Reageren met interessant"]'
            )
            like_button.click()
            time.sleep(random.uniform(0, 3))

            return True

        except Exception as e:
            self.logger.warning(f"Failed to switch identity and like in feed: {e}")
            return False

    def run(self):
        """
        Main bot execution - called by the scheduler
        """
        self.logger.info("=" * 60)
        self.logger.info("LinkedIn Like Bot Starting")
        self.logger.info("=" * 60)

        try:
            # Wait until office hours
            self.humanizer.wait_until_office_hours()

            # Add initial random delay
            min_delay = self.random_delay_config['min']
            max_delay = self.random_delay_config['max']
            self.humanizer.wait_random(min_delay, max_delay)

            # Setup bot (login)
            self.setup()

            # Like posts from interesting people
            self.logger.info("\nPhase 1: Liking posts from interesting people")
            self.like_posts_from_interesting_people()

            # Search and like posts
            self.logger.info("\nPhase 2: Searching and liking relevant posts")
            self.like_posts_from_search()

            # Cleanup
            self.cleanup()

            # Prepare success message
            success_message = self._prepare_summary_message()

            # Send success notification
            self.email_logger.notify_success('LinkedIn Like Bot', success_message)
            self.logger.info("\n" + "=" * 60)
            self.logger.info("LinkedIn Like Bot Completed Successfully")
            self.logger.info(success_message)
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Error during bot execution: {e}", exc_info=True)

            # Prepare error message with context
            error_message = f"Error: {str(e)}\n\n"
            error_message += f"Likes completed before error: {self.liked_count}\n"
            if self.errors:
                error_message += f"\nPrevious errors: {len(self.errors)}\n"

            self.email_logger.notify_error('LinkedIn Like Bot', Exception(error_message))

            # Try to cleanup even on error
            try:
                self.cleanup()
            except:
                pass

    def _prepare_summary_message(self) -> str:
        """Prepare summary message for email notification"""
        message = f"""Run Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total Likes: {self.liked_count}
   • From interesting people: {self.liked_from_people}
   • From keyword search: {self.liked_from_search}

🎯 Keywords searched: {len(self.keywords)}
👥 People visited: {min(self.max_people, len(self.interesting_people))}
⚙️ Max actions limit: {self.max_actions}
"""

        if self.errors:
            message += f"\n⚠️ Minor errors encountered: {len(self.errors)}\n"
            message += "   (These were handled gracefully)\n"

        return message

    def cleanup(self):
        """Cleanup resources (close browser)"""
        self.logger.info("Cleaning up...")

        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed")
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")


# Function that will be called by the scheduler
def run_linkedin_bot(config, humanizer, email_logger):
    """
    Entry point for the scheduler to run the LinkedIn bot
    """
    bot = LinkedInLikeBot(config, humanizer, email_logger)
    bot.run()
