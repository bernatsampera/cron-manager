import json
import time
import requests
from datetime import datetime
from logger import LogManager
from server_monitor import ServerMonitor

class CronManager:
    def __init__(self):
        self.logger = LogManager()
        self.server_monitor = ServerMonitor()
        self.config = self._load_config()

    def _load_config(self):
        with open('config.json', 'r') as f:
            return json.load(f)

    def execute_job(self, job):
        try:
            if not self.server_monitor.ensure_server_running():
                self.logger.log_cron_job(job['name'], "FAILED", error="Server is not running")
                return
            
            # Only print to console if there's an error
            response = requests.request(
                method=job['method'],
                url=job['url'],
                timeout=10
            )
            
            # Only log successful jobs at debug level
            self.logger.log_cron_job(
                job['name'],
                status=response.status_code,
                response={
                    "status_code": response.status_code,
                    "response": response.json()
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
                # Parse the schedule (format: "*/10 * * * * *" for every 10 seconds)
                schedule_parts = job['schedule'].split()
                if len(schedule_parts) == 6:  # Including seconds
                    seconds = schedule_parts[0]
                    if seconds.startswith('*/'):
                        interval = int(seconds[2:])
                        if current_time.second % interval == 0:
                            self.execute_job(job)

            time.sleep(1)  # Check every second

if __name__ == "__main__":
    manager = CronManager()
    manager.run() 