"""
Main Scheduler - Orchestrates all bots and auto-updates

This is the main entry point for the semi-agentic company scheduler.
It manages:
- Auto git pulls and restarts
- Scheduling of all bots
- Email notifications
- Human-like behavior patterns
"""
import os
import sys
import logging
import yaml
import time
from logging.handlers import RotatingFileHandler

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.schedule_manager import ScheduleManager
from utils.git_updater import GitUpdater
from utils.humanizer import Humanizer
from utils.email_logger import EmailLogger

# Import bot modules
from bots.linkedin_likebot.bot import run_linkedin_bot
from bots.linkedin_follower_messagebot.bot import run_follower_message_bot


class MainScheduler:
    """Main scheduler that orchestrates all bots and services"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.config = self.load_config()
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.email_logger = EmailLogger(self.config.get('email', {}))
        self.humanizer = Humanizer(self.config.get('office_hours', {}))
        self.git_updater = GitUpdater(self.config.get('git', {}), self.email_logger)
        
        # Get timezone from office hours config
        timezone = self.config.get('office_hours', {}).get('timezone', 'UTC')
        self.schedule_manager = ScheduleManager(timezone)
        
        self.logger.info("=" * 60)
        self.logger.info("Semi-Agentic Company Scheduler Starting")
        self.logger.info("=" * 60)
        
        # Log current git commit if available
        commit = self.git_updater.get_current_commit()
        if commit:
            self.logger.info(f"Current commit: {commit}")
    
    def load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_config.get('file_path', 'logs/scheduler.log'))
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_config.get('console_level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()  # Console output
            ]
        )
        
        # Add file handler if enabled
        if log_config.get('file_enabled', True):
            file_handler = RotatingFileHandler(
                log_config.get('file_path', 'logs/scheduler.log'),
                maxBytes=log_config.get('max_log_size_mb', 10) * 1024 * 1024,
                backupCount=log_config.get('backup_count', 5)
            )
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logging.getLogger().addHandler(file_handler)
    
    def schedule_git_updates(self):
        """Schedule automatic git update checks"""
        if not self.git_updater.enabled:
            self.logger.info("Git auto-update disabled")
            return
        
        interval = self.config['git'].get('check_interval_minutes', 5)
        
        self.schedule_manager.add_interval_job(
            func=self.check_and_update,
            job_id='git_updater',
            interval_minutes=interval
        )
        
        self.logger.info(f"Scheduled git update checks every {interval} minutes")
    
    def check_and_update(self):
        """Check for git updates and restart if needed"""
        self.logger.debug("Checking for git updates...")
        self.git_updater.update_and_restart_if_needed()
    
    def schedule_bots(self):
        """Schedule all configured bots"""
        bots_config = self.config.get('bots', {})
        
        for bot_name, bot_config in bots_config.items():
            if not bot_config.get('enabled', False):
                self.logger.info(f"Bot '{bot_name}' is disabled, skipping")
                continue
            
            self.schedule_bot(bot_name, bot_config)
    
    def schedule_bot(self, bot_name: str, bot_config: dict):
        """
        Schedule a single bot based on its configuration
        
        Args:
            bot_name: Name of the bot
            bot_config: Bot configuration dictionary
        """
        schedule_type = bot_config.get('schedule_type', 'daily')
        
        # Map bot names to their run functions
        bot_functions = {
            'linkedin_likebot': run_linkedin_bot,
            'linkedin_follower_messagebot': run_follower_message_bot,  # ADD THIS
            # Add more bots here as you create them
        }
        
        if bot_name not in bot_functions:
            self.logger.error(f"Unknown bot: {bot_name}")
            return
        
        bot_func = bot_functions[bot_name]
        
        # Create wrapper function that passes dependencies to the bot
        def bot_wrapper():
            bot_func(bot_config, self.humanizer, self.email_logger)
        
        # Schedule based on type
        try:
            if schedule_type == 'daily':
                time_window = bot_config.get('time_window', {'start': '09:00', 'end': '17:00'})
                self.schedule_manager.add_daily_job(
                    func=bot_wrapper,
                    job_id=bot_name,
                    time_window=time_window
                )
            
            elif schedule_type == 'weekly':
                day_of_week = bot_config.get('day_of_week', 'monday')
                time = bot_config.get('time', '10:00')
                self.schedule_manager.add_weekly_job(
                    func=bot_wrapper,
                    job_id=bot_name,
                    day_of_week=day_of_week,
                    time=time
                )
            
            elif schedule_type == 'monthly':
                day_of_month = bot_config.get('day_of_month', 1)
                time = bot_config.get('time', '09:00')
                self.schedule_manager.add_monthly_job(
                    func=bot_wrapper,
                    job_id=bot_name,
                    day_of_month=day_of_month,
                    time=time
                )
            
            elif schedule_type == 'interval':
                # Support both interval_hours and interval_minutes
                interval_hours = bot_config.get('interval_hours')
                interval_minutes = bot_config.get('interval_minutes')

                if interval_hours:
                    interval_minutes = interval_hours * 60
                elif not interval_minutes:
                    interval_minutes = 60  # Default to 1 hour

                # Check if should run immediately on start
                run_on_start = bot_config.get('run_on_start', False)

                self.schedule_manager.add_interval_job(
                    func=bot_wrapper,
                    job_id=bot_name,
                    interval_minutes=interval_minutes,
                    run_immediately=run_on_start
                )

            else:
                self.logger.error(f"Unknown schedule type for {bot_name}: {schedule_type}")
                return

            self.logger.info(f"Scheduled bot: {bot_name} ({schedule_type})")

        except Exception as e:
            self.logger.error(f"Failed to schedule bot {bot_name}: {e}")

    def start(self):
        """Start the scheduler"""
        try:
            # Schedule git updates
            self.schedule_git_updates()

            # Schedule all bots
            self.schedule_bots()

            # Start the scheduler
            self.schedule_manager.start()

            # Print scheduled jobs
            self.schedule_manager.print_jobs()

            self.logger.info("Scheduler is running. Press Ctrl+C to exit.")

            # Send startup email
            if self.email_logger.enabled:
                self.email_logger.notify_info(
                    'Scheduler',
                    f"Scheduler started successfully with {len(self.schedule_manager.get_jobs())} jobs"
                )

            # Keep the script running
            try:
                while True:
                    time.sleep(60)
            except (KeyboardInterrupt, SystemExit):
                self.logger.info("Shutdown signal received")
                self.shutdown()

        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            if self.email_logger:
                self.email_logger.notify_error('Scheduler', e)
            sys.exit(1)

    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        self.logger.info("Shutting down scheduler...")
        self.schedule_manager.shutdown()
        self.logger.info("Scheduler stopped")


def main():
    """Main entry point"""
    scheduler = MainScheduler()
    scheduler.start()


if __name__ == '__main__':
    main()