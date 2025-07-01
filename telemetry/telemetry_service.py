#!/usr/bin/env python3
"""
Default Telemetry Service

Concrete implementation of TelemetryService using dependency injection.
"""

import json
import uuid
from datetime import datetime, date
from typing import Dict, Any, Optional
from .models import TelemetryEvent, SessionStats, EventType
from .interfaces import TelemetryRepository

class DefaultTelemetryService:
    """Default implementation of TelemetryService with enhanced duration tracking."""
    
    def __init__(self, repository: TelemetryRepository):
        self.repository = repository
        # Session management
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
    
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
        
        event = TelemetryEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            message=message,
            confidence=confidence,
            state=state,
            detection_method=detection_method,
            metadata=metadata,
            duration_seconds=duration_seconds,
            session_id=self.current_session_id
        )
        
        # Parse match_rect if provided
        if match_rect and len(match_rect) >= 4:
            event.match_rect_x = match_rect[0]
            event.match_rect_y = match_rect[1]
            event.match_rect_width = match_rect[2]
            event.match_rect_height = match_rect[3]
        
        self.repository.log_event(event)
    
    def record_event(self, 
                    event_type: EventType,
                    message: str = None,
                    **kwargs) -> None:
        """Record any type of event with flexible parameters."""
        
        # Extract known parameters from kwargs
        confidence = kwargs.get('confidence')
        detection_method = kwargs.get('detection_method')
        state = kwargs.get('state')
        match_rect = kwargs.get('match_rect')
        duration_seconds = kwargs.get('duration_seconds')
        
        # Put remaining kwargs into metadata
        metadata = {k: v for k, v in kwargs.items() 
                   if k not in ['confidence', 'detection_method', 'state', 'match_rect', 'duration_seconds']}
        
        self.record_detection(
            event_type=event_type,
            message=message,
            confidence=confidence,
            detection_method=detection_method,
            state=state,
            match_rect=match_rect,
            metadata=metadata if metadata else None,
            duration_seconds=duration_seconds
        )
    
    def get_recent_stats(self, hours: int = 24) -> SessionStats:
        """Get statistics for recent activity."""
        from datetime import timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        return self.repository.get_session_stats(start_time, end_time)
    
    # Convenience methods for common event types
    def record_idle_detection(self, confidence: float = None, 
                            detection_method: str = None,
                            match_rect: tuple = None,
                            duration_seconds: float = None) -> None:
        """Convenience method for recording idle detections."""
        self.record_detection(
            event_type=EventType.IDLE_DETECTION,
            message="Agent idle state detected",
            confidence=confidence,
            detection_method=detection_method,
            state="idle",
            match_rect=match_rect,
            duration_seconds=duration_seconds
        )
    
    def record_active_detection(self, confidence: float = None, 
                              detection_method: str = None,
                              match_rect: tuple = None,
                              duration_seconds: float = None) -> None:
        """Convenience method for recording active detections."""
        self.record_detection(
            event_type=EventType.ACTIVE_DETECTION,
            message="Agent active state detected",
            confidence=confidence,
            detection_method=detection_method,
            state="active",
            match_rect=match_rect,
            duration_seconds=duration_seconds
        )
    
    def record_run_command_detection(self, confidence: float = None, 
                                   detection_method: str = None,
                                   match_rect: tuple = None,
                                   duration_seconds: float = None) -> None:
        """Convenience method for recording run command detections."""
        self.record_detection(
            event_type=EventType.ACTIVE_DETECTION,  # TODO: Add RUN_COMMAND_DETECTION event type
            message="Agent run command state detected",
            confidence=confidence,
            detection_method=detection_method,
            state="run_command",
            match_rect=match_rect,
            duration_seconds=duration_seconds
        )
    
    def record_state_change(self, old_state: str, new_state: str, duration_seconds: float = None) -> None:
        """Convenience method for recording state changes with duration."""
        self.record_detection(
            event_type=EventType.STATE_CHANGE,
            message=f"State changed from {old_state} to {new_state}",
            state=new_state,
            duration_seconds=duration_seconds,
            metadata={'old_state': old_state, 'new_state': new_state}
        )
    
    # NEW DURATION TRACKING METHODS
    
    def record_state_duration(self, state: str, duration_seconds: float, 
                            confidence: float = None, detection_method: str = None) -> None:
        """Record the duration spent in a specific state."""
        self.record_detection(
            event_type=EventType.STATE_DURATION,
            message=f"Spent {duration_seconds:.1f} seconds in {state} state",
            state=state,
            confidence=confidence,
            detection_method=detection_method,
            duration_seconds=duration_seconds
        )
    
    def get_daily_durations(self, target_date: date) -> Dict[str, float]:
        """Get total duration by state for a specific day."""
        return self.repository.get_daily_durations(target_date)
    
    def get_weekly_durations(self, start_date: date) -> Dict[str, Dict[str, float]]:
        """Get duration breakdown by state for each day in a week."""
        return self.repository.get_weekly_durations(start_date)
    
    def get_monthly_durations(self, month: int, year: int) -> Dict[str, Dict[str, float]]:
        """Get duration breakdown by state for each day in a month."""
        return self.repository.get_monthly_durations(month, year)
    
    def get_cumulative_stats(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get cumulative statistics for a date range."""
        return self.repository.get_cumulative_stats(start_date, end_date)
    
    # SESSION MANAGEMENT METHODS
    
    def start_session(self, config_snapshot: Optional[str] = None) -> str:
        """Start a new monitoring session."""
        if self.current_session_id:
            # End existing session before starting new one
            self.end_session()
        
        self.current_session_id = str(uuid.uuid4())
        self.session_start_time = datetime.now()
        
        # Create session in repository
        self.repository.create_session(self.current_session_id, config_snapshot)
        
        # Record session start event
        self.record_detection(
            event_type=EventType.SESSION_START,
            message=f"Monitoring session started: {self.current_session_id}",
            metadata={'session_id': self.current_session_id, 'config': config_snapshot}
        )
        
        return self.current_session_id
    
    def end_session(self) -> Optional[str]:
        """End the current monitoring session."""
        if not self.current_session_id:
            return None
        
        session_id = self.current_session_id
        
        # Record session end event
        session_duration = (datetime.now() - self.session_start_time).total_seconds() if self.session_start_time else 0
        self.record_detection(
            event_type=EventType.SESSION_END,
            message=f"Monitoring session ended: {session_id}",
            duration_seconds=session_duration,
            metadata={'session_id': session_id, 'total_duration': session_duration}
        )
        
        # Update session in repository
        self.repository.end_session(session_id)
        
        # Clear current session
        self.current_session_id = None
        self.session_start_time = None
        
        return session_id
    
    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self.current_session_id
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        return self.repository.get_session_info(session_id)
    
    def record_app_pause(self) -> None:
        """Record application pause event."""
        self.record_detection(
            event_type=EventType.APP_PAUSE,
            message="Application paused",
            metadata={'session_id': self.current_session_id}
        )
    
    def record_app_resume(self, pause_duration_seconds: float = None) -> None:
        """Record application resume event."""
        self.record_detection(
            event_type=EventType.APP_RESUME,
            message="Application resumed",
            duration_seconds=pause_duration_seconds,
            metadata={'session_id': self.current_session_id, 'pause_duration': pause_duration_seconds}
        ) 