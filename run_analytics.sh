#!/bin/bash

# Agent Monitor Analytics Runner
# Provides easy access to analytics commands

source venv/bin/activate

echo "Agent Monitor Analytics Tool"
echo "============================"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Available commands:"
    echo "  info       - Show database information"
    echo "  events     - Show recent events"
    echo "  stats      - Show statistics"
    echo "  report     - Generate daily report"
    echo "  trends     - Show accuracy trends"
    echo "  activity   - Analyze activity patterns"
    echo "  export     - Export data to CSV"
    echo "  chart      - Generate charts"
    echo "  cleanup    - Clean up old data"
    echo ""
    echo "Examples:"
    echo "  $0 info"
    echo "  $0 events --limit 10 --hours 6"
    echo "  $0 stats --hours 12"
    echo "  $0 report --date 2024-01-15"
    echo "  $0 chart accuracy_trend --days 14"
    echo "  $0 export telemetry_data.csv --days 30"
    exit 1
fi

python3 analytics_cli.py "$@" 