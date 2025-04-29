import os
from datetime import datetime
from loguru import logger
import json

class LogManager:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        # Remove any existing handlers to prevent duplication
        logger.remove()
        self._setup_logging()

    def _setup_logging(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Create today's log directory
        today = datetime.now().strftime("%Y-%m-%d")
        today_log_dir = os.path.join(self.log_dir, today)
        if not os.path.exists(today_log_dir):
            os.makedirs(today_log_dir)

        # Configure cron job logger with a more readable format
        logger.add(
            os.path.join(today_log_dir, "cron.log"),
            rotation="00:00",  # Create new file at midnight
            retention="7 days",  # Keep logs for 7 days
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
            level="INFO",
            enqueue=True,  # Thread-safe logging
            serialize=False  # Don't serialize the message
        )

        # # Configure server health logger with the same format
        # logger.add(
        #     os.path.join(today_log_dir, "server_health.log"),
        #     rotation="00:00",
        #     retention="7 days",
        #     format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        #     level="INFO",
        #     enqueue=True,
        #     serialize=False
        # )

    def log_cron_job(self, job_name, status=None, response=None, error=None):
        # Create a more readable log message
        status_color = "🟢" if status == 200 or status == 201 or status == 202 or status == "SUCCESS" else "🔴"
        message = f"{status_color} Job: {job_name} | Status: {status}"
        
        if response:
            message += f" | Response: {json.dumps(response, indent=4)}"
        if error:
            message += f" | Error: {error}"
            
        logger.info(message)

    def log_server_health(self, status, error=None):
        # Create a more readable log message
        status_icon = "🟢" if status == "UP" else "🔴"
        message = f"{status_icon} Server Status: {status}"
        
        if error:
            message += f" | Error: {error}"
            
        logger.info(message)

    def get_today_logs(self, log_type="cron"):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, today, f"{log_type}.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return f.readlines()
        return []

    def get_logs_by_date(self, date, log_type="cron"):
        log_file = os.path.join(self.log_dir, date, f"{log_type}.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return f.readlines()
        return [] 