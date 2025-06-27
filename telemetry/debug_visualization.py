#!/usr/bin/env python3
"""
Debug Visualization Services

Provides status-based coloring and rendering for debug visualizations following SOLID principles.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Any, Dict

from .interfaces import DebugColorProvider, DebugRenderer


class StateBasedColorProvider:
    """Provides colors based on agent state following the user's specification:
    - Active: Green
    - Idle: Yellow  
    - Run Command: Blue
    - Unknown: Gray
    """
    
    def __init__(self):
        # BGR color tuples for OpenCV
        self._state_colors: Dict[str, Tuple[int, int, int]] = {
            'active': (0, 255, 0),      # Green
            'idle': (0, 255, 255),      # Yellow  
            'run_command': (255, 0, 0), # Blue
            'unknown': (128, 128, 128)  # Gray
        }
        
        # Text colors (same as rectangle colors for consistency)
        self._text_colors: Dict[str, Tuple[int, int, int]] = self._state_colors.copy()
    
    def get_color_for_state(self, state: str) -> Tuple[int, int, int]:
        """Get BGR color tuple for the given agent state."""
        return self._state_colors.get(state.lower(), self._state_colors['unknown'])
    
    def get_text_color_for_state(self, state: str) -> Tuple[int, int, int]:
        """Get BGR color tuple for text associated with the given state."""
        return self._text_colors.get(state.lower(), self._text_colors['unknown'])


class OpenCVDebugRenderer:
    """Renders debug visualizations using OpenCV with dependency injection for color provider."""
    
    def __init__(self, color_provider: DebugColorProvider):
        self._color_provider = color_provider
        self._rectangle_thickness = 3
        self._text_font = cv2.FONT_HERSHEY_SIMPLEX
        self._text_scale = 0.7
        self._text_thickness = 2
    
    def render_detection_overlay(self, 
                                image_array: Any,
                                detection_rect: Tuple[int, int, int, int],
                                state: str,
                                confidence: Optional[float] = None,
                                label: Optional[str] = None) -> Any:
        """Render detection overlay on image array with state-based coloring."""
        if len(detection_rect) < 4:
            return image_array
            
        x, y, w, h = detection_rect[:4]
        
        # Get state-based colors
        rect_color = self._color_provider.get_color_for_state(state)
        text_color = self._color_provider.get_text_color_for_state(state)
        
        # Draw rectangle around detected area
        cv2.rectangle(
            image_array, 
            (int(x), int(y)), 
            (int(x + w), int(y + h)), 
            rect_color, 
            self._rectangle_thickness
        )
        
        # Create and draw label
        if label is None:
            label = self.create_detection_label(state, confidence)
        
        # Position text above the rectangle
        text_y = max(int(y) - 10, 20)
        cv2.putText(
            image_array, 
            label, 
            (int(x), text_y), 
            self._text_font, 
            self._text_scale, 
            text_color, 
            self._text_thickness
        )
        
        return image_array
    
    def create_detection_label(self, 
                              state: str, 
                              confidence: Optional[float] = None) -> str:
        """Create formatted label for detection visualization."""
        label = f"Detected: {state}"
        if confidence is not None:
            label += f" ({confidence:.3f})"
        return label 