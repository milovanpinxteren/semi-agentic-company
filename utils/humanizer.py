"""
Humanizer utility - adds random delays and human-like behavior patterns
"""
import random
import time
from datetime import datetime, time as dt_time
import pytz
import logging


class Humanizer:
    """Utilities for making bot behavior appear more human"""
    
    def __init__(self, config: dict):
        self.office_hours_enabled = config.get('enabled', False)
        self.timezone = pytz.timezone(config.get('timezone', 'UTC'))
        self.start_hour = config.get('start_hour', 9)
        self.end_hour = config.get('end_hour', 17)
        self.weekdays_only = config.get('weekdays_only', True)
        self.logger = logging.getLogger(__name__)
    
    def random_delay(self, min_minutes: int, max_minutes: int) -> int:
        """
        Generate a random delay in seconds
        
        Args:
            min_minutes: Minimum delay in minutes
            max_minutes: Maximum delay in minutes
            
        Returns:
            int: Random delay in seconds
        """
        delay_seconds = random.randint(min_minutes * 60, max_minutes * 60)
        return delay_seconds
    
    def wait_random(self, min_minutes: int, max_minutes: int):
        """
        Wait for a random amount of time
        
        Args:
            min_minutes: Minimum wait time in minutes
            max_minutes: Maximum wait time in minutes
        """
        delay = self.random_delay(min_minutes, max_minutes)
        self.logger.info(f"Waiting {delay // 60} minutes ({delay} seconds)...")
        time.sleep(delay)
    
    def is_office_hours(self) -> bool:
        """
        Check if current time is within office hours
        
        Returns:
            bool: True if within office hours, False otherwise
        """
        if not self.office_hours_enabled:
            return True
        
        now = datetime.now(self.timezone)
        
        # Check if weekday
        if self.weekdays_only and now.weekday() >= 5:  # 5=Saturday, 6=Sunday
            self.logger.debug("Outside office hours: Weekend")
            return False
        
        # Check if within hour range
        if not (self.start_hour <= now.hour < self.end_hour):
            self.logger.debug(f"Outside office hours: {now.hour}:00 not between {self.start_hour}:00-{self.end_hour}:00")
            return False
        
        return True
    
    def wait_until_office_hours(self):
        """
        Wait until we're within office hours
        Will sleep and check periodically
        """
        if not self.office_hours_enabled:
            return
        
        while not self.is_office_hours():
            self.logger.info("Outside office hours, waiting...")
            time.sleep(300)  # Check every 5 minutes
    
    def random_time_in_window(self, start_time: str, end_time: str) -> datetime:
        """
        Generate a random time within a given window
        
        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            
        Returns:
            datetime: Random datetime within the window (today)
        """
        now = datetime.now(self.timezone)
        
        # Parse start and end times
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        
        # Convert to minutes since midnight
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        
        # Generate random time
        random_minutes = random.randint(start_minutes, end_minutes)
        random_hour = random_minutes // 60
        random_minute = random_minutes % 60
        
        # Create datetime for today at random time
        target = now.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
        
        return target
    
    def random_action_delay(self) -> float:
        """
        Random delay between individual actions (e.g., between likes)
        Returns delay in seconds, typically 2-10 seconds
        """
        return random.uniform(2.0, 10.0)
    
    def should_take_break(self, actions_count: int, break_threshold: int = 10) -> bool:
        """
        Determine if bot should take a break after certain actions
        
        Args:
            actions_count: Number of actions performed so far
            break_threshold: Take break after this many actions
            
        Returns:
            bool: True if should take break
        """
        if actions_count > 0 and actions_count % break_threshold == 0:
            return True
        return False
    
    def take_break(self):
        """Take a longer break (1-3 minutes) to appear more human"""
        break_time = random.randint(60, 180)  # 1-3 minutes
        self.logger.info(f"Taking a break for {break_time} seconds...")
        time.sleep(break_time)
