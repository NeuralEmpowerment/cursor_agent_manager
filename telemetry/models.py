#!/usr/bin/env python3
"""
Telemetry Database Models

Defines the SQLite database schema for agent monitoring telemetry.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class EventType(Enum):
    IDLE_DETECTION = "idle_detection"
    ACTIVE_DETECTION = "active_detection"
    DETECTION_FAILURE = "detection_failure"
    COMMAND_EXECUTION = "command_execution"
    STATE_CHANGE = "state_change"
    ERROR = "error"
    INFO = "info"

@dataclass
class TelemetryEvent:
    """Represents a single telemetry event."""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    event_type: Optional[EventType] = None
    message: Optional[str] = None
    confidence: Optional[float] = None
    state: Optional[str] = None
    detection_method: Optional[str] = None
    match_rect_x: Optional[int] = None
    match_rect_y: Optional[int] = None
    match_rect_width: Optional[int] = None
    match_rect_height: Optional[int] = None
    metadata: Optional[str] = None  # JSON string for additional data

@dataclass
class SessionStats:
    """Aggregated statistics for a monitoring session."""
    total_idle_detections: int = 0
    total_active_detections: int = 0
    total_detection_failures: int = 0
    average_confidence: float = 0.0
    session_duration_seconds: int = 0
    first_event: Optional[datetime] = None
    last_event: Optional[datetime] = None

class DatabaseSchema:
    """Database schema definitions."""
    
    CREATE_EVENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS telemetry_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT NOT NULL,
        message TEXT,
        confidence REAL,
        state TEXT,
        detection_method TEXT,
        match_rect_x INTEGER,
        match_rect_y INTEGER,
        match_rect_width INTEGER,
        match_rect_height INTEGER,
        metadata TEXT
    )
    """
    
    CREATE_SESSIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS monitoring_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
        session_end DATETIME,
        total_events INTEGER DEFAULT 0,
        config_snapshot TEXT
    )
    """
    
    CREATE_PERFORMANCE_TABLE = """
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        check_duration_ms REAL,
        memory_usage_mb REAL,
        cpu_usage_percent REAL,
        screenshot_size_kb REAL
    )
    """

    @staticmethod
    def get_all_schemas() -> List[str]:
        """Get all schema creation statements."""
        return [
            DatabaseSchema.CREATE_EVENTS_TABLE,
            DatabaseSchema.CREATE_SESSIONS_TABLE,
            DatabaseSchema.CREATE_PERFORMANCE_TABLE
        ] 