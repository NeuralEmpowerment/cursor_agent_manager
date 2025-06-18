# Agent Monitor Telemetry System

## Overview

The Agent Monitor now includes a comprehensive telemetry system with SQLite database integration, dependency injection, and advanced analytics capabilities. This system provides detailed tracking, analysis, and visualization of agent monitoring activities.

## Architecture

### Dependency Injection

The telemetry system uses dependency injection with the `dependency-injector` library for clean separation of concerns:

- **Interfaces**: Abstract protocols define service contracts
- **Implementations**: Concrete implementations of telemetry services
- **Container**: Manages dependencies and provides configured instances

### Components

1. **TelemetryRepository**: Data storage interface (SQLite implementation)
2. **TelemetryService**: High-level telemetry operations
3. **AnalyticsService**: Data analysis and visualization
4. **LegacyTelemetryAdapter**: Maintains compatibility with existing code

## Database Schema

The SQLite database includes three main tables:

### telemetry_events
- `id`: Primary key
- `timestamp`: Event timestamp
- `event_type`: Type of event (idle_detection, active_detection, etc.)
- `message`: Human-readable message
- `confidence`: Detection confidence score
- `state`: Agent state (idle, active, unknown)
- `detection_method`: Method used for detection
- `match_rect_*`: Bounding box coordinates for detections
- `metadata`: JSON metadata for additional information

### monitoring_sessions
- Session tracking for long-running monitoring periods

### performance_metrics
- Performance data for system optimization

## Event Types

```python
class EventType(Enum):
    IDLE_DETECTION = "idle_detection"
    ACTIVE_DETECTION = "active_detection"
    DETECTION_FAILURE = "detection_failure"
    COMMAND_EXECUTION = "command_execution"
    STATE_CHANGE = "state_change"
    ERROR = "error"
    INFO = "info"
```

## Usage

### Basic Telemetry Recording

```python
from container import TelemetryContainer
from telemetry import EventType

# Initialize container
container = TelemetryContainer()
container.initialize_database()

# Get telemetry service
telemetry = container.telemetry_service()

# Record events using generic method
telemetry.record_detection(
    event_type=EventType.IDLE_DETECTION,
    message="Agent idle state detected",
    confidence=0.95,
    detection_method="TemplateMatchDetector",
    state="idle",
    match_rect=(100, 200, 50, 30)
)

# Record with flexible parameters
telemetry.record_event(
    event_type=EventType.COMMAND_EXECUTION,
    message="Executed user command",
    command="ls -la",
    execution_time=0.5
)
```

### Analytics and Reporting

```python
# Get analytics service
analytics = container.analytics_service()

# Generate daily report
report = analytics.generate_daily_report(datetime.now())
print(json.dumps(report, indent=2))

# Get accuracy trends
trends = analytics.get_detection_accuracy_trends(days=7)

# Create visualizations
chart_path = analytics.create_visualization("accuracy_trend")
```

## Command Line Interface

Use the analytics CLI tool to review data and generate reports:

```bash
# Show database information
./run_analytics.sh info

# Show recent events
./run_analytics.sh events --limit 20 --hours 12

# Generate statistics
./run_analytics.sh stats --hours 24

# Create daily report
./run_analytics.sh report --date 2024-01-15

# Show accuracy trends
./run_analytics.sh trends --days 14

# Analyze activity patterns
./run_analytics.sh activity --days 30

# Export data to CSV
./run_analytics.sh export data.csv --days 7

# Generate charts
./run_analytics.sh chart accuracy_trend --days 14
./run_analytics.sh chart activity_heatmap --days 30
./run_analytics.sh chart event_distribution --days 7
./run_analytics.sh chart confidence_scatter --days 14

# Clean up old data
./run_analytics.sh cleanup --days 30 --dry-run
```

## Available Chart Types

1. **accuracy_trend**: Line chart showing detection accuracy over time
2. **activity_heatmap**: Heatmap showing activity patterns by hour and day
3. **event_distribution**: Pie chart showing distribution of event types
4. **confidence_scatter**: Scatter plot of confidence scores over time

## Data Export and Integration

### CSV Export
Export telemetry data to CSV for external analysis:
```bash
./run_analytics.sh export telemetry_data.csv --days 30
```

### Database Access
Direct SQLite database access:
```bash
sqlite3 database/telemetry.db
```

Example queries:
```sql
-- Get hourly activity counts
SELECT 
    strftime('%H', timestamp) as hour,
    COUNT(*) as event_count
FROM telemetry_events 
WHERE date(timestamp) = date('now')
GROUP BY hour
ORDER BY hour;

-- Get average confidence by detection method
SELECT 
    detection_method,
    AVG(confidence) as avg_confidence,
    COUNT(*) as detection_count
FROM telemetry_events 
WHERE confidence IS NOT NULL
GROUP BY detection_method;
```

## Configuration

### Database Location
Configure database path in the container:
```python
container = TelemetryContainer()
container.config.database_path.from_value("custom/path/telemetry.db")
```

### Charts Directory
Configure charts output directory:
```python
container.config.charts_directory.from_value("custom/charts")
```

## Performance Considerations

- Database is automatically created in `database/` directory
- Old data cleanup available via CLI: `./run_analytics.sh cleanup`
- Database size monitoring available via `info` command
- Indexes automatically created for common queries

## Integration with Existing Code

The system maintains backward compatibility through `LegacyTelemetryAdapter`:

```python
# Old code continues to work
telemetry.record_detection()
telemetry.record_failure()
telemetry.log_event("Custom message")

# But now with enhanced capabilities
telemetry.record_detection(
    confidence=0.95,
    detection_method="TemplateMatch",
    match_rect=(x, y, w, h)
)
```

## Troubleshooting

### Database Issues
```bash
# Check database info
./run_analytics.sh info

# Recreate database
rm database/telemetry.db
python3 -c "from container import TelemetryContainer; TelemetryContainer().initialize_database()"
```

### Chart Generation Issues
- Ensure matplotlib is installed: `pip install matplotlib`
- Check charts directory permissions
- Charts saved to `database/charts/` by default

### Performance Issues
- Run cleanup regularly: `./run_analytics.sh cleanup --days 30`
- Monitor database size with `info` command
- Consider data archival for long-term deployments

## Advanced Usage

### Custom Event Types
Extend the EventType enum for application-specific events:

```python
class CustomEventType(EventType):
    USER_INTERACTION = "user_interaction"
    SYSTEM_ALERT = "system_alert"
```

### Custom Analytics
Implement custom analytics by extending the analytics service:

```python
class CustomAnalyticsService(DefaultAnalyticsService):
    def get_user_interaction_patterns(self):
        # Custom analysis logic
        pass
```

### Batch Operations
For high-volume telemetry, consider batch operations:

```python
events = [
    TelemetryEvent(event_type=EventType.IDLE_DETECTION, ...),
    TelemetryEvent(event_type=EventType.ACTIVE_DETECTION, ...),
]

# Process in batch
for event in events:
    repository.log_event(event)
``` 