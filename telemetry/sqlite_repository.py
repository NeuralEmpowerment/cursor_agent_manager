#!/usr/bin/env python3
"""
SQLite Telemetry Repository

Concrete implementation of TelemetryRepository using SQLite database.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Tuple
from .models import TelemetryEvent, SessionStats, EventType, DatabaseSchema
from .interfaces import TelemetryRepository

class SQLiteTelemetryRepository:
    """SQLite implementation of TelemetryRepository."""
    
    def __init__(self, db_path: str = "database/telemetry.db"):
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def initialize(self) -> None:
        """Initialize the database with required tables and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            # Create all tables
            for schema in DatabaseSchema.get_all_schemas():
                conn.execute(schema)
            
            # Create all indexes for performance
            for index in DatabaseSchema.get_all_indexes():
                conn.execute(index)
            
            conn.commit()
    
    def log_event(self, event: TelemetryEvent) -> int:
        """Log a telemetry event and return the event ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert enum to string if needed
            event_type_str = event.event_type.value if isinstance(event.event_type, EventType) else event.event_type
            
            # Serialize metadata to JSON if it exists
            metadata_json = json.dumps(event.metadata) if event.metadata else None
            
            cursor.execute("""
                INSERT INTO telemetry_events 
                (timestamp, event_type, message, confidence, state, detection_method,
                 match_rect_x, match_rect_y, match_rect_width, match_rect_height, metadata,
                 duration_seconds, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp or datetime.now(),
                event_type_str,
                event.message,
                event.confidence,
                event.state,
                event.detection_method,
                event.match_rect_x,
                event.match_rect_y,
                event.match_rect_width,
                event.match_rect_height,
                metadata_json,
                event.duration_seconds,
                event.session_id
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            return event_id
    
    def get_events(self, 
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  event_type: Optional[EventType] = None,
                  limit: Optional[int] = None) -> List[TelemetryEvent]:
        """Get events with optional filtering."""
        
        query = "SELECT * FROM telemetry_events WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                # Parse metadata JSON if it exists
                metadata = json.loads(row['metadata']) if row['metadata'] else None
                
                event = TelemetryEvent(
                    id=row['id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    event_type=EventType(row['event_type']),
                    message=row['message'],
                    confidence=row['confidence'],
                    state=row['state'],
                    detection_method=row['detection_method'],
                    match_rect_x=row['match_rect_x'],
                    match_rect_y=row['match_rect_y'],
                    match_rect_width=row['match_rect_width'],
                    match_rect_height=row['match_rect_height'],
                    metadata=metadata,
                    duration_seconds=row.get('duration_seconds'),
                    session_id=row.get('session_id')
                )
                events.append(event)
            
            return events
    
    def get_session_stats(self, 
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> SessionStats:
        """Get aggregated statistics for a time period."""
        
        if not start_time:
            start_time = datetime.now() - timedelta(days=1)  # Default to last 24 hours
        if not end_time:
            end_time = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count different event types
            cursor.execute("""
                SELECT 
                    event_type,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM telemetry_events 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY event_type
            """, (start_time, end_time))
            
            results = cursor.fetchall()
            
            stats = SessionStats()
            total_confidence_sum = 0
            total_confidence_count = 0
            
            for event_type, count, avg_confidence in results:
                if event_type == EventType.IDLE_DETECTION.value:
                    stats.total_idle_detections = count
                elif event_type == EventType.ACTIVE_DETECTION.value:
                    stats.total_active_detections = count
                elif event_type == EventType.DETECTION_FAILURE.value:
                    stats.total_detection_failures = count
                
                if avg_confidence is not None:
                    total_confidence_sum += avg_confidence * count
                    total_confidence_count += count
            
            # Calculate overall average confidence
            if total_confidence_count > 0:
                stats.average_confidence = total_confidence_sum / total_confidence_count
            
            # Get first and last events in the time range
            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp)
                FROM telemetry_events 
                WHERE timestamp BETWEEN ? AND ?
            """, (start_time, end_time))
            
            first_event, last_event = cursor.fetchone()
            if first_event:
                stats.first_event = datetime.fromisoformat(first_event)
            if last_event:
                stats.last_event = datetime.fromisoformat(last_event)
                if stats.first_event:
                    stats.session_duration_seconds = int((stats.last_event - stats.first_event).total_seconds())
            
            return stats
    
    # NEW DURATION-BASED QUERY METHODS FOR ENHANCED ANALYTICS
    
    def get_daily_durations(self, target_date: date) -> Dict[str, float]:
        """Get total duration by state for a specific day."""
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT state, SUM(duration_seconds) as total_duration
                FROM telemetry_events 
                WHERE timestamp BETWEEN ? AND ? 
                AND duration_seconds IS NOT NULL
                AND state IS NOT NULL
                GROUP BY state
            """, (start_time, end_time))
            
            results = cursor.fetchall()
            return {state: duration for state, duration in results}
    
    def get_weekly_durations(self, start_date: date) -> Dict[str, Dict[str, float]]:
        """Get duration breakdown by state for each day in a week."""
        weekly_data = {}
        
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            daily_durations = self.get_daily_durations(current_date)
            weekly_data[current_date.isoformat()] = daily_durations
        
        return weekly_data
    
    def get_monthly_durations(self, month: int, year: int) -> Dict[str, Dict[str, float]]:
        """Get duration breakdown by state for each day in a month."""
        from calendar import monthrange
        
        start_date = date(year, month, 1)
        days_in_month = monthrange(year, month)[1]
        monthly_data = {}
        
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            daily_durations = self.get_daily_durations(current_date)
            monthly_data[current_date.isoformat()] = daily_durations
        
        return monthly_data
    
    def get_cumulative_stats(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get cumulative statistics for a date range."""
        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.max.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get total durations by state
            cursor.execute("""
                SELECT 
                    state,
                    SUM(duration_seconds) as total_duration,
                    COUNT(*) as event_count,
                    AVG(duration_seconds) as avg_duration,
                    MIN(duration_seconds) as min_duration,
                    MAX(duration_seconds) as max_duration
                FROM telemetry_events 
                WHERE timestamp BETWEEN ? AND ? 
                AND duration_seconds IS NOT NULL
                AND state IS NOT NULL
                GROUP BY state
            """, (start_time, end_time))
            
            state_stats = {}
            for row in cursor.fetchall():
                state, total, count, avg, min_dur, max_dur = row
                state_stats[state] = {
                    'total_duration': total,
                    'event_count': count,
                    'average_duration': avg,
                    'min_duration': min_dur,
                    'max_duration': max_dur
                }
            
            # Get overall statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    SUM(duration_seconds) as total_duration,
                    AVG(confidence) as avg_confidence,
                    MIN(timestamp) as first_event,
                    MAX(timestamp) as last_event
                FROM telemetry_events 
                WHERE timestamp BETWEEN ? AND ?
            """, (start_time, end_time))
            
            overall = cursor.fetchone()
            
            return {
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'overall': {
                    'total_events': overall[0],
                    'total_duration': overall[1] or 0,
                    'average_confidence': overall[2] or 0,
                    'first_event': overall[3],
                    'last_event': overall[4],
                    'period_days': (end_date - start_date).days + 1
                },
                'by_state': state_stats
            }
    
    # SESSION MANAGEMENT METHODS
    
    def create_session(self, session_id: str, config_snapshot: Optional[str] = None) -> int:
        """Create a new monitoring session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO monitoring_sessions 
                (session_id, session_start, config_snapshot)
                VALUES (?, ?, ?)
            """, (session_id, datetime.now(), config_snapshot))
            
            session_record_id = cursor.lastrowid
            conn.commit()
            return session_record_id
    
    def end_session(self, session_id: str) -> None:
        """End a monitoring session and calculate final statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Calculate session statistics from events
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    SUM(CASE WHEN state = 'idle' AND duration_seconds IS NOT NULL 
                        THEN duration_seconds ELSE 0 END) as total_idle,
                    SUM(CASE WHEN state = 'active' AND duration_seconds IS NOT NULL 
                        THEN duration_seconds ELSE 0 END) as total_active,
                    SUM(CASE WHEN state = 'run_command' AND duration_seconds IS NOT NULL 
                        THEN duration_seconds ELSE 0 END) as total_run_command,
                    SUM(CASE WHEN duration_seconds IS NOT NULL 
                        THEN duration_seconds ELSE 0 END) as total_runtime
                FROM telemetry_events 
                WHERE session_id = ?
            """, (session_id,))
            
            stats = cursor.fetchone()
            
            # Update session record
            cursor.execute("""
                UPDATE monitoring_sessions 
                SET session_end = ?,
                    total_events = ?,
                    total_idle_seconds = ?,
                    total_active_seconds = ?,
                    total_run_command_seconds = ?,
                    total_runtime_seconds = ?
                WHERE session_id = ?
            """, (
                datetime.now(),
                stats[0],  # total_events
                stats[1],  # total_idle
                stats[2],  # total_active
                stats[3],  # total_run_command
                stats[4],  # total_runtime
                session_id
            ))
            
            conn.commit()
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM monitoring_sessions 
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old data. Returns number of records removed."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM telemetry_events 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get table counts
            cursor.execute("SELECT COUNT(*) FROM telemetry_events")
            event_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM monitoring_sessions")
            session_count = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size_bytes = page_count * page_size
            
            # Get date range
            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM telemetry_events
            """)
            date_range = cursor.fetchone()
            
            # Get duration tracking statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as events_with_duration,
                    SUM(duration_seconds) as total_tracked_duration,
                    AVG(duration_seconds) as avg_duration
                FROM telemetry_events 
                WHERE duration_seconds IS NOT NULL
            """)
            duration_stats = cursor.fetchone()
            
            return {
                "db_path": self.db_path,
                "total_events": event_count,
                "total_sessions": session_count,
                "db_size_bytes": db_size_bytes,
                "db_size_mb": round(db_size_bytes / (1024 * 1024), 2),
                "earliest_event": date_range[0] if date_range[0] else None,
                "latest_event": date_range[1] if date_range[1] else None,
                "duration_tracking": {
                    "events_with_duration": duration_stats[0],
                    "total_tracked_seconds": duration_stats[1] or 0,
                    "average_duration": duration_stats[2] or 0
                }
            } 