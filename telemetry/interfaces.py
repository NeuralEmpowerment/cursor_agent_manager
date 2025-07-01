#!/usr/bin/env python3
"""
Telemetry Interfaces

Abstract interfaces for telemetry systems using Protocol for dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Optional, Dict, Any, Tuple
from datetime import datetime, date
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
    
    # NEW: Duration tracking methods
    def get_daily_durations(self, target_date: date) -> Dict[str, float]:
        """Get total duration by state for a specific day."""
        ...
    
    def get_weekly_durations(self, start_date: date) -> Dict[str, Dict[str, float]]:
        """Get duration breakdown by state for each day in a week."""
        ...
    
    def get_monthly_durations(self, month: int, year: int) -> Dict[str, Dict[str, float]]:
        """Get duration breakdown by state for each day in a month."""
        ...
    
    def get_cumulative_stats(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get cumulative statistics for a date range."""
        ...
    
    # NEW: Session management methods
    def create_session(self, session_id: str, config_snapshot: Optional[str] = None) -> int:
        """Create a new monitoring session."""
        ...
    
    def end_session(self, session_id: str) -> None:
        """End a monitoring session and calculate final statistics."""
        ...
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
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
                        metadata: Dict[str, Any] = None,
                        duration_seconds: float = None) -> None:
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
    
    # NEW: Duration tracking methods
    def record_state_duration(self, state: str, duration_seconds: float, 
                            confidence: float = None, detection_method: str = None) -> None:
        """Record the duration spent in a specific state."""
        ...
    
    def get_daily_durations(self, target_date: date) -> Dict[str, float]:
        """Get total duration by state for a specific day."""
        ...
    
    def get_weekly_durations(self, start_date: date) -> Dict[str, Dict[str, float]]:
        """Get duration breakdown by state for each day in a week."""
        ...
    
    def get_monthly_durations(self, month: int, year: int) -> Dict[str, Dict[str, float]]:
        """Get duration breakdown by state for each day in a month."""
        ...
    
    def get_cumulative_stats(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get cumulative statistics for a date range."""
        ...
    
    # NEW: Session management methods
    def start_session(self, config_snapshot: Optional[str] = None) -> str:
        """Start a new monitoring session."""
        ...
    
    def end_session(self) -> Optional[str]:
        """End the current monitoring session."""
        ...
    
    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        ...
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        ...
    
    def record_app_pause(self) -> None:
        """Record application pause event."""
        ...
    
    def record_app_resume(self, pause_duration_seconds: float = None) -> None:
        """Record application resume event."""
        ...

class AnalyticsService(Protocol):
    """Analytics and reporting service interface."""
    
    def generate_daily_report(self, date: datetime) -> Dict[str, Any]:
        """Generate a comprehensive daily analytics report."""
        ...
    
    def create_activity_chart(self, start_date: datetime, end_date: datetime, 
                            chart_type: str = "timeline") -> str:
        """Create an activity chart and return the file path."""
        ...
    
    def export_data_csv(self, filepath: str, 
                       start_date: datetime, 
                       end_date: datetime) -> None:
        """Export telemetry data to CSV file."""
        ...

class DebugColorProvider(Protocol):
    """Provides colors for debug visualization."""
    
    def get_state_color(self, state: str, confidence: float = None) -> Tuple[int, int, int]:
        """Get RGB color for a given state."""
        ...
    
    def get_confidence_color(self, confidence: float) -> Tuple[int, int, int]:
        """Get RGB color based on confidence level."""
        ...

class DebugRenderer(Protocol):
    """Renders debug overlays on screenshots."""
    
    def render_detection_overlay(self, 
                                screenshot: Any,
                                detections: List[Dict[str, Any]],
                                current_state: str,
                                confidence: float) -> Any:
        """Render detection overlay on screenshot."""
        ... 