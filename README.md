# Cron Job Manager

A Python-based cron job manager that helps you organize and monitor your scheduled tasks, with a focus on HTTP requests and server health monitoring.

## Features

- Schedule and manage HTTP requests as cron jobs
- Automatic server health monitoring
- Organized logging system with daily rotation
- Easy-to-use configuration
- Server auto-start capability

## Installation

1. Clone this repository
2. Install the required dependencies:

Set up a virtual environment and install dependencies with uv:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e . # On Prod
uv pip install -e ".[dev]" # Local

```

## Configuration

Create a `.env` file in the root directory with the following variables:

```
SERVER_URL=http://127.0.0.1:8000
SERVER_START_COMMAND=your_server_start_command
LOG_DIR=logs
```

## Usage

1. Start the cron manager:

```bash
python cron_manager.py
```

2. View logs:

```bash
python view_logs.py
```

## Log Structure

Logs are organized by date in the following structure:

```
logs/
  ├── 2024-03-21/
  │   ├── cron.log
  │   └── server_health.log
  └── 2024-03-20/
      ├── cron.log
      └── server_health.log
```

## Adding New Cron Jobs

Add new cron jobs in the `config.json` file:

```json
{
  "jobs": [
    {
      "name": "test_endpoint",
      "url": "http://127.0.0.1:8000/test",
      "schedule": "*/10 * * * * *",
      "method": "GET"
    }
  ]
}
```

## Server Health Monitoring

The system automatically checks if the target server is running. If the server is down:

1. It will attempt to start the server using the configured command
2. Log the incident
3. Continue monitoring

## Viewing Logs

Today's logs can be viewed using:

```bash
python view_logs.py --today
```

View logs for a specific date:

```bash
python view_logs.py --date 2024-03-21
```

## Project Structure

```
cron-manager/
├── cron_manager.py      # Main cron job manager
├── server_monitor.py    # Server health monitoring
├── logger.py           # Logging configuration
├── config.json         # Cron job configurations
├── .env               # Environment variables
├── requirements.txt   # Project dependencies
└── logs/             # Log directory
```
