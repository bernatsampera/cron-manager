# Cron Manager

A Python-based cron job manager that executes scheduled tasks and ensures the server and Docker container are running.

## Features

- Automatically starts the server if it's not running
- Automatically starts the Docker container if it's not running
- Configurable cron jobs with flexible scheduling
- Logging of job execution results
- Health monitoring of the server

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure the `.env` file with your settings
4. Configure your cron jobs in `config.json`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```
# Server configuration
SERVER_URL=http://127.0.0.1:8008/health

# Docker configuration
DOCKER_CONTAINER_NAME=stage_bjjgym
DOCKER_IMAGE=stage_bjjgym:latest
```

### Docker Configuration

The cron manager will automatically check if the Docker container is running and start it if needed. Make sure:

1. Docker is installed and running on your system
2. The Docker image specified in `DOCKER_IMAGE` exists
3. You have the necessary permissions to run Docker commands

If you're having issues with Docker container startup:

1. Check if Docker is running: `docker info`
2. Verify the container exists: `docker container inspect stage_bjjgym`
3. Check Docker logs: `docker logs stage_bjjgym`
4. Ensure the Docker image exists: `docker images | grep stage_bjjgym`

### Cron Job Configuration

Cron jobs are configured in the `config.json` file. Each job has the following properties:

- `name`: A descriptive name for the job
- `url`: The URL to call when the job is executed
- `method`: The HTTP method to use (GET, POST, etc.)
- `schedule`: The cron schedule in the format `* * * * * *` (seconds, minutes, hours, day of month, month, day of week)
- `notes`: Optional notes about the job

#### Schedule Format

The schedule uses a modified cron format that includes seconds:

```
* * * * * *
│ │ │ │ │ │
│ │ │ │ │ └── Day of week (0-6) (Sunday=0)
│ │ │ │ └──── Month (1-12)
│ │ │ └────── Day of month (1-31)
│ │ └──────── Hour (0-23)
│ └────────── Minute (0-59)
└──────────── Second (0-59)
```

#### Examples

1. **Run every 10 seconds**:

   ```
   "schedule": "*/10 * * * * *"
   ```

2. **Run every 10 minutes**:

   ```
   "schedule": "0 */10 * * * *"
   ```

3. **Run every hour**:

   ```
   "schedule": "0 0 * * * *"
   ```

4. **Run at 2:30 PM every day**:

   ```
   "schedule": "0 30 14 * * *"
   ```

5. **Run every Monday at 9:00 AM**:
   ```
   "schedule": "0 0 9 * * 1"
   ```

### Example Configuration

```json
{
  "jobs": [
    {
      "name": "Health Check",
      "url": "http://127.0.0.1:8008/health",
      "notes": "This job checks the health of the server every 10 minutes",
      "schedule": "0 */10 * * * *",
      "method": "GET"
    },
    {
      "name": "Reddit Poster",
      "url": "http://127.0.0.1:8008/local/reddit-poster",
      "notes": "This job runs the Reddit poster every 10 seconds",
      "schedule": "*/10 * * * * *",
      "method": "GET"
    }
  ],
  "server_check_interval": 60,
  "log_retention_days": 7
}
```

## Usage

Run the cron manager:

```
python cron_manager.py
```

To run in the background:

```
nohup python cron_manager.py > /dev/null 2>&1 &
```

## Logs

Logs are stored in the `logs` directory. You can view them using the `view_logs.py` script:

```
python view_logs.py
```

## Troubleshooting

If the server or Docker container fails to start, check the logs for error messages. Common issues include:

- The server directory path is incorrect
- The virtual environment path is incorrect
- The Docker container image is not available
- The server URL is incorrect
- Docker is not running or not properly installed
- Insufficient permissions to run Docker commands

### Docker Troubleshooting

If you're having issues with Docker container startup:

1. Make sure Docker is installed and running:

   ```
   docker info
   ```

2. Check if the Docker image exists:

   ```
   docker images | grep stage_bjjgym
   ```

3. If the image doesn't exist, you need to build it or pull it from a registry.

4. Check Docker logs for errors:

   ```
   docker logs stage_bjjgym
   ```

5. If the container exists but won't start, try removing it and recreating:
   ```
   docker rm stage_bjjgym
   docker run -d --name stage_bjjgym stage_bjjgym:latest
   ```

## License

MIT
