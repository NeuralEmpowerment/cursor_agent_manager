#!/usr/bin/env python3
"""
Default Telemetry Service

Concrete implementation of TelemetryService using dependency injection.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from .models import TelemetryEvent, SessionStats, EventType
from .interfaces import TelemetryRepository

class DefaultTelemetryService:
    """Default implementation of TelemetryService."""
    
    def __init__(self, repository: TelemetryRepository):
        self.repository = repository
    
    def record_detection(self, 
                        event_type: EventType,
                        message: str = None,
                        confidence: float = None, 
                        detection_method: str = None,
                        state: str = None,
                        match_rect: tuple = None,
                        metadata: Dict[str, Any] = None) -> None:
        """Record a detection event with specified type and optional parameters."""
        
        event = TelemetryEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            message=message,
            confidence=confidence,
            state=state,
            detection_method=detection_method,
            metadata=metadata
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
        
        # Put remaining kwargs into metadata
        metadata = {k: v for k, v in kwargs.items() 
                   if k not in ['confidence', 'detection_method', 'state', 'match_rect']}
        
        self.record_detection(
            event_type=event_type,
            message=message,
            confidence=confidence,
            detection_method=detection_method,
            state=state,
            match_rect=match_rect,
            metadata=metadata if metadata else None
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
                            match_rect: tuple = None) -> None:
        """Convenience method for recording idle detections."""
        self.record_detection(
            event_type=EventType.IDLE_DETECTION,
            message="Agent idle state detected",
            confidence=confidence,
            detection_method=detection_method,
            state="idle",
            match_rect=match_rect
        )
    
    def record_active_detection(self, confidence: float = None,
                              detection_method: str = None) -> None:
        """Convenience method for recording active detections."""
        self.record_detection(
            event_type=EventType.ACTIVE_DETECTION,
            message="Agent active state detected",
            confidence=confidence,
            detection_method=detection_method,
            state="active"
        )
    
    def record_detection_failure(self, error_message: str = None) -> None:
        """Convenience method for recording detection failures."""
        self.record_detection(
            event_type=EventType.DETECTION_FAILURE,
            message=error_message or "Detection failed",
            state="unknown"
        )
    
    def record_command_execution(self, command: str) -> None:
        """Convenience method for recording command executions."""
        self.record_detection(
            event_type=EventType.COMMAND_EXECUTION,
            message=f"Executed command: {command}",
            metadata={"command": command}
        )
    
    def record_state_change(self, old_state: str, new_state: str) -> None:
        """Convenience method for recording state changes."""
        self.record_detection(
            event_type=EventType.STATE_CHANGE,
            message=f"State changed from {old_state} to {new_state}",
            state=new_state,
            metadata={"old_state": old_state, "new_state": new_state}
        ) 