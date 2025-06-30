#!/usr/bin/env python3
"""
Cursor Agent Monitor POC (macOS, Cursor IDE)

Advanced architecture with:
1. Modular state detection via Strategy Pattern (Template, OCR, Vision)
2. State machine for agent interaction
3. Input command queue for intelligent IDE control
4. Telemetry logging and structured metrics
5. Diagnostic mode to help test match confidence
6. Simple GUI overlay to control agent (start/stop, mute/unmute)
7. Sound alerts for idle state detection

Dependencies:
    pip install pyautogui pync pytesseract Pillow simpleaudio numpy
"""

import pyautogui
import time
import threading
from pync import Notifier
from datetime import datetime
from typing import Optional, Protocol
from PIL import ImageGrab, Image
import pytesseract
import queue
import simpleaudio as sa
import os
import cv2
import numpy as np
import platform
from enum import Enum, auto
import logging
import AppKit
import objc
from Foundation import NSObject, NSMakeRect, NSMakePoint, NSLayoutConstraint
import signal
import sys
########################################################
# === Configuration ===
########################################################
# === Enhanced Detection Config ===
# Directory-based template loading - just drop images into these folders!
TEMPLATE_DIRECTORIES = {
    "agent_idle": "assets/ui-cursor/agent_idle",
    "agent_active": "assets/ui-cursor/agent_active", 
    "run_command": "assets/ui-cursor/run_command"
}

# Detection parameters
CONFIDENCE_THRESHOLD = 0.8          # Minimum confidence for valid detection
MIN_CONFIDENCE_GAP = 0.08          # Lowered from 0.12 to handle closer matches
REQUIRED_CONFIRMATIONS = 2         # Require 2 consistent detections for stability
MIN_STATE_CHANGE_INTERVAL = 5      # Minimum seconds between state changes (increased for stability)

# Legacy support - you can switch back to simple detector by setting this to True
USE_LEGACY_DETECTOR = False

CHECK_INTERVAL_SEC = 2
TELEMETRY_FILE = "telemetry.json"
AUTO_CLICK_ENABLED = False
OCR_ENABLED = True
COMMAND_QUEUE_ENABLED = True
DIAGNOSTIC_MODE = True

# Enhanced diagnostic output settings
# ===================================
# DIAGNOSTIC_VERBOSITY options:
#   "low"    - Only show state changes and summary every 10 seconds
#   "medium" - Show compact status updates every 5 seconds
#   "high"   - Show all detection details in real-time
DIAGNOSTIC_VERBOSITY = "high"     # Recommended: "low" for clean output

# Output formatting options:
CLEAR_CONSOLE_ON_UPDATE = False  # Clear console before each update (can be jarring)
SHOW_CONFIDENCE_DETAILS = True   # Show detailed confidence scores
USE_COMPACT_OUTPUT = True        # Use single-line status updates (recommended)

# === Agent States ===
class AgentState:
    IDLE = "idle"
    ACTIVE = "active"
    RUN_COMMAND = "run_command"
    UNKNOWN = "unknown"

# State mapping - 1:1 mapping of directories to states
STATE_TEMPLATE_MAPPING = {
    AgentState.IDLE: ["agent_idle"],
    AgentState.ACTIVE: ["agent_active"],
    AgentState.RUN_COMMAND: ["run_command"]
}

# Sound configuration
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio", "alerts")
ALERT_SOUNDS = {
    "idle": "alert_idle_simple.wav",  # New simple two-note sound
    "run_command": "alert_ascending.wav",  # Urgent ascending tone for commands ready to run
    "error": "alert_error.wav",
    "success": "alert_success.wav",
    "thinking": "alert_thinking.wav",
    "completed": "alert_completed.wav",
    "warning": "alert_warning.wav"  # More urgent alternative for run_command
}

# Alert repeat settings
IDLE_ALERT_REPEAT_INTERVAL = 60  # Repeat idle alert every 60 seconds
RUN_COMMAND_ALERT_REPEAT_INTERVAL = 60  # Repeat run_command alert every 60 seconds

# === Enhanced Telemetry with DI ===
from container import initialize_telemetry_system
from telemetry import EventType, TelemetryService

# === Enhanced Console Output Utilities ===
class DiagnosticOutput:
    """Utility class for better formatted diagnostic output."""
    
    def __init__(self):
        self.last_output_time = 0
        self.last_state = None
        self.output_count = 0
        
    def clear_console(self):
        """Clear the console screen."""
        if CLEAR_CONSOLE_ON_UPDATE:
            os.system('cls' if os.name == 'nt' else 'clear')
            
    def print_header(self):
        """Print a formatted header."""
        if DIAGNOSTIC_VERBOSITY in ["medium", "high"]:
            print("=" * 60)
            print(f"  Cursor Agent Monitor - {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 60)
            
    def should_output(self, force=False):
        """Determine if we should output based on verbosity settings."""
        if force:
            return True
            
        current_time = time.time()
        
        if DIAGNOSTIC_VERBOSITY == "low":
            # Only output on state changes or every 10 seconds
            return current_time - self.last_output_time > 10
        elif DIAGNOSTIC_VERBOSITY == "medium":
            # Output every cycle but with reduced verbosity
            return True
        else:  # high
            # Output everything
            return True
            
    def format_status(self, state, confidence, stable_state=None):
        """Format the current status in a clean way."""
        # Ensure confidence is not None
        if confidence is None:
            conf_str = "None"
        elif isinstance(confidence, (int, float)):
            conf_str = f"{confidence:.2f}"
        else:
            conf_str = str(confidence)
            
        if USE_COMPACT_OUTPUT:
            # Single line status update with timestamp
            timestamp = datetime.now().strftime('%H:%M:%S')
            status_line = f"[{timestamp}] {state:<10} (conf: {conf_str})"
            if stable_state is not None and stable_state != state:
                status_line += f" → {stable_state}"
            return status_line
        else:
            status_line = f"State: {state:<10} | Confidence: {conf_str}"
            if stable_state is not None:
                status_line += f" | Stable: {stable_state}"
            return status_line
        
    def format_confidences(self, state_confidences):
        """Format confidence scores in a compact way."""
        if not SHOW_CONFIDENCE_DETAILS or not state_confidences:
            return ""
            
        conf_items = []
        for state, conf in state_confidences.items():
            # Ensure confidence is not None and is a valid number
            if conf is None:
                conf_str = "None"
            elif isinstance(conf, (int, float)):
                conf_str = f"{conf:.2f}"
            else:
                conf_str = str(conf)
            conf_items.append(f"{state}: {conf_str}")
            
        if USE_COMPACT_OUTPUT:
            return " | " + " | ".join(conf_items)
        else:
            return "Confidences: " + " | ".join(conf_items)
            
    def print_status_update(self, state, confidence, stable_state, state_confidences):
        """Print a formatted status update."""
        if USE_COMPACT_OUTPUT:
            # Single line with all info
            status_line = self.format_status(state, confidence, stable_state)
            if SHOW_CONFIDENCE_DETAILS:
                status_line += self.format_confidences(state_confidences)
            print(status_line)
        else:
            # Multi-line format
            print(self.format_status(state, confidence, stable_state))
            if SHOW_CONFIDENCE_DETAILS:
                conf_line = self.format_confidences(state_confidences)
                if conf_line:
                    print(conf_line)

# Global diagnostic output instance
diagnostic_output = DiagnosticOutput()

class LegacyTelemetryAdapter:
    """Adapter to maintain compatibility with existing code while using new telemetry system."""
    
    def __init__(self, telemetry_service: TelemetryService):
        self.telemetry_service = telemetry_service
        self.idle_detections = 0
        self.detection_failures = 0
        self.last_idle_detection = None
        
        # Initialize stats from database
        self._sync_stats()
    
    def _sync_stats(self):
        """Sync stats with database."""
        try:
            stats = self.telemetry_service.get_recent_stats(hours=24)
            self.idle_detections = stats.total_idle_detections
            self.detection_failures = stats.total_detection_failures
            if stats.last_event:
                self.last_idle_detection = stats.last_event.timestamp()
        except:
            pass  # Use defaults if database isn't available
    
    def log_event(self, msg: str):
        """Log a generic info event."""
        self.telemetry_service.record_detection(
            event_type=EventType.INFO,
            message=msg
        )

    def record_detection(self, confidence: float = None, detection_method: str = None, match_rect: tuple = None):
        """Record an idle detection."""
        self.idle_detections += 1
        self.last_idle_detection = time.time()
        
        self.telemetry_service.record_detection(
            event_type=EventType.IDLE_DETECTION,
            message="Agent idle state detected",
            confidence=confidence,
            detection_method=detection_method,
            state="idle",
            match_rect=match_rect
        )

    def record_active_detection(self, confidence: float = None, detection_method: str = None, match_rect: tuple = None):
        """Record an active detection."""
        self.telemetry_service.record_detection(
            event_type=EventType.ACTIVE_DETECTION,
            message="Agent active state detected",
            confidence=confidence,
            detection_method=detection_method,
            state="active",
            match_rect=match_rect
        )

    def record_failure(self, error_message: str = None):
        """Record a detection failure."""
        self.detection_failures += 1
        
        self.telemetry_service.record_detection(
            event_type=EventType.DETECTION_FAILURE,
            message=error_message or "Failed to detect agent state",
            state="unknown"
        )

# === Template Loading Utilities ===
def load_templates_from_directories(template_dirs: dict, state_mapping: dict):
    """Load all template images from organized directories."""
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    
    # Dictionary to store templates by state
    state_templates = {
        AgentState.IDLE: [],
        AgentState.ACTIVE: [],
        AgentState.RUN_COMMAND: []
    }
    
    # Load templates for each state
    for state, dir_names in state_mapping.items():
        for dir_name in dir_names:
            dir_path = template_dirs.get(dir_name)
            if not dir_path or not os.path.exists(dir_path):
                print(f"[WARNING] Template directory not found: {dir_path}")
                continue
                
            # Load all image files from directory
            try:
                files = os.listdir(dir_path)
                image_files = [f for f in files if f.lower().endswith(supported_formats)]
                
                for image_file in image_files:
                    full_path = os.path.join(dir_path, image_file)
                    state_templates[state].append(full_path)
                    
                print(f"[INFO] Loaded {len(image_files)} templates from {dir_name}/ directory")
                
            except Exception as e:
                print(f"[ERROR] Failed to load templates from {dir_path}: {e}")
    
    return state_templates

# === Detection Engine Interface ===
class StateDetector(Protocol):
    def detect_state(self) -> str:
        ...

# === Enhanced Multi-Template Detection Engine ===
class EnhancedTemplateMatchDetector:
    def __init__(self, state_templates: dict, confidence_threshold=0.8, min_confidence_gap=0.1):
        self.state_templates = state_templates
        self.confidence_threshold = confidence_threshold
        self.min_confidence_gap = min_confidence_gap
        self.last_confidence = None
        self.state_confidences = {}  # Store confidence for each state
        self._last_match_rect = None
        self._detection_history = []  # For state stability
        self._last_state_change = 0
        self._min_state_change_interval = MIN_STATE_CHANGE_INTERVAL
        self._required_confirmations = REQUIRED_CONFIRMATIONS
        
        # Load all template images by state
        self.loaded_templates = {}
        
        for state, template_paths in state_templates.items():
            self.loaded_templates[state] = []
            for template_path in template_paths:
                if not os.path.exists(template_path):
                    print(f"[WARNING] Template not found: {template_path}")
                    continue
                img = cv2.imread(template_path)
                if img is not None:
                    self.loaded_templates[state].append((template_path, img))
                    print(f"[INFO] Loaded {state} template: {template_path} ({img.shape})")
                else:
                    print(f"[ERROR] Failed to load template: {template_path}")
        
        # Verify we have templates for the main states
        if not self.loaded_templates.get(AgentState.IDLE) or not self.loaded_templates.get(AgentState.ACTIVE):
            raise RuntimeError("Failed to load template images for required states (idle and active)")

    def _match_templates(self, img, template_list, state_name):
        """Match multiple templates and return the best match."""
        best_confidence = 0
        best_rect = None
        best_template_name = None
        
        # Convert PIL image to OpenCV format once
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        for template_path, template in template_list:
            # Get dimensions
            h, w = template.shape[:2]
            
            # Template matching
            result = cv2.matchTemplate(img_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_rect = (max_loc[0], max_loc[1], w, h)
                best_template_name = os.path.basename(template_path)
        
        if DIAGNOSTIC_MODE and DIAGNOSTIC_VERBOSITY == "high" and best_confidence > 0.5:
            template_info = best_template_name if best_template_name else "no template"
            print(f"[DIAGNOSTIC] Best {state_name} match: {best_confidence:.2f} ({template_info})")
            
            # DIAGNOSTIC: High confidence detection (only show if chosen but not final winner)
            if best_confidence >= 0.99 and state_name == "idle":
                print(f"[DIAGNOSTIC] Perfect idle match: {best_confidence:.2f} ({template_info})")
                print(f"[DIAGNOSTIC] Note: Perfect matches are good if the state is actually idle!")
        
        return best_confidence, best_rect, best_template_name

    def _is_state_change_allowed(self):
        """Check if enough time has passed since last state change."""
        return time.time() - self._last_state_change > self._min_state_change_interval

    def _add_to_history(self, state):
        """Add detection to history for state stability."""
        current_time = time.time()
        # Keep only recent history (last 10 seconds)
        self._detection_history = [(t, s) for t, s in self._detection_history if current_time - t < 10]
        self._detection_history.append((current_time, state))

    def _get_stable_state(self, current_detection):
        """Determine if we have enough consistent detections for a stable state."""
        self._add_to_history(current_detection)
        
        if len(self._detection_history) < self._required_confirmations:
            return None
        
        # Check if last N detections are consistent
        recent_states = [state for _, state in self._detection_history[-self._required_confirmations:]]
        if all(state == current_detection for state in recent_states):
            return current_detection
        
        return None

    def detect_state(self) -> str:
        try:
            # Take a screenshot
            screenshot = pyautogui.screenshot()
            
            # Match templates for all states
            state_results = {}
            for state, template_list in self.loaded_templates.items():
                if template_list:  # Only check states that have templates
                    try:
                        confidence, rect, template_name = self._match_templates(screenshot, template_list, state)
                        state_results[state] = {
                            'confidence': confidence,
                            'rect': rect,
                            'template': template_name
                        }
                    except Exception as e:
                        if DIAGNOSTIC_MODE:
                            print(f"[WARNING] Template matching failed for {state}: {e}")
                        # Set defaults for failed state
                        state_results[state] = {
                            'confidence': 0.0,
                            'rect': None,
                            'template': None
                        }
            
            # Store all confidences for debugging - ensure no None values
            self.state_confidences = {}
            for state, result in state_results.items():
                confidence = result.get('confidence', 0.0)
                self.state_confidences[state] = confidence if confidence is not None else 0.0
            
            # SMART WARNING: Check for potentially too-generic templates
            high_confidence_states = [(state, conf) for state, conf in self.state_confidences.items() if conf >= 0.95]
            if len(high_confidence_states) > 1 and DIAGNOSTIC_MODE:
                print(f"[⚠️  TEMPLATE WARNING] Multiple states with suspiciously high confidence!")
                for state, conf in high_confidence_states:
                    print(f"[⚠️  TEMPLATE WARNING]   {state}: {conf:.3f}")
                print(f"[⚠️  TEMPLATE WARNING] Consider making templates more distinctive to avoid false matches.")
            
            # Find the best matching state
            valid_states = {}
            for state, result in state_results.items():
                if result['confidence'] >= self.confidence_threshold:
                    valid_states[state] = result
            
            detected_state = AgentState.UNKNOWN
            
            if len(valid_states) == 0:
                # No state meets threshold
                detected_state = AgentState.UNKNOWN
            elif len(valid_states) == 1:
                # Only one state valid - use it
                state = list(valid_states.keys())[0]
                result = valid_states[state]
                detected_state = state
                self.last_confidence = result['confidence']
                self._last_match_rect = result['rect']
            else:
                # Multiple states valid - FIXED PRIORITY LOGIC: Choose highest confidence with smart run_command priority
                sorted_states = sorted(valid_states.items(), key=lambda x: x[1]['confidence'], reverse=True)
                
                detected_state = AgentState.UNKNOWN
                chosen_result = None
                
                best_state, best_result = sorted_states[0]
                second_state, second_result = sorted_states[1] if len(sorted_states) > 1 else (None, {'confidence': 0.0})
                
                confidence_gap = best_result['confidence'] - second_result['confidence']
                
                # FIXED LOGIC: Always prioritize run_command when it meets threshold (regardless of confidence vs other states)
                # Priority 1: Run command (always prioritized if above threshold - needs immediate user action)
                if AgentState.RUN_COMMAND in valid_states:
                    detected_state = AgentState.RUN_COMMAND
                    chosen_result = valid_states[AgentState.RUN_COMMAND]
                    
                # Priority 2: Highest confidence wins (fixed from arbitrary active/idle priority)
                elif confidence_gap >= self.min_confidence_gap:
                    # Clear winner based on confidence
                    detected_state = best_state
                    chosen_result = best_result
                else:
                    # Too close - stay unknown to avoid flickering
                    detected_state = AgentState.UNKNOWN
                    if DIAGNOSTIC_MODE and DIAGNOSTIC_VERBOSITY == "high":
                        print(f"[DIAGNOSTIC] Confidence gap too small ({confidence_gap:.2f}) between {best_state} and {second_state}")
                
                # Set results if we chose a state
                if chosen_result:
                    self.last_confidence = chosen_result['confidence']
                    self._last_match_rect = chosen_result['rect']
                    
                    if DIAGNOSTIC_MODE and DIAGNOSTIC_VERBOSITY == "high":
                        if detected_state == AgentState.RUN_COMMAND:
                            idle_conf = valid_states.get(AgentState.IDLE, {}).get('confidence', 0.0)
                            active_conf = valid_states.get(AgentState.ACTIVE, {}).get('confidence', 0.0)
                            print(f"[DIAGNOSTIC] RUN_COMMAND chosen (run:{chosen_result['confidence']:.2f} vs idle:{idle_conf:.2f} vs active:{active_conf:.2f})")
                        else:
                            print(f"[DIAGNOSTIC] Selected {detected_state} with confidence {chosen_result['confidence']:.2f} (gap: {confidence_gap:.2f})")
            
            # Apply state stability check
            stable_state = self._get_stable_state(detected_state)
            
            # EXTRA DEBUG: Log state decision process
            if DIAGNOSTIC_MODE and DIAGNOSTIC_VERBOSITY == "high":
                if detected_state != AgentState.UNKNOWN:
                    print(f"[STATE_LOGIC] Raw Detection: {detected_state} | Stable State: {stable_state}")
                    if stable_state != detected_state:
                        print(f"[STATE_LOGIC] Waiting for more confirmations ({len(self._detection_history)}/{self._required_confirmations})")
            
            # Enhanced diagnostic output with better formatting
            if DIAGNOSTIC_MODE and diagnostic_output.should_output():
                confidence = self.last_confidence if hasattr(self, 'last_confidence') else 0.0
                
                # Only show output on state changes or based on verbosity
                show_output = False
                if stable_state != diagnostic_output.last_state:
                    show_output = True
                elif DIAGNOSTIC_VERBOSITY == "high":
                    show_output = True
                elif DIAGNOSTIC_VERBOSITY == "medium" and time.time() - diagnostic_output.last_output_time > 5:
                    show_output = True
                    
                if show_output:
                    # Clear console for clean display only on state changes
                    if stable_state != diagnostic_output.last_state and CLEAR_CONSOLE_ON_UPDATE:
                        diagnostic_output.clear_console()
                        diagnostic_output.print_header()
                    
                    # Print formatted status update
                    diagnostic_output.print_status_update(
                        detected_state, confidence, stable_state, self.state_confidences
                    )
                    
                    diagnostic_output.last_state = stable_state
                    diagnostic_output.last_output_time = time.time()
            
            # Only return stable state if we have enough confirmations
            if stable_state is not None:
                if stable_state != AgentState.UNKNOWN:
                    self._last_state_change = time.time()
                return stable_state
            
            # If no stable state yet, return current detection but don't change timestamp
            return detected_state
                
        except Exception as e:
            print(f"[ERROR] Enhanced template matching error: {str(e)}")
            return AgentState.UNKNOWN

# === OCR Strategy ===
class OCRDetector:
    def detect_state(self) -> str:
        try:
            screenshot = ImageGrab.grab()
            text = pytesseract.image_to_string(screenshot)
            # FIXME: These are not valid for idle states, to remove
            if "Start a new chat" in text or "Accept" in text:
                return AgentState.IDLE
            # FIXME: "Generating" is a valid active state
            return AgentState.ACTIVE
        except Exception as e:
            print(f"[ERROR] OCR detection failed: {e}")
            return AgentState.UNKNOWN

# === Command Queue ===
class CommandExecutor:
    def __init__(self):
        self.queue = queue.Queue()

    def add_command(self, command: str):
        self.queue.put(command)

    def process_next(self):
        if not self.queue.empty():
            command = self.queue.get()
            pyautogui.write(command)
            pyautogui.press('enter')
            return command
        return None

# === Sound Player ===
class SoundPlayer:
    def __init__(self):
        self._cache = {}
        self._current_play = None
        
    def play_sound(self, sound_type: str):
        if sound_type not in ALERT_SOUNDS:
            return
            
        sound_path = os.path.join(AUDIO_DIR, ALERT_SOUNDS[sound_type])
        if not os.path.exists(sound_path):
            print(f"[WARNING] Sound file not found: {sound_path}")
            return
            
        try:
            if sound_path not in self._cache:
                self._cache[sound_path] = sa.WaveObject.from_wave_file(sound_path)
                
            # Stop current sound if playing
            if self._current_play and self._current_play.is_playing():
                self._current_play.stop()
                
            self._current_play = self._cache[sound_path].play()
        except Exception as e:
            print(f"[ERROR] Failed to play sound: {e}")

# === Cursor Agent Monitor ===
class AgentMonitor:
    def __init__(self, detectors: list, telemetry: LegacyTelemetryAdapter, executor: Optional[CommandExecutor] = None):
        self.detectors = detectors
        self.telemetry = telemetry
        self.executor = executor
        self.state = AgentState.UNKNOWN
        self.muted = False
        self.running = True
        self.paused = False
        self.sound_player = SoundPlayer()
        self.last_confidence = None
        self.current_state = AgentState.UNKNOWN
        self.last_screenshot = None
        self.last_detection_rect = None
        # Enhanced state tracking to prevent unnecessary notifications
        self.last_stable_state = AgentState.UNKNOWN
        self.last_notification_time = 0
        self.min_notification_interval = 5  # Minimum seconds between same-type notifications
        # Idle alert repeat functionality
        self.idle_start_time = None  # When idle state started
        self.last_idle_alert_time = 0  # Last time we played idle alert
        # Run command alert repeat functionality
        self.run_command_start_time = None  # When run_command state started
        self.last_run_command_alert_time = 0  # Last time we played run_command alert

    def _should_notify_state_change(self, new_state):
        """Determine if we should notify about a state change to prevent spam."""
        current_time = time.time()
        
        # Always notify if it's a different type of state change
        if new_state != self.last_stable_state:
            return True
            
        # Don't notify if same state and too soon since last notification
        if current_time - self.last_notification_time < self.min_notification_interval:
            return False
            
        return True

    def _check_idle_repeat_alert(self):
        """Check if we should play a repeating idle alert."""
        current_time = time.time()
        
        # Only check if we're in idle state and not muted
        if self.state != AgentState.IDLE or self.muted or self.paused:
            return
            
        # If we just entered idle state, set the start time
        if self.idle_start_time is None:
            self.idle_start_time = current_time
            self.last_idle_alert_time = current_time  # Count initial alert
            return
            
        # Check if enough time has passed since last alert
        time_since_last_alert = current_time - self.last_idle_alert_time
        if time_since_last_alert >= IDLE_ALERT_REPEAT_INTERVAL:
            # Play the idle alert again
            self.sound_player.play_sound("idle")
            self.last_idle_alert_time = current_time
            
            # Optional: Also show notification for repeat alerts
            idle_duration = int(current_time - self.idle_start_time)
            Notifier.notify(f"Still idle after {idle_duration // 60}:{idle_duration % 60:02d}", title="Agent Watcher")

    def _check_run_command_repeat_alert(self):
        """Check if we should play a repeating run_command alert."""
        current_time = time.time()
        
        # Only check if we're in run_command state and not muted
        if self.state != AgentState.RUN_COMMAND or self.muted or self.paused:
            return
            
        # If we just entered run_command state, set the start time
        if self.run_command_start_time is None:
            self.run_command_start_time = current_time
            self.last_run_command_alert_time = current_time  # Count initial alert
            return
            
        # Check if enough time has passed since last alert
        time_since_last_alert = current_time - self.last_run_command_alert_time
        if time_since_last_alert >= RUN_COMMAND_ALERT_REPEAT_INTERVAL:
            # Play the run_command alert again
            self.sound_player.play_sound("run_command")
            self.last_run_command_alert_time = current_time
            
            # Show notification for repeat alerts
            command_duration = int(current_time - self.run_command_start_time)
            Notifier.notify(f"🚨 COMMAND STILL WAITING - {command_duration // 60}:{command_duration % 60:02d} elapsed", title="Agent Monitor - URGENT")

    def _reset_idle_tracking(self):
        """Reset idle state tracking when leaving idle."""
        self.idle_start_time = None
        self.last_idle_alert_time = 0

    def _reset_run_command_tracking(self):
        """Reset run_command state tracking when leaving run_command."""
        self.run_command_start_time = None
        self.last_run_command_alert_time = 0

    def scan_and_act(self):
        if not self.running or self.paused:
            return

        # Take screenshot once for all detectors
        self.last_screenshot = pyautogui.screenshot()
        self.last_detection_rect = None
        
        detection_successful = False

        # Use the enhanced detector (priority logic now handled in detector)
        detected_state = self.detectors[0].detect_state()  # Primary detector with priority logic
        confidence = getattr(self.detectors[0], 'last_confidence', 0.0)
        
        # Update monitor state
        state = detected_state
        self.current_state = state
        self.last_confidence = confidence
        
        # Update detection rectangle from detector
        if hasattr(self.detectors[0], '_last_match_rect'):
            self.last_detection_rect = self.detectors[0]._last_match_rect
        
        best_detector = self.detectors[0]
        
        # DEBUG: Log detection decision
        if DIAGNOSTIC_MODE and DIAGNOSTIC_VERBOSITY == "high":
            if state != AgentState.UNKNOWN:
                print(f"[DETECTOR_WINNER] {best_detector.__class__.__name__} detected {state} (conf: {confidence:.3f})")
            else:
                print(f"[DETECTOR_WINNER] No detector met thresholds")
        
        # === STATE HANDLING LOGIC (MOVED OUTSIDE DIAGNOSTIC BLOCK) ===
        if state == AgentState.IDLE:
            # Handle idle state (agent waiting for input)
            if self.state != AgentState.IDLE:
                # Reset tracking if coming from a different state
                self._reset_idle_tracking()
                if self.state == AgentState.RUN_COMMAND:
                    self._reset_run_command_tracking()
                
                self.state = AgentState.IDLE
                
                # Record detection with enhanced telemetry
                self.telemetry.record_detection(
                    confidence=self.last_confidence,
                    detection_method=best_detector.__class__.__name__,
                    match_rect=self.last_detection_rect
                )
                
                # Only notify if it's appropriate (not spam)
                if self._should_notify_state_change(AgentState.IDLE):
                    self.last_stable_state = AgentState.IDLE
                    self.last_notification_time = time.time()
                    
                    Notifier.notify("Agent idle – input may be needed", title="Agent Watcher")
                        
                    if not self.muted:
                        self.sound_player.play_sound("idle")
                    
                    if AUTO_CLICK_ENABLED:
                        pyautogui.press("enter")
                    if self.executor:
                        cmd = self.executor.process_next()
                        if cmd:
                            self.telemetry.log_event(f"Executed command: {cmd}")
            
            # Check for repeating idle alerts
            self._check_idle_repeat_alert()
            detection_successful = True
            return
            
        elif state == AgentState.RUN_COMMAND:
            # Handle run command state (waiting for user to accept/execute)
            if self.state != AgentState.RUN_COMMAND:
                # Reset run_command tracking if coming from a different state
                self._reset_run_command_tracking()
                
                self.state = AgentState.RUN_COMMAND
                
                # Record detection with enhanced telemetry
                self.telemetry.record_detection(
                    confidence=self.last_confidence,
                    detection_method=best_detector.__class__.__name__,
                    match_rect=self.last_detection_rect
                )
                
                # Only notify if it's appropriate (not spam)
                if self._should_notify_state_change(AgentState.RUN_COMMAND):
                    self.last_stable_state = AgentState.RUN_COMMAND
                    self.last_notification_time = time.time()
                    
                    # SPECIAL NOTIFICATION for run commands
                    Notifier.notify("🚨 COMMAND READY - Click Accept/Run to continue!", title="Agent Monitor - Action Required")
                        
                    if not self.muted:
                        # Use the dedicated run_command sound (ascending tone)
                        self.sound_player.play_sound("run_command")
                    
                    # Optional: Auto-click if enabled
                    if AUTO_CLICK_ENABLED:
                        # Could add logic to auto-click the accept button
                        pyautogui.press("enter")
            
            # Check for repeating run_command alerts (like idle)
            self._check_run_command_repeat_alert()
            detection_successful = True
            return
            
        elif state == AgentState.ACTIVE:
            # Reset tracking when becoming active
            if self.state == AgentState.IDLE:
                self._reset_idle_tracking()
            elif self.state == AgentState.RUN_COMMAND:
                self._reset_run_command_tracking()
            
            # Only update main state and notify if this is a meaningful state change
            if self.state != AgentState.ACTIVE:
                self.state = AgentState.ACTIVE
                
                # Record active detection with enhanced telemetry
                self.telemetry.record_active_detection(
                    confidence=self.last_confidence,
                    detection_method=best_detector.__class__.__name__,
                    match_rect=self.last_detection_rect
                )
                
                # Only notify if it's appropriate (not spam)
                if self._should_notify_state_change(AgentState.ACTIVE):
                    self.last_stable_state = AgentState.ACTIVE
                    self.last_notification_time = time.time()
                    
                    # Optional: Add sound for active state (currently no sound for active)
                    # if not self.muted:
                    #     self.sound_player.play_sound("thinking")
                
            detection_successful = True
            
        elif state == AgentState.UNKNOWN:
            # Don't change main state for unknown - but still update current detection for UI
            pass

        # Only record failure if we couldn't detect any state at all
        if not detection_successful and self.current_state == AgentState.UNKNOWN:
            self.telemetry.record_failure("Unable to detect any agent state")

    def toggle_running(self):
        self.paused = not self.paused
        # NOTE: Disabling sounds for pause and unpause temporarily,
        # but can be enabled in the future
        # if not self.muted:
        #     if not self.paused:
        #         self.sound_player.play_sound("success")
        #     else:
        #         self.sound_player.play_sound("error")

    def toggle_muted(self):
        self.muted = not self.muted
        
    def pause(self):
        self.paused = True
        
    def resume(self):
        self.paused = False

# === GUI Control Panel ===
class ControlPanel(NSObject):
    def initWithMonitor_debugRenderer_(self, monitor, debug_renderer):
        self = objc.super(ControlPanel, self).init()
        if self is None:
            return None
            
        self.monitor = monitor
        self.debug_renderer = debug_renderer
        self.debug_window = None
        self.show_debug = False
        self.alpha = 0.95
        
        # Create the window - sized for 2x2 grid layout
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 240, 260),  # Proper size for 2x2 button grid
            AppKit.NSWindowStyleMaskTitled | 
            AppKit.NSWindowStyleMaskClosable | 
            AppKit.NSWindowStyleMaskResizable |
            AppKit.NSWindowStyleMaskFullSizeContentView,
            AppKit.NSBackingStoreBuffered,
            False
        )
        
        # Configure window properties
        self.window.setTitle_("Cursor Agent Monitor")
        self.window.setTitlebarAppearsTransparent_(True)
        self.window.setLevel_(AppKit.NSFloatingWindowLevel)
        self.window.setMovableByWindowBackground_(True)
        
        # Set minimum and maximum size to prevent content overflow
        self.window.setMinSize_(NSMakePoint(220, 240))
        self.window.setMaxSize_(NSMakePoint(300, 320))
        
        # Create main view
        self.content_view = AppKit.NSView.alloc().init()
        self.window.setContentView_(self.content_view)
        
        bg_color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.2, 0.2, self.alpha)
        self.window.setBackgroundColor_(bg_color)
        
        self._setup_ui_with_autolayout()
        
        # Position and show the window
        screen = AppKit.NSScreen.mainScreen()
        screen_rect = screen.frame()
        window_rect = self.window.frame()
        x = screen_rect.size.width - window_rect.size.width - 20
        y = screen_rect.size.height - window_rect.size.height - 40
        self.window.setFrameOrigin_(NSMakePoint(x, y))
        self.window.makeKeyAndOrderFront_(None)
        
        self._createMenu()
        
        self.update_timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, objc.selector(self.updateDisplay_, signature=b"v@:"), None, True
        )
        
        return self

    def _setup_ui_with_autolayout(self):
        """Create and layout UI components using Auto Layout - Responsive 2x2 Grid Design."""
        self.stats_window = None
        self.show_stats = False
        
        # --- Helpers to create styled UI elements without frames ---
        def create_label(panel_self, text, size=12, is_bold=False, align='center'):
            label = AppKit.NSTextField.alloc().init()
            label.setStringValue_(text)
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            font = AppKit.NSFont.boldSystemFontOfSize_(size) if is_bold else AppKit.NSFont.systemFontOfSize_(size)
            label.setFont_(font)
            label.setTextColor_(AppKit.NSColor.controlTextColor())
            if align == 'right': 
                label.setAlignment_(AppKit.NSTextAlignmentRight)
            elif align == 'center': 
                label.setAlignment_(AppKit.NSTextAlignmentCenter)
            else: 
                label.setAlignment_(AppKit.NSTextAlignmentLeft)
            label.setTranslatesAutoresizingMaskIntoConstraints_(False)
            panel_self.content_view.addSubview_(label)
            return label

        def create_button(panel_self, title, size=12):
            button = AppKit.NSButton.alloc().init()
            button.setTitle_(title)
            button.setBezelStyle_(AppKit.NSBezelStyleRounded)
            button.setFont_(AppKit.NSFont.systemFontOfSize_(size))
            button.setTranslatesAutoresizingMaskIntoConstraints_(False)
            panel_self.content_view.addSubview_(button)
            return button

        # --- Create UI Elements with Proper Responsive Layout ---
        
        # Title (properly centered, no duplication)
        self.title_label = create_label(self, "", 16, is_bold=True, align='center')
        # self.title_label = create_label(self, "Cursor Agent Monitor", 16, is_bold=True, align='center')
        
        # Settings button (top right)
        self.settings_btn = create_button(self, "⚙️", 14)
        self.settings_btn.setTarget_(self)
        self.settings_btn.setAction_(objc.selector(self.toggleAlphaSlider_, signature=b"v@:"))
        
        # Alpha slider (hidden by default)
        self.alpha_slider = AppKit.NSSlider.alloc().init()
        self.alpha_slider.setMinValue_(0.2)
        self.alpha_slider.setMaxValue_(1.0)
        self.alpha_slider.setFloatValue_(self.alpha)
        self.alpha_slider.setTarget_(self)
        self.alpha_slider.setAction_(objc.selector(self.changeAlpha_, signature=b"v@:"))
        self.alpha_slider.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.alpha_slider.setHidden_(True)
        self.content_view.addSubview_(self.alpha_slider)

        # Status display (properly centered)
        self.status_state_label = create_label(self, "❓ Unknown • Running", 14, is_bold=True, align='center')
        self.confidence_label = create_label(self, "Confidence: -", 11, align='center')

        # 2x2 Button Grid Layout
        self.toggle_btn = create_button(self, "⏸️", 16)  # Top-left
        self.toggle_btn.setTarget_(self)
        self.toggle_btn.setAction_(objc.selector(self.toggleMonitor_, signature=b"v@:"))
        
        self.mute_btn = create_button(self, "🔊", 16)  # Top-right
        self.mute_btn.setTarget_(self)
        self.mute_btn.setAction_(objc.selector(self.toggleMute_, signature=b"v@:"))
        
        self.stats_btn = create_button(self, "📊", 16)  # Bottom-left
        self.stats_btn.setTarget_(self)
        self.stats_btn.setAction_(objc.selector(self.toggleStatsWindow_, signature=b"v@:"))
        
        self.debug_btn = create_button(self, "🐛", 16)  # Bottom-right
        self.debug_btn.setTarget_(self)
        self.debug_btn.setAction_(objc.selector(self.toggleDebugView_, signature=b"v@:"))

        # --- Responsive Constraints for Proper Centering and 2x2 Grid ---
        padding = 16
        button_spacing = 8
        
        NSLayoutConstraint.activateConstraints_([
            # Title - properly centered across full width
            self.title_label.topAnchor().constraintEqualToAnchor_constant_(self.content_view.topAnchor(), padding),
            self.title_label.centerXAnchor().constraintEqualToAnchor_(self.content_view.centerXAnchor()),
            self.title_label.leadingAnchor().constraintGreaterThanOrEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.title_label.trailingAnchor().constraintLessThanOrEqualToAnchor_constant_(self.settings_btn.leadingAnchor(), -8),

            # Settings button - top right corner
            self.settings_btn.topAnchor().constraintEqualToAnchor_constant_(self.content_view.topAnchor(), padding),
            self.settings_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            self.settings_btn.widthAnchor().constraintEqualToConstant_(32),
            self.settings_btn.heightAnchor().constraintEqualToConstant_(32),

            # Alpha slider - full width, hidden by default
            self.alpha_slider.topAnchor().constraintEqualToAnchor_constant_(self.title_label.bottomAnchor(), 8),
            self.alpha_slider.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.alpha_slider.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            self.alpha_slider.heightAnchor().constraintEqualToConstant_(20),

            # Status display - centered
            self.status_state_label.topAnchor().constraintEqualToAnchor_constant_(self.alpha_slider.bottomAnchor(), padding),
            self.status_state_label.centerXAnchor().constraintEqualToAnchor_(self.content_view.centerXAnchor()),
            self.status_state_label.leadingAnchor().constraintGreaterThanOrEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.status_state_label.trailingAnchor().constraintLessThanOrEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),

            self.confidence_label.topAnchor().constraintEqualToAnchor_constant_(self.status_state_label.bottomAnchor(), 4),
            self.confidence_label.centerXAnchor().constraintEqualToAnchor_(self.content_view.centerXAnchor()),
            self.confidence_label.leadingAnchor().constraintGreaterThanOrEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.confidence_label.trailingAnchor().constraintLessThanOrEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),

            # 2x2 Button Grid - properly centered and responsive
            # Top row buttons
            self.toggle_btn.topAnchor().constraintEqualToAnchor_constant_(self.confidence_label.bottomAnchor(), padding),
            self.toggle_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.toggle_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.centerXAnchor(), -button_spacing/2),
            self.toggle_btn.heightAnchor().constraintEqualToConstant_(40),

            self.mute_btn.topAnchor().constraintEqualToAnchor_(self.toggle_btn.topAnchor()),
            self.mute_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.centerXAnchor(), button_spacing/2),
            self.mute_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            self.mute_btn.heightAnchor().constraintEqualToConstant_(40),

            # Bottom row buttons
            self.stats_btn.topAnchor().constraintEqualToAnchor_constant_(self.toggle_btn.bottomAnchor(), button_spacing),
            self.stats_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.stats_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.centerXAnchor(), -button_spacing/2),
            self.stats_btn.heightAnchor().constraintEqualToConstant_(40),

            self.debug_btn.topAnchor().constraintEqualToAnchor_(self.stats_btn.topAnchor()),
            self.debug_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.centerXAnchor(), button_spacing/2),
            self.debug_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            self.debug_btn.heightAnchor().constraintEqualToConstant_(40),

            # Bottom constraint - ensure proper window height
            self.stats_btn.bottomAnchor().constraintLessThanOrEqualToAnchor_constant_(self.content_view.bottomAnchor(), -padding),
        ])



    def updateDisplay_(self, timer):
        """Update the display with current status."""
        # Update state display with emojis
        state = self.monitor.current_state if self.monitor.current_state else "Unknown"
        status = "Paused" if self.monitor.paused else "Running"
        
        # Add emojis based on state
        if state == "idle":
            state_with_emoji = "💤 idle"
        elif state == "active":
            state_with_emoji = "🚀 active"
        elif state == "run_command":
            state_with_emoji = "⚡ run_command"
        else:
            state_with_emoji = "❓ Unknown"
            
        self.status_state_label.setStringValue_(f"{state_with_emoji} • {status}")
        
        # Update confidence display
        confidence = f"{self.monitor.last_confidence:.2f}" if self.monitor.last_confidence is not None else "-"
        self.confidence_label.setStringValue_(f"Confidence: {confidence}")
        
        # Update button states - 2x2 grid with larger emoji buttons
        self.toggle_btn.setTitle_("▶️" if self.monitor.paused else "⏸️")
        self.mute_btn.setTitle_("🔇" if self.monitor.muted else "🔊")
        self.stats_btn.setTitle_("📊")
        self.debug_btn.setTitle_("🐛")
        
        # Update stats window if open
        if self.show_stats and hasattr(self, 'stats_detections_label'):
            self.stats_detections_label.setStringValue_(f"{self.monitor.telemetry.idle_detections}")
            self.stats_failures_label.setStringValue_(f"{self.monitor.telemetry.detection_failures}")
            last_detection_time = self._formatTime_(self.monitor.telemetry.last_idle_detection)
            self.stats_last_detection_label.setStringValue_(f"{last_detection_time}")
        
        self._updateDebugView_(None)

    def toggleMonitor_(self, sender):
        self.monitor.toggle_running()
        # Button title is updated in updateDisplay_ method

    def toggleMute_(self, sender):
        self.monitor.toggle_muted()
        # Button title is updated in updateDisplay_ method
        
    def toggleStatsWindow_(self, sender):
        """Toggle the statistics popup window."""
        self.show_stats = not self.show_stats
        if self.show_stats:
            if not self.stats_window:
                self._createStatsWindow()
            self.stats_window.makeKeyAndOrderFront_(None)
        else:
            if self.stats_window:
                self.stats_window.orderOut_(None)

    def toggleDebugView_(self, sender):
        self.show_debug = not self.show_debug
        if self.show_debug:
            if not self.debug_window:
                self._createDebugWindow()
            self.debug_window.makeKeyAndOrderFront_(None)
        else:
            if self.debug_window:
                self.debug_window.orderOut_(None)
            
    def _createStatsWindow(self):
        """Create the statistics popup window."""
        self.stats_window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 300, 200),
            AppKit.NSWindowStyleMaskTitled | 
            AppKit.NSWindowStyleMaskClosable | 
            AppKit.NSWindowStyleMaskResizable,
            AppKit.NSBackingStoreBuffered,
            False
        )
        
        self.stats_window.setTitle_("Cursor Agent Monitor Statistics")
        self.stats_window.setLevel_(AppKit.NSFloatingWindowLevel)
        
        # Position relative to main window
        main_frame = self.window.frame()
        x = main_frame.origin.x + main_frame.size.width + 10
        y = main_frame.origin.y
        self.stats_window.setFrameOrigin_(NSMakePoint(x, y))
        
        bg_color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.2, 0.2, 0.95)
        self.stats_window.setBackgroundColor_(bg_color)
        
        # Create content view
        content_view = AppKit.NSView.alloc().init()
        self.stats_window.setContentView_(content_view)
        
        # Create labels
        def create_stats_label(text, size=12, is_bold=False):
            label = self.createStyledLabelWithFrame_text_(NSMakeRect(0,0,0,0), text)
            font = AppKit.NSFont.boldSystemFontOfSize_(size) if is_bold else AppKit.NSFont.systemFontOfSize_(size)
            label.setFont_(font)
            label.setTranslatesAutoresizingMaskIntoConstraints_(False)
            content_view.addSubview_(label)
            return label
        
        title_label = create_stats_label("Statistics", 16, is_bold=True)
        
        detections_key = create_stats_label("Idle Detections:")
        self.stats_detections_label = create_stats_label("0")
        self.stats_detections_label.setAlignment_(AppKit.NSTextAlignmentRight)
        
        failures_key = create_stats_label("Detection Failures:")
        self.stats_failures_label = create_stats_label("0")
        self.stats_failures_label.setAlignment_(AppKit.NSTextAlignmentRight)
        
        last_detection_key = create_stats_label("Last Idle Detection:")
        self.stats_last_detection_label = create_stats_label("Never")
        self.stats_last_detection_label.setAlignment_(AppKit.NSTextAlignmentRight)
        
        # Layout with constraints
        padding = 20
        line_spacing = 15
        NSLayoutConstraint.activateConstraints_([
            title_label.topAnchor().constraintEqualToAnchor_constant_(content_view.topAnchor(), padding),
            title_label.centerXAnchor().constraintEqualToAnchor_(content_view.centerXAnchor()),
            
            detections_key.topAnchor().constraintEqualToAnchor_constant_(title_label.bottomAnchor(), padding),
            detections_key.leadingAnchor().constraintEqualToAnchor_constant_(content_view.leadingAnchor(), padding),
            self.stats_detections_label.topAnchor().constraintEqualToAnchor_(detections_key.topAnchor()),
            self.stats_detections_label.trailingAnchor().constraintEqualToAnchor_constant_(content_view.trailingAnchor(), -padding),
            
            failures_key.topAnchor().constraintEqualToAnchor_constant_(detections_key.bottomAnchor(), line_spacing),
            failures_key.leadingAnchor().constraintEqualToAnchor_constant_(content_view.leadingAnchor(), padding),
            self.stats_failures_label.topAnchor().constraintEqualToAnchor_(failures_key.topAnchor()),
            self.stats_failures_label.trailingAnchor().constraintEqualToAnchor_constant_(content_view.trailingAnchor(), -padding),
            
            last_detection_key.topAnchor().constraintEqualToAnchor_constant_(failures_key.bottomAnchor(), line_spacing),
            last_detection_key.leadingAnchor().constraintEqualToAnchor_constant_(content_view.leadingAnchor(), padding),
            self.stats_last_detection_label.topAnchor().constraintEqualToAnchor_(last_detection_key.topAnchor()),
            self.stats_last_detection_label.trailingAnchor().constraintEqualToAnchor_constant_(content_view.trailingAnchor(), -padding),
            self.stats_last_detection_label.bottomAnchor().constraintLessThanOrEqualToAnchor_constant_(content_view.bottomAnchor(), -padding),
        ])

    def _createDebugWindow(self):
        self.debug_window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 400, 300),
            AppKit.NSWindowStyleMaskTitled | 
            AppKit.NSWindowStyleMaskClosable |
            AppKit.NSWindowStyleMaskResizable,
            AppKit.NSBackingStoreBuffered,
            False
        )
        self.debug_window.setTitle_("Debug View")
        self.debug_window.setBackgroundColor_(AppKit.NSColor.blackColor())
        self.debug_image_view = AppKit.NSImageView.alloc().initWithFrame_(
            NSMakeRect(0, 0, 400, 300)
        )
        self.debug_image_view.setImageScaling_(AppKit.NSImageScaleProportionallyUpOrDown)
        self.debug_window.setContentView_(self.debug_image_view)
        main_frame = self.window.frame()
        debug_frame = self.debug_window.frame()
        new_x = main_frame.origin.x - debug_frame.size.width - 20
        new_y = main_frame.origin.y
        self.debug_window.setFrameOrigin_(NSMakePoint(new_x, new_y))
        
    def _updateDebugView_(self, sender):
        if not self.show_debug or not self.debug_window:
            return
        if hasattr(self.monitor, 'last_screenshot') and self.monitor.last_screenshot is not None:
            try:
                img_array = np.array(self.monitor.last_screenshot)
                height, width, _ = img_array.shape
                
                # Check for detection rectangle - try multiple possible attribute names
                rect = None
                if hasattr(self.monitor, 'last_detection_rect') and self.monitor.last_detection_rect is not None:
                    rect = self.monitor.last_detection_rect
                elif hasattr(self.monitor, '_last_match_rect') and self.monitor._last_match_rect is not None:
                    rect = self.monitor._last_match_rect
                elif len(self.monitor.detectors) > 0:
                    # Try to get from the first detector
                    detector = self.monitor.detectors[0]
                    if hasattr(detector, '_last_match_rect') and detector._last_match_rect is not None:
                        rect = detector._last_match_rect
                        # Update monitor's rect for consistency
                        self.monitor.last_detection_rect = rect
                    elif hasattr(detector, 'last_match_rect') and detector.last_match_rect is not None:
                        rect = detector.last_match_rect
                        self.monitor.last_detection_rect = rect
                
                # Draw rectangle if we found one
                if rect is not None:
                    # Ensure rect has 4 values (x, y, width, height)
                    if len(rect) >= 4:
                        # Use debug renderer with state-based coloring
                        current_state = self.monitor.current_state or "unknown"
                        img_array = self.debug_renderer.render_detection_overlay(
                            image_array=img_array,
                            detection_rect=rect,
                            state=current_state,
                            confidence=self.monitor.last_confidence
                        )
                
                # Convert to RGB and save as temporary PNG file
                img_array_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                
                # Use PIL to create the image data more safely
                from PIL import Image
                pil_img = Image.fromarray(img_array_rgb)
                
                # Convert to NSImage via temporary file path
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    pil_img.save(tmp.name, 'PNG')
                    ns_image = AppKit.NSImage.alloc().initWithContentsOfFile_(tmp.name)
                    os.unlink(tmp.name)  # Clean up temp file
                
                if ns_image:
                    self.debug_image_view.setImage_(ns_image)
            except Exception as e:
                print(f"[ERROR] Debug view update failed: {e}")
                import traceback
                traceback.print_exc()
            
    def _formatTime_(self, timestamp):
        if timestamp is None:
            return "Never"
        return datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        
    def _createMenu(self):
        menubar = AppKit.NSMenu.alloc().init()
        app_menu_item = AppKit.NSMenuItem.alloc().init()
        menubar.addItem_(app_menu_item)
        app_menu = AppKit.NSMenu.alloc().init()
        quit_title = "Quit Cursor Agent Monitor"
        quit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(quit_title, "terminate:", "q")
        app_menu.addItem_(quit_item)
        app_menu_item.setSubmenu_(app_menu)
        AppKit.NSApp().setMainMenu_(menubar)

    def _updateBackgroundColor(self):
        color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 0.2, 0.2, self.alpha)
        self.window.setBackgroundColor_(color)

    def changeAlpha_(self, sender):
        self.alpha = sender.floatValue()
        self._updateBackgroundColor()

    def toggleAlphaSlider_(self, sender):
        self.alpha_slider.setHidden_(not self.alpha_slider.isHidden())

    def createStyledButtonWithFrame_title_(self, frame, title):
        button = AppKit.NSButton.alloc().initWithFrame_(frame)
        button.setTitle_(title)
        button.setBezelStyle_(AppKit.NSBezelStyleRounded)
        button.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        return button

    def createStyledLabelWithFrame_text_(self, frame, text):
        label = AppKit.NSTextField.alloc().initWithFrame_(frame)
        label.setStringValue_(text)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        label.setTextColor_(AppKit.NSColor.controlTextColor())
        return label

    def createStyledBoxWithFrame_title_(self, frame, title):
        box = AppKit.NSBox.alloc().initWithFrame_(frame)
        box.setTitle_(title)
        box.setTitlePosition_(AppKit.NSAtTop)
        box.setBorderType_(AppKit.NSLineBorder)
        box.setBoxType_(AppKit.NSBoxPrimary)
        return box

# === Service Runner ===
class AgentWatcherService:
    def __init__(self, monitor: AgentMonitor):
        self.monitor = monitor
        self.thread = threading.Thread(target=self.run_loop, daemon=True)

    def run_loop(self):
        while True:
            try:
                self.monitor.scan_and_act()
                time.sleep(CHECK_INTERVAL_SEC)
            except Exception as e:
                print(f"[ERROR] Monitor loop error: {e}")
                time.sleep(CHECK_INTERVAL_SEC)

    def start(self):
        print("[INFO] Starting AgentWatcherService...")
        self.thread.start()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n👋 Received interrupt signal. Shutting down Agent Monitor...")
    AppKit.NSApp().terminate_(None)

def main():
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Cursor Agent Monitor...")
    print("   Press Ctrl+C to exit anytime")
    print("   Or use Cmd+Q to quit from the app menu")
    print("")
    
    try:
        # Initialize NSApplication
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
        
        # Initialize telemetry with dependency injection
        container = initialize_telemetry_system()
        telemetry_service = container.telemetry_service()
        debug_renderer = container.debug_renderer()
        
        # Initialize components
        telemetry = LegacyTelemetryAdapter(telemetry_service)
        executor = CommandExecutor() if COMMAND_QUEUE_ENABLED else None

        # Load templates from organized directories
        state_templates = load_templates_from_directories(TEMPLATE_DIRECTORIES, STATE_TEMPLATE_MAPPING)
        
        if not state_templates.get(AgentState.IDLE) or not state_templates.get(AgentState.ACTIVE):
            print("[ERROR] No templates found for required states! Please add template images to agent_idle/ and agent_active/ directories.")
            return
        
        # Create detectors
        if USE_LEGACY_DETECTOR:
            # Fallback to legacy single-template detector (use first template from each category)
            detectors = [TemplateMatchDetector(
                state_templates[AgentState.IDLE][0], 
                state_templates[AgentState.ACTIVE][0]
            )]
        else:
            # Use enhanced multi-template detector with all loaded templates
            detectors = [EnhancedTemplateMatchDetector(
                state_templates,
                confidence_threshold=CONFIDENCE_THRESHOLD,
                min_confidence_gap=MIN_CONFIDENCE_GAP
            )]
        
        if OCR_ENABLED:
            detectors.append(OCRDetector())

        # Create and start the monitor
        monitor = AgentMonitor(detectors, telemetry, executor)
        service = AgentWatcherService(monitor)
        service.start()

        # Start the control panel
        panel = ControlPanel.alloc().initWithMonitor_debugRenderer_(monitor, debug_renderer)
        
        # Run the application
        AppKit.NSApp().run()
        
    except KeyboardInterrupt:
        print("\n👋 Keyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
    finally:
        print("✅ Agent Monitor stopped.")

if __name__ == "__main__":
    main()