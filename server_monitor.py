import os
import subprocess
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from logger import LogManager

load_dotenv()

class ServerMonitor:
    def __init__(self):
        self.server_url = os.getenv('SERVER_URL', 'http://127.0.0.1:8008/health')
        self.server_dir = "/Users/bsampera/Documents/projects/ai-backend"
        self.venv_path = os.path.join(self.server_dir, ".venv")
        self.uvicorn_path = os.path.join(self.venv_path, "bin", "uvicorn")
        self.logger = LogManager()

    def check_server_health(self):
        try:
            # Checks every hour
            response = requests.get(self.server_url, timeout=3600) 
            if response.status_code == 200:
                self.logger.log_cron_job("UP", "SUCCESS")
                return True
            else:
                self.logger.log_cron_job("DOWN", f"Status code: {response.status_code}")
                return False
        except requests.RequestException as e:
            self.logger.log_cron_job("DOWN", str(e))
            return False

    def start_server(self):
        try:
            # Verify that uvicorn exists in the virtual environment
            if not os.path.exists(self.uvicorn_path):
                self.logger.log_cron_job("ERROR", f"Uvicorn not found at {self.uvicorn_path}")
                return False

            self.logger.log_cron_job("STARTING", f"Starting server in {self.server_dir}")
            
            # Use the virtual environment's uvicorn directly
            process = subprocess.Popen(
                [self.uvicorn_path, "main:app", "--reload", "--port", "8008"],
                cwd=self.server_dir,
                text=True,
                env={
                    **os.environ,
                    "PATH": f"{os.path.join(self.venv_path, 'bin')}:{os.environ.get('PATH', '')}",
                    "VIRTUAL_ENV": self.venv_path,
                    "PYTHONPATH": self.server_dir
                }
            )
            
            # Wait a moment to see if the process starts successfully
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated
                # Since stdout/stderr are no longer piped, we can't read them here.
                # The error messages would have been printed directly to the console.
                error_msg = f"Process terminated with code {process.returncode}."
                self.logger.log_cron_job("ERROR", error_msg)
                return False
            
            # Process is running, now wait for server to be available
            self.logger.log_cron_job("STARTING", "SUCCESS")
            
            # Wait for server to become available (up to 30 seconds)
            for _ in range(2):  # 6 attempts with 5 second intervals
                time.sleep(5)
                if self.check_server_health():
                    self.logger.log_cron_job("STARTED", "SUCCESS")
                    return True
            
            self.logger.log_cron_job("ERROR", "Server process started but health check failed after 30 seconds")
            return False
        except Exception as e:
            self.logger.log_cron_job("ERROR", f"Failed to start server: {str(e)}")
            return False

    def ensure_server_running(self):
        if not self.check_server_health():
            self.logger.log_cron_job("ATTEMPTING_START", "Server is down, attempting to start")
            return self.start_server()
        return True 