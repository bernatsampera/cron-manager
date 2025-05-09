import json
import time
import requests
import subprocess
import os
import shutil
import re
from datetime import datetime
from logger import LogManager
from server_monitor import ServerMonitor

class CronParser:
    def __init__(self):
        self.field_names = ['second', 'minute', 'hour', 'day', 'month', 'weekday']
        self.field_ranges = [
            (0, 59),   # seconds
            (0, 59),   # minutes
            (0, 23),   # hours
            (1, 31),   # day of month
            (1, 12),   # month
            (0, 6)     # day of week (0=Sunday)
        ]

    def _parse_field(self, field, field_index):
        """Parse a single cron field into a set of valid values."""
        field = field.strip()
        if field == '*':
            return set(range(self.field_ranges[field_index][0], self.field_ranges[field_index][1] + 1))
        
        values = set()
        for part in field.split(','):
            part = part.strip()
            
            # Handle step values (e.g., */5)
            if '/' in part:
                step_part, step = part.split('/')
                step = int(step)
                if step_part == '*':
                    start = self.field_ranges[field_index][0]
                    end = self.field_ranges[field_index][1]
                else:
                    start = int(step_part)
                    end = self.field_ranges[field_index][1]
                values.update(range(start, end + 1, step))
                continue
            
            # Handle ranges (e.g., 1-5)
            if '-' in part:
                start, end = map(int, part.split('-'))
                values.update(range(start, end + 1))
                continue
            
            # Handle single values
            values.add(int(part))
        
        return values

    def parse(self, expression):
        """Parse a cron expression into a dictionary of valid values for each field."""
        fields = expression.strip().split()
        if len(fields) != 6:
            raise ValueError("Cron expression must have exactly 6 fields (second minute hour day month weekday)")
        
        result = {}
        for i, (field, (field_name, (min_val, max_val))) in enumerate(zip(fields, zip(self.field_names, self.field_ranges))):
            try:
                result[field_name] = self._parse_field(field, i)
            except ValueError as e:
                raise ValueError(f"Invalid value in {field_name} field: {str(e)}")
        
        return result

    def should_run(self, expression, current_time):
        """Check if a job should run at the given time based on its cron expression."""
        try:
            schedule = self.parse(expression)
            current_values = {
                'second': current_time.second,
                'minute': current_time.minute,
                'hour': current_time.hour,
                'day': current_time.day,
                'month': current_time.month,
                'weekday': current_time.weekday()
            }
            
            return all(current_values[field] in schedule[field] for field in self.field_names)
        except ValueError as e:
            print(f"Error parsing cron expression: {str(e)}")
            return False

class CronManager:
    def __init__(self):
        self.logger = LogManager()
        self.server_monitor = ServerMonitor()
        self.config = self._load_config()
        self.docker_container_name = os.getenv('DOCKER_CONTAINER_NAME', 'stage_bjjgym')
        self.max_docker_retries = int(os.getenv('MAX_DOCKER_RETRIES', '30'))  # Default 30 retries
        self.docker_retry_delay = int(os.getenv('DOCKER_RETRY_DELAY', '10'))  # Default 10 seconds
        self.cron_parser = CronParser()
        
        # Check server and Docker container on startup
        self._ensure_services_running()

    def _load_config(self):
        with open('config.json', 'r') as f:
            return json.load(f)
            
    def _is_docker_available(self):
        """Check if Docker is installed and running."""
        try:
            # Check if docker command exists
            if not shutil.which('docker'):
                self.logger.log_cron_job("DOCKER", "Docker command not found")
                return False
                
            # Check if Docker daemon is running
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.log_cron_job("DOCKER", f"Docker daemon not running: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            self.logger.log_cron_job("DOCKER", f"Error checking Docker availability: {str(e)}")
            return False
            
    def _wait_for_docker(self):
        """Wait for Docker daemon to become available with retries."""
        self.logger.log_cron_job("DOCKER", "Waiting for Docker daemon to become available...")
        
        for attempt in range(1, self.max_docker_retries + 1):
            if self._is_docker_available():
                self.logger.log_cron_job("DOCKER", f"Docker daemon is now available after {attempt} attempts")
                return True
                
            self.logger.log_cron_job("DOCKER", f"Attempt {attempt}/{self.max_docker_retries}: Docker daemon not available yet, waiting {self.docker_retry_delay} seconds...")
            time.sleep(self.docker_retry_delay)
            
        self.logger.log_cron_job("DOCKER", f"Docker daemon not available after {self.max_docker_retries} attempts")
        return False
            
    def _check_docker_container(self):
        """Check if the Docker container is running and start it if not."""
        try:
            # First check if Docker is available, with retries
            if not self._wait_for_docker():
                self.logger.log_cron_job("DOCKER", "Docker is not available after retries, skipping container check")
                return False
                
            # Check if container exists
            check_exists = subprocess.run(
                ["docker", "container", "inspect", self.docker_container_name],
                capture_output=True,
                text=True
            )
            
            container_exists = check_exists.returncode == 0
            
            # Check if container is running
            check_running = subprocess.run(
                ["docker", "ps", "-q", "-f", f"name={self.docker_container_name}"],
                capture_output=True,
                text=True
            )
            
            container_running = bool(check_running.stdout.strip())
            
            if container_running:
                self.logger.log_cron_job("DOCKER", "Container is already running")
                return True
                
            if container_exists:
                # Container exists but not running, start it
                self.logger.log_cron_job("DOCKER", "Container exists but not running, attempting to start")
                start_result = subprocess.run(
                    ["docker", "start", self.docker_container_name],
                    capture_output=True,
                    text=True
                )
                
                if start_result.returncode != 0:
                    self.logger.log_cron_job("DOCKER", f"Failed to start container: {start_result.stderr}")
                    return False
                    
                # Wait a moment for the container to fully start
                time.sleep(2)
                
                # Verify it's running now
                verify_running = subprocess.run(
                    ["docker", "ps", "-q", "-f", f"name={self.docker_container_name}"],
                    capture_output=True,
                    text=True
                )
                
                if not verify_running.stdout.strip():
                    self.logger.log_cron_job("DOCKER", "Container failed to start properly")
                    return False
                    
                self.logger.log_cron_job("DOCKER", "Container started successfully")
                return True
            else:
                # Container doesn't exist - we don't want to create a new one
                # Just log the error and return false
                self.logger.log_cron_job("DOCKER", f"Container '{self.docker_container_name}' does not exist. Please create it manually.")
                return False
                
        except Exception as e:
            self.logger.log_cron_job("DOCKER", f"Error checking Docker container: {str(e)}")
            return False
            
    def _ensure_services_running(self):
        """Ensure both the server and Docker container are running on startup."""
        # First check Docker container
        docker_running = self._check_docker_container()
        
        # Then check server
        server_running = self.server_monitor.ensure_server_running()
        
        if docker_running and server_running:
            self.logger.log_cron_job("DOCKER AND SERVER RUNNING", "SUCCESS")
            return True
        else:
            status = []
            if not docker_running:
                status.append("Docker container")
            if not server_running:
                status.append("server")
                
            self.logger.log_cron_job("STARTUP", f"Failed to start: {', '.join(status)}")
            return False

    def execute_job(self, job):
        try:
            if not self.server_monitor.ensure_server_running():
                self.logger.log_cron_job(job['name'], "FAILED", error="Server is not running")
                return
            
            response = requests.request(
                method=job['method'],
                url=job['url'],
                timeout=50000
            )
            
            # Print response text to console for debugging
            # print(f"Job '{job['name']}' - Status: {response.status_code}, Response Text: {response.text}")

            response_data = None
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text} # Log raw response if not JSON

            self.logger.log_cron_job(
                job['name'],
                status=response.status_code,
                response={
                    "status_code": response.status_code,
                    "response": response_data
                }
            )
        except Exception as e:
            # Print errors to console
            print(f"Error executing job {job['name']}: {str(e)}")
            self.logger.log_cron_job(job['name'], "FAILED", error=str(e))

    def run(self):
        print("Cron Manager started...")
        while True:
            current_time = datetime.now()
            
            for job in self.config['jobs']:
                if self.cron_parser.should_run(job['schedule'], current_time):
                    self.execute_job(job)

            time.sleep(1)  # Check every second

if __name__ == "__main__":
    manager = CronManager()
    manager.run() 