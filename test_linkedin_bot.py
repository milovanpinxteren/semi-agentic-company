"""
Test script to run LinkedIn bot immediately (for testing purposes)
"""
import sys
import os
import logging
import yaml

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.humanizer import Humanizer
from utils.email_logger import EmailLogger
from bots.linkedin_likebot.bot import run_linkedin_bot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize components
email_logger = EmailLogger(config.get('email', {}))
humanizer = Humanizer(config.get('office_hours', {}))
bot_config = config.get('bots', {}).get('linkedin_likebot', {})

# Disable office hours check for testing
humanizer.office_hours_enabled = False

# Disable the initial random delay for testing
bot_config['random_delay_minutes'] = {'min': 0, 'max': 0}

logger.info("=" * 60)
logger.info("TESTING LINKEDIN BOT - Running immediately")
logger.info("=" * 60)

# Run the bot
run_linkedin_bot(bot_config, humanizer, email_logger)

logger.info("=" * 60)
logger.info("Test completed!")
logger.info("=" * 60)