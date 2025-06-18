#!/usr/bin/env python3
"""
Telemetry Interfaces

Abstract interfaces for telemetry systems using Protocol for dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime
from .models import TelemetryEvent, SessionStats, EventType

class TelemetryRepository(Protocol):
    """Abstract interface for telemetry data storage."""
    
    def initialize(self) -> None:
        """Initialize the repository."""
        ...
    
    def log_event(self, event: TelemetryEvent) -> int:
        """Log a telemetry event. Returns the event ID."""
        ...
    
    def get_events(self, 
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  event_type: Optional[EventType] = None,
                  limit: Optional[int] = None) -> List[TelemetryEvent]:
        """Get events with optional filtering."""
        ...
    
    def get_session_stats(self, 
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> SessionStats:
        """Get aggregated statistics for a time period."""
        ...
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old data. Returns number of records removed."""
        ...

class TelemetryService(Protocol):
    """High-level telemetry service interface."""
    
    def record_detection(self, 
                        event_type: EventType,
                        message: str = None,
                        confidence: float = None, 
                        detection_method: str = None,
                        state: str = None,
                        match_rect: tuple = None,
                        metadata: Dict[str, Any] = None) -> None:
        """Record a detection event with specified type and optional parameters."""
        ...
    
    def record_event(self, 
                    event_type: EventType,
                    message: str = None,
                    **kwargs) -> None:
        """Record any type of event with flexible parameters."""
        ...
    
    def get_recent_stats(self, hours: int = 24) -> SessionStats:
        """Get statistics for recent activity."""
        ...

class AnalyticsService(Protocol):
    """Analytics service interface for data analysis."""
    
    def generate_daily_report(self, date: datetime) -> Dict[str, Any]:
        """Generate a daily analytics report."""
        ...
    
    def get_detection_accuracy_trends(self, days: int = 7) -> Dict[str, List[float]]:
        """Get detection accuracy trends over time."""
        ...
    
    def get_activity_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Analyze activity patterns."""
        ...
    
    def export_data_csv(self, filepath: str, 
                       start_date: datetime, 
                       end_date: datetime) -> None:
        """Export data to CSV file."""
        ...
    
    def create_visualization(self, chart_type: str, 
                           data_range: tuple = None) -> str:
        """Create data visualization. Returns path to saved chart."""
        ... 