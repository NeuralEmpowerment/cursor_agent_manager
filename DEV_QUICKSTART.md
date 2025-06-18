# Developer Quickstart Guide

Get up and running with the Agent Monitor and its analytics system in minutes.

## 🚀 Quick Setup (5 minutes)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd agent_monitor_poc
./setup.sh
```

### 2. Test the System
```bash
# Test telemetry integration
python3 test_telemetry.py

# Run quickstart demonstration
python3 quickstart_test.py

# Start the monitor
./run.sh
```

### 3. Verify Analytics
```bash
# Check database info
./run_analytics.sh info

# Generate some test data and view it
./run_analytics.sh events --limit 5
```

## 🖥️ Running the Monitor

### Start the Application
```bash
./run.sh
```

**What you'll see:**
- Floating control panel appears on screen
- Console output showing template loading
- Monitor starts scanning every 2 seconds

### Control Panel Features
- **Pause/Resume**: Toggle monitoring on/off
- **Mute/Unmute**: Control sound alerts
- **Show Debug View**: See real-time detection visualization
- **Statistics**: Live counts from database
- **Diagnostics**: Current confidence scores and states

### First Time Setup
1. **Template Images**: Ensure `idle_button.png` and `generating_button.png` are in root directory
2. **Sound Files**: Place `.wav` files in `audio/` directory
3. **Permissions**: Grant screen recording permissions when prompted

## 📊 Analytics Deep Dive

### Database Overview
```bash
# Database info and stats
./run_analytics.sh info

# Recent activity
./run_analytics.sh events --limit 20 --hours 6

# Performance statistics
./run_analytics.sh stats --hours 24
```

### Generate Reports
```bash
# Daily report for today
./run_analytics.sh report

# Daily report for specific date
./run_analytics.sh report --date 2024-01-15

# Weekly accuracy trends
./run_analytics.sh trends --days 7

# Activity patterns
./run_analytics.sh activity --days 30
```

### Data Visualization
```bash
# Detection accuracy over time
./run_analytics.sh chart accuracy_trend --days 14

# Activity heatmap (hour vs day of week)
./run_analytics.sh chart activity_heatmap --days 30

# Event type distribution
./run_analytics.sh chart event_distribution --days 7

# Confidence scores scatter plot
./run_analytics.sh chart confidence_scatter --days 14
```

Charts are saved to `database/charts/` with timestamped filenames.

### Data Export
```bash
# Export last 7 days to CSV
./run_analytics.sh export telemetry_data.csv --days 7

# Export specific date range (modify analytics_cli.py for custom ranges)
./run_analytics.sh export monthly_data.csv --days 30
```

### Database Maintenance
```bash
# Preview what would be deleted (older than 30 days)
./run_analytics.sh cleanup --days 30 --dry-run

# Actually delete old data
./run_analytics.sh cleanup --days 30
```

## 🔧 Adding New Event Types

### 1. Define New Event Type

**Edit `telemetry/models.py`:**
```python
class EventType(Enum):
    IDLE_DETECTION = "idle_detection"
    ACTIVE_DETECTION = "active_detection"
    DETECTION_FAILURE = "detection_failure"
    COMMAND_EXECUTION = "command_execution"
    STATE_CHANGE = "state_change"
    ERROR = "error"
    INFO = "info"
    
    # Add your new event types here
    USER_INTERACTION = "user_interaction"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_WARNING = "performance_warning"
```

### 2. Add Convenience Methods

**Edit `telemetry/telemetry_service.py`:**
```python
class DefaultTelemetryService:
    # ... existing methods ...
    
    def record_user_interaction(self, interaction_type: str, details: dict = None):
        """Record user interaction events."""
        self.record_detection(
            event_type=EventType.USER_INTERACTION,
            message=f"User interaction: {interaction_type}",
            metadata={"interaction_type": interaction_type, **details} if details else {"interaction_type": interaction_type}
        )
    
    def record_system_alert(self, alert_level: str, message: str):
        """Record system alerts."""
        self.record_detection(
            event_type=EventType.SYSTEM_ALERT,
            message=message,
            metadata={"alert_level": alert_level}
        )
```

### 3. Use in Main Application

**Edit `agent_monitor_poc.py`:**
```python
# In the AgentMonitor class or wherever appropriate
def handle_user_interaction(self, interaction_type: str):
    """Example of recording user interactions."""
    self.telemetry.telemetry_service.record_user_interaction(
        interaction_type=interaction_type,
        details={"timestamp": time.time(), "context": "control_panel"}
    )

# In scan_and_act method or other detection logic
if some_performance_condition:
    self.telemetry.telemetry_service.record_detection(
        event_type=EventType.PERFORMANCE_WARNING,
        message="High memory usage detected",
        metadata={"memory_mb": memory_usage, "cpu_percent": cpu_usage}
    )
```

### 4. Update Analytics (Optional)

**Edit `telemetry/analytics.py`:**
```python
def get_user_interaction_analysis(self, days: int = 7) -> Dict[str, Any]:
    """Analyze user interaction patterns."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    events = self.repository.get_events(
        start_time=start_date,
        end_time=end_date,
        event_type=EventType.USER_INTERACTION
    )
    
    # Process and analyze interaction data
    interaction_types = {}
    for event in events:
        if event.metadata and 'interaction_type' in event.metadata:
            itype = event.metadata['interaction_type']
            interaction_types[itype] = interaction_types.get(itype, 0) + 1
    
    return {
        "total_interactions": len(events),
        "interaction_breakdown": interaction_types,
        "average_per_day": len(events) / days
    }
```

### 5. Add CLI Support (Optional)

**Edit `analytics_cli.py`:**
```python
# Add new subparser
interactions_parser = subparsers.add_parser('interactions', help='Analyze user interactions')
interactions_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')

# Add to the command handling
elif args.command == 'interactions':
    if hasattr(analytics, 'get_user_interaction_analysis'):
        analysis = analytics.get_user_interaction_analysis(args.days)
        print(f"User Interaction Analysis (last {args.days} days):")
        print("=" * 50)
        print_json(analysis)
    else:
        print("User interaction analysis not available")
```

## 🛠️ Common Development Tasks

### Testing Your Changes
```bash
# Test telemetry system
python3 test_telemetry.py

# Test specific event recording
python3 -c "
from container import initialize_telemetry_system
from telemetry import EventType

container = initialize_telemetry_system()
service = container.telemetry_service()

# Test your new event type
service.record_detection(
    event_type=EventType.USER_INTERACTION,
    message='Test user interaction',
    metadata={'test': True}
)

print('Event recorded successfully!')
"

# Verify in database
./run_analytics.sh events --limit 5
```

### Debugging Detection Issues
```bash
# Enable diagnostic mode in agent_monitor_poc.py
DIAGNOSTIC_MODE = True

# Run with debug output
./run.sh

# Check confidence scores in real-time via GUI debug view
# Or via analytics
./run_analytics.sh chart confidence_scatter --days 1
```

### Performance Monitoring
```bash
# Check database size and event counts
./run_analytics.sh info

# Monitor detection accuracy
./run_analytics.sh stats --hours 6

# Look for performance patterns
./run_analytics.sh activity --days 3
```

### Custom Analytics Queries
```bash
# Direct SQLite access for custom queries
sqlite3 database/telemetry.db

# Example queries:
sqlite> SELECT event_type, COUNT(*) FROM telemetry_events GROUP BY event_type;
sqlite> SELECT strftime('%H', timestamp) as hour, COUNT(*) FROM telemetry_events WHERE date(timestamp) = date('now') GROUP BY hour;
sqlite> SELECT AVG(confidence) FROM telemetry_events WHERE confidence IS NOT NULL;
```

## 🔍 Troubleshooting

### Monitor Not Detecting
1. **Check Templates**: Ensure `idle_button.png` and `generating_button.png` exist
2. **Enable Diagnostics**: Set `DIAGNOSTIC_MODE = True` in code
3. **Use Debug View**: Click "Show Debug View" to see what's being detected
4. **Check Confidence**: Run `./run_analytics.sh chart confidence_scatter`

### Database Issues
```bash
# Check if database exists and is accessible
./run_analytics.sh info

# Recreate database if corrupted
rm database/telemetry.db
python3 -c "from container import initialize_telemetry_system; initialize_telemetry_system()"

# Check database integrity
sqlite3 database/telemetry.db "PRAGMA integrity_check;"
```

### Performance Issues
```bash
# Clean up old data
./run_analytics.sh cleanup --days 30

# Check database size
./run_analytics.sh info

# Monitor system resources during detection
# (Add performance tracking to your custom events)
```

### Chart Generation Issues
```bash
# Ensure matplotlib is installed
pip install matplotlib

# Check charts directory permissions
ls -la database/charts/

# Test chart generation with minimal data
./run_analytics.sh chart event_distribution --days 1
```

## 📚 Next Steps

1. **Read Full Documentation**: See `TELEMETRY_README.md` for complete API documentation
2. **Extend Detection**: Add new detector classes implementing `StateDetector` protocol
3. **Custom Analytics**: Create specialized analysis functions for your use case
4. **Integration**: Use the telemetry system in other applications via the container
5. **Dashboard**: Build a web interface using the SQLite data

## 💡 Pro Tips

- **Use `record_detection()` for structured events** with specific types
- **Use `record_event()` for flexible events** with arbitrary metadata
- **Test telemetry changes** with `python3 test_telemetry.py` before running main app
- **Generate charts regularly** to visualize detection accuracy trends
- **Export data periodically** for external analysis or backup
- **Clean up old data** to maintain performance with `./run_analytics.sh cleanup`

## 🤝 Development Workflow

```bash
# 1. Make your changes
# 2. Test telemetry integration
python3 test_telemetry.py

# 3. Test the monitor
./run.sh

# 4. Verify analytics work
./run_analytics.sh events --limit 5

# 5. Generate a chart to verify data
./run_analytics.sh chart event_distribution --days 1

# 6. Clean up test data if needed
./run_analytics.sh cleanup --days 0 --dry-run
```

Happy coding! 🎉 