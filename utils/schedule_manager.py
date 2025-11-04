"""
Schedule manager - wraps APScheduler for managing bot schedules
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging
import pytz


class ScheduleManager:
    """Manages scheduling of bot jobs with different patterns"""
    
    def __init__(self, timezone: str = 'UTC'):
        self.timezone = pytz.timezone(timezone)
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.logger = logging.getLogger(__name__)
        self.jobs = {}
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        self.logger.info("Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        self.logger.info("Scheduler stopped")
    
    def add_daily_job(self, func, job_id: str, time_window: dict, **kwargs):
        """
        Add a job that runs once per day within a time window
        
        Args:
            func: Function to execute
            job_id: Unique job identifier
            time_window: Dict with 'start' and 'end' times (HH:MM format)
            **kwargs: Additional arguments for the job
        """
        # Parse time window
        start_time = time_window.get('start', '09:00')
        end_time = time_window.get('end', '17:00')
        
        # Calculate a random time within the window for first run
        from utils.humanizer import Humanizer
        humanizer = Humanizer({
            'enabled': False,
            'timezone': str(self.timezone)  # Pass the scheduler's timezone
        })
        next_run = humanizer.random_time_in_window(start_time, end_time)
        
        # If the random time has already passed today, schedule for tomorrow
        if next_run < datetime.now(self.timezone):
            next_run += timedelta(days=1)
        
        # Add job to run at the calculated time, then every 24 hours
        job = self.scheduler.add_job(
            func,
            trigger='interval',
            days=1,
            start_date=next_run,
            id=job_id,
            name=f"Daily job: {job_id}",
            **kwargs
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Added daily job '{job_id}' - next run: {next_run}")
        return job
    
    def add_weekly_job(self, func, job_id: str, day_of_week: str, time: str, **kwargs):
        """
        Add a job that runs once per week on a specific day
        
        Args:
            func: Function to execute
            job_id: Unique job identifier
            day_of_week: Day name (monday, tuesday, etc.)
            time: Time to run (HH:MM format)
            **kwargs: Additional arguments for the job
        """
        # Parse time
        hour, minute = map(int, time.split(':'))
        
        # Map day names to APScheduler format
        day_map = {
            'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
            'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'
        }
        
        day = day_map.get(day_of_week.lower(), 'mon')
        
        # Create cron trigger
        trigger = CronTrigger(
            day_of_week=day,
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )
        
        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=f"Weekly job: {job_id} ({day_of_week})",
            **kwargs
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Added weekly job '{job_id}' - {day_of_week} at {time}")
        return job
    
    def add_monthly_job(self, func, job_id: str, day_of_month: int, time: str, **kwargs):
        """
        Add a job that runs once per month on a specific day
        
        Args:
            func: Function to execute
            job_id: Unique job identifier
            day_of_month: Day of the month (1-31)
            time: Time to run (HH:MM format)
            **kwargs: Additional arguments for the job
        """
        # Parse time
        hour, minute = map(int, time.split(':'))
        
        # Create cron trigger
        trigger = CronTrigger(
            day=day_of_month,
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )
        
        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=f"Monthly job: {job_id} (day {day_of_month})",
            **kwargs
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Added monthly job '{job_id}' - day {day_of_month} at {time}")
        return job
    
    def add_interval_job(self, func, job_id: str, interval_minutes: int, run_immediately: bool = False, **kwargs):
        """
        Add a job that runs at fixed intervals

        Args:
            func: Function to execute
            job_id: Unique job identifier
            interval_minutes: Interval in minutes
            run_immediately: If True, run the job immediately, then at intervals
            **kwargs: Additional arguments for the job
        """
        from datetime import datetime, timedelta

        # Schedule interval job - if run_immediately, set next run to now + 1 second
        if run_immediately:
            next_run = datetime.now(self.timezone) + timedelta(seconds=1)
        else:
            next_run = None  # Will start after first interval

        trigger = IntervalTrigger(
            minutes=interval_minutes,
            timezone=self.timezone,
            start_date=next_run
        )

        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=f"Interval job: {job_id} (every {interval_minutes} min)",
            next_run_time=next_run,  # Force immediate execution
            **kwargs
        )

        self.jobs[job_id] = job
        if run_immediately:
            self.logger.info(f"Added interval job '{job_id}' - every {interval_minutes} minutes (starting immediately)")
        else:
            self.logger.info(f"Added interval job '{job_id}' - every {interval_minutes} minutes")
        return job

    def remove_job(self, job_id: str):
        """Remove a job by ID"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            self.logger.info(f"Removed job '{job_id}'")

    def get_jobs(self) -> list:
        """Get list of all scheduled jobs"""
        return self.scheduler.get_jobs()

    def print_jobs(self):
        """Print all scheduled jobs"""
        jobs = self.get_jobs()
        if not jobs:
            self.logger.info("No jobs scheduled")
            return

        self.logger.info(f"Scheduled jobs ({len(jobs)}):")
        for job in jobs:
            self.logger.info(f"  - {job.name} (next run: {job.next_run_time})")