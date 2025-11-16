"""
Test script for LinkedIn Follower Message Bot

Run this to test the bot without waiting for the scheduler.
Usage: python test_follower_bot.py
"""

import os
import sys
import yaml
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from YOUR existing utilities
from utils.humanizer import Humanizer
from utils.email_logger import EmailLogger
from bots.linkedin_follower_messagebot.bot import run_follower_message_bot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("LinkedIn Follower Message Bot - TEST RUN")
    logger.info("=" * 60)

    # Load config
    config = load_config()

    # Check if bot is configured
    if 'linkedin_follower_messagebot' not in config.get('bots', {}):
        logger.error("Bot not configured in config.yaml!")
        logger.error("Please add 'linkedin_follower_messagebot' section to config.yaml")
        sys.exit(1)

    bot_config = config['bots']['linkedin_follower_messagebot']

    # Initialize utilities
    humanizer = Humanizer(config.get('office_hours', {}))
    email_logger = EmailLogger(config.get('email', {}))

    # Check office hours
    if not humanizer.is_office_hours():
        logger.warning("Outside office hours! Bot may not run.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            logger.info("Test cancelled")
            sys.exit(0)

    # Run the bot
    logger.info("Starting bot test run...")
    try:
        run_follower_message_bot(bot_config, humanizer, email_logger)
        logger.info("=" * 60)
        logger.info("Test completed successfully!")
        logger.info("=" * 60)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
