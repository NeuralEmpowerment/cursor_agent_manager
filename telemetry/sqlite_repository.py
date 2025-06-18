#!/usr/bin/env python3
"""
SQLite Telemetry Repository

Concrete implementation of TelemetryRepository using SQLite database.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
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
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            for schema in DatabaseSchema.get_all_schemas():
                conn.execute(schema)
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
                 match_rect_x, match_rect_y, match_rect_width, match_rect_height, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                metadata_json
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
                    metadata=metadata
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
            
            return {
                "db_path": self.db_path,
                "total_events": event_count,
                "db_size_bytes": db_size_bytes,
                "db_size_mb": round(db_size_bytes / (1024 * 1024), 2),
                "earliest_event": date_range[0] if date_range[0] else None,
                "latest_event": date_range[1] if date_range[1] else None
            } 