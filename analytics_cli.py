#!/usr/bin/env python3
"""
Analytics CLI Tool

Command-line interface for reviewing telemetry data and generating analytics reports.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from container import initialize_telemetry_system
from telemetry import EventType

def print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2, default=str))

def main():
    parser = argparse.ArgumentParser(description="Agent Monitor Analytics Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Database info command
    info_parser = subparsers.add_parser('info', help='Show database information')
    
    # Recent events command
    events_parser = subparsers.add_parser('events', help='Show recent events')
    events_parser.add_argument('--limit', type=int, default=20, help='Number of events to show')
    events_parser.add_argument('--type', choices=[e.value for e in EventType], help='Filter by event type')
    events_parser.add_argument('--hours', type=int, default=24, help='Hours back to search')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('--hours', type=int, default=24, help='Hours back to analyze')
    
    # Daily report command
    report_parser = subparsers.add_parser('report', help='Generate daily report')
    report_parser.add_argument('--date', help='Date in YYYY-MM-DD format (default: today)')
    
    # Trends command
    trends_parser = subparsers.add_parser('trends', help='Show accuracy trends')
    trends_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    
    # Activity patterns command
    activity_parser = subparsers.add_parser('activity', help='Analyze activity patterns')
    activity_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to CSV')
    export_parser.add_argument('output_file', help='Output CSV file path')
    export_parser.add_argument('--days', type=int, default=7, help='Number of days to export')
    
    # Chart generation command
    chart_parser = subparsers.add_parser('chart', help='Generate charts')
    chart_parser.add_argument('chart_type', choices=[
        'accuracy_trend', 'activity_heatmap', 'event_distribution', 'confidence_scatter'
    ], help='Type of chart to generate')
    chart_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Days of data to keep')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize container and services
    container = initialize_telemetry_system()
    
    repository = container.telemetry_repository()
    analytics = container.analytics_service()
    
    try:
        if args.command == 'info':
            db_info = repository.get_database_info()
            print("Database Information:")
            print("=" * 40)
            print(f"Path: {db_info['db_path']}")
            print(f"Total Events: {db_info['total_events']:,}")
            print(f"Database Size: {db_info['db_size_mb']} MB")
            print(f"Earliest Event: {db_info['earliest_event']}")
            print(f"Latest Event: {db_info['latest_event']}")
            
        elif args.command == 'events':
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=args.hours)
            
            event_type = EventType(args.type) if args.type else None
            events = repository.get_events(
                start_time=start_time,
                end_time=end_time,
                event_type=event_type,
                limit=args.limit
            )
            
            print(f"Recent Events (last {args.hours} hours):")
            print("=" * 60)
            for event in events:
                confidence_str = f" (conf: {event.confidence:.2f})" if event.confidence else ""
                print(f"{event.timestamp} | {event.event_type.value:20} | {event.message}{confidence_str}")
                
        elif args.command == 'stats':
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=args.hours)
            
            stats = repository.get_session_stats(start_time, end_time)
            
            print(f"Statistics (last {args.hours} hours):")
            print("=" * 40)
            print(f"Idle Detections: {stats.total_idle_detections}")
            print(f"Active Detections: {stats.total_active_detections}")
            print(f"Detection Failures: {stats.total_detection_failures}")
            print(f"Average Confidence: {stats.average_confidence:.2f}")
            print(f"Session Duration: {stats.session_duration_seconds // 60} minutes")
            
            total_detections = stats.total_idle_detections + stats.total_active_detections
            total_attempts = total_detections + stats.total_detection_failures
            accuracy = (total_detections / total_attempts * 100) if total_attempts > 0 else 0
            print(f"Detection Accuracy: {accuracy:.1f}%")
            
        elif args.command == 'report':
            if args.date:
                date = datetime.strptime(args.date, "%Y-%m-%d")
            else:
                date = datetime.now()
            
            report = analytics.generate_daily_report(date)
            print(f"Daily Report for {report['date']}:")
            print("=" * 50)
            print_json(report)
            
        elif args.command == 'trends':
            trends = analytics.get_detection_accuracy_trends(args.days)
            print(f"Accuracy Trends (last {args.days} days):")
            print("=" * 50)
            print_json(trends)
            
        elif args.command == 'activity':
            patterns = analytics.get_activity_patterns(args.days)
            print(f"Activity Patterns (last {args.days} days):")
            print("=" * 50)
            print_json(patterns)
            
        elif args.command == 'export':
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            
            analytics.export_data_csv(args.output_file, start_date, end_date)
            print(f"Data exported to {args.output_file}")
            print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
        elif args.command == 'chart':
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            
            chart_path = analytics.create_visualization(args.chart_type, (start_date, end_date))
            print(f"Chart generated: {chart_path}")
            
        elif args.command == 'cleanup':
            if args.dry_run:
                cutoff_date = datetime.now() - timedelta(days=args.days)
                events = repository.get_events(end_time=cutoff_date)
                print(f"Would delete {len(events)} events older than {cutoff_date}")
            else:
                deleted_count = repository.cleanup_old_data(args.days)
                print(f"Deleted {deleted_count} old records")
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 