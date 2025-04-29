import argparse
from datetime import datetime
from logger import LogManager

def main():
    parser = argparse.ArgumentParser(description='View cron job logs')
    parser.add_argument('--today', action='store_true', help='View today\'s logs')
    parser.add_argument('--date', type=str, help='View logs for a specific date (YYYY-MM-DD)')
    parser.add_argument('--type', type=str, default='cron', choices=['cron', 'server_health'],
                      help='Type of logs to view (default: cron)')
    
    args = parser.parse_args()
    logger = LogManager()

    if args.today:
        logs = logger.get_today_logs(args.type)
        print(f"\nToday's {args.type} logs:")
    elif args.date:
        logs = logger.get_logs_by_date(args.date, args.type)
        print(f"\nLogs for {args.date} ({args.type}):")
    else:
        print("Please specify --today or --date")
        return

    if not logs:
        print("No logs found")
        return

    for log in logs:
        print(log.strip())

if __name__ == "__main__":
    main() 