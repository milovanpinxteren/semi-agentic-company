"""
Email logging utility for sending notifications
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional


class EmailLogger:
    """Handles email notifications for bot events"""
    
    def __init__(self, config: dict):
        self.enabled = config.get('enabled', False)
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender_email = config.get('sender_email')
        self.sender_password = config.get('sender_password')
        self.recipient_email = config.get('recipient_email')
        self.notify_on = config.get('notify_on', ['error'])
        self.subject_prefix = config.get('subject_prefix', '[Bot]')
        self.logger = logging.getLogger(__name__)
        
    def send_email(self, subject: str, body: str, level: str = 'info') -> bool:
        """
        Send an email notification
        
        Args:
            subject: Email subject
            body: Email body
            level: Notification level (error, warning, info, success)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            self.logger.debug("Email logging disabled, skipping email")
            return False
            
        if level not in self.notify_on:
            self.logger.debug(f"Level '{level}' not in notify_on list, skipping email")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f"{self.subject_prefix} {subject}"
            
            # Add timestamp and level to body
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_body = f"Time: {timestamp}\nLevel: {level.upper()}\n\n{body}"
            
            msg.attach(MIMEText(full_body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def notify_error(self, bot_name: str, error: Exception):
        """Send error notification"""
        subject = f"ERROR: {bot_name} Failed"
        body = f"Bot: {bot_name}\n\nError:\n{str(error)}\n\nType: {type(error).__name__}"
        self.send_email(subject, body, level='error')
    
    def notify_success(self, bot_name: str, message: str):
        """Send success notification"""
        subject = f"SUCCESS: {bot_name} Completed"
        body = f"Bot: {bot_name}\n\n{message}"
        self.send_email(subject, body, level='success')
    
    def notify_warning(self, bot_name: str, message: str):
        """Send warning notification"""
        subject = f"WARNING: {bot_name}"
        body = f"Bot: {bot_name}\n\n{message}"
        self.send_email(subject, body, level='warning')
    
    def notify_info(self, bot_name: str, message: str):
        """Send info notification"""
        subject = f"INFO: {bot_name}"
        body = f"Bot: {bot_name}\n\n{message}"
        self.send_email(subject, body, level='info')
    
    def notify_update_available(self):
        """Notify when git updates are detected"""
        subject = "Code Update Detected"
        body = "New code detected in repository. System will restart shortly."
        self.send_email(subject, body, level='info')
    
    def notify_restart(self):
        """Notify when system restarts"""
        subject = "System Restarted"
        body = "Scheduler has been restarted with updated code."
        self.send_email(subject, body, level='info')
