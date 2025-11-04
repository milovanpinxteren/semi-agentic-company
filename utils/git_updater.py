"""
Git updater utility - automatically pulls updates from repository
"""
import git
import logging
import os
import sys
from typing import Optional


class GitUpdater:
    """Handles automatic git pull and restart logic"""
    
    def __init__(self, config: dict, email_logger=None):
        self.enabled = config.get('enabled', False)
        self.branch = config.get('branch', 'main')
        self.email_logger = email_logger
        self.logger = logging.getLogger(__name__)
        
        # Get repository path (current working directory)
        self.repo_path = os.getcwd()
        self.repo: Optional[git.Repo] = None
        
        if self.enabled:
            self._initialize_repo()
    
    def _initialize_repo(self):
        """Initialize git repository object"""
        try:
            self.repo = git.Repo(self.repo_path)
            self.logger.info(f"Git updater initialized for branch: {self.branch}")
        except git.InvalidGitRepositoryError:
            self.logger.error(f"Not a git repository: {self.repo_path}")
            self.enabled = False
        except Exception as e:
            self.logger.error(f"Failed to initialize git repo: {e}")
            self.enabled = False
    
    def check_for_updates(self) -> bool:
        """
        Check if there are updates available in the remote repository
        
        Returns:
            bool: True if updates are available, False otherwise
        """
        if not self.enabled or not self.repo:
            return False
        
        try:
            # Fetch latest changes from remote
            origin = self.repo.remote('origin')
            origin.fetch()
            
            # Get current commit and remote commit
            local_commit = self.repo.head.commit
            remote_commit = origin.refs[self.branch].commit
            
            # Check if there are new commits
            if local_commit != remote_commit:
                self.logger.info(f"Updates available: {local_commit.hexsha[:7]} -> {remote_commit.hexsha[:7]}")
                return True
            else:
                self.logger.debug("No updates available")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return False
    
    def pull_updates(self) -> bool:
        """
        Pull latest updates from remote repository
        
        Returns:
            bool: True if pull was successful, False otherwise
        """
        if not self.enabled or not self.repo:
            return False
        
        try:
            origin = self.repo.remote('origin')
            
            # Check for uncommitted changes
            if self.repo.is_dirty():
                self.logger.warning("Repository has uncommitted changes, stashing...")
                self.repo.git.stash('save', 'Auto-stash before pull')
            
            # Pull latest changes
            pull_info = origin.pull(self.branch)
            
            self.logger.info(f"Successfully pulled updates: {pull_info}")
            
            # Notify via email if configured
            if self.email_logger:
                self.email_logger.notify_update_available()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error pulling updates: {e}")
            
            # Notify via email if configured
            if self.email_logger:
                self.email_logger.notify_error('Git Updater', e)
            
            return False
    
    def restart_scheduler(self):
        """
        Restart the scheduler process to apply updates
        This will exit the current process and let systemd restart it
        """
        self.logger.info("Restarting scheduler to apply updates...")
        
        # Notify via email if configured
        if self.email_logger:
            self.email_logger.notify_restart()
        
        # Exit with code 0 (systemd will restart the service)
        sys.exit(0)
    
    def update_and_restart_if_needed(self) -> bool:
        """
        Check for updates, pull them, and restart if updates were found
        
        Returns:
            bool: True if updates were found and applied, False otherwise
        """
        if not self.enabled:
            return False
        
        if self.check_for_updates():
            self.logger.info("Updates found, pulling...")
            if self.pull_updates():
                self.logger.info("Updates pulled successfully, restarting...")
                self.restart_scheduler()
                return True
        
        return False
    
    def get_current_commit(self) -> Optional[str]:
        """Get current commit hash"""
        if not self.repo:
            return None
        try:
            return self.repo.head.commit.hexsha[:7]
        except Exception:
            return None
