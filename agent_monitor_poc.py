#!/usr/bin/env python3
"""
Agent Monitor POC (macOS, Cursor IDE)

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

# === Enhanced Detection Config ===
IDLE_TEMPLATES = [
    "assets/ui-cursor/idle_button.png",
    "assets/ui-cursor/run_button.png"  # Another idle state variant
]
ACTIVE_TEMPLATES = [
    "assets/ui-cursor/generating_button.png"
]

# Detection parameters
CONFIDENCE_THRESHOLD = 0.8          # Minimum confidence for valid detection
MIN_CONFIDENCE_GAP = 0.1           # Minimum gap between idle/active confidence to avoid ambiguity
REQUIRED_CONFIRMATIONS = 2         # Number of consistent detections before state change
MIN_STATE_CHANGE_INTERVAL = 3      # Minimum seconds between state changes

# Legacy support - you can switch back to simple detector by setting this to True
USE_LEGACY_DETECTOR = False

CHECK_INTERVAL_SEC = 2
TELEMETRY_FILE = "telemetry.json"
AUTO_CLICK_ENABLED = False
OCR_ENABLED = True
COMMAND_QUEUE_ENABLED = True
DIAGNOSTIC_MODE = True

# Sound configuration
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio", "alerts")
ALERT_SOUNDS = {
    "idle": "alert_waiting.wav",
    "error": "alert_error.wav",
    "success": "alert_success.wav",
    "thinking": "alert_thinking.wav",
    "completed": "alert_completed.wav"
}

# === Agent States ===
class AgentState:
    IDLE = "idle"
    ACTIVE = "active"
    UNKNOWN = "unknown"

# === Enhanced Telemetry with DI ===
from container import initialize_telemetry_system
from telemetry import EventType, TelemetryService

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

# === Detection Engine Interface ===
class StateDetector(Protocol):
    def detect_state(self) -> str:
        ...

# === Enhanced Multi-Template Detection Engine ===
class EnhancedTemplateMatchDetector:
    def __init__(self, idle_templates: list, active_templates: list, confidence_threshold=0.8, min_confidence_gap=0.1):
        self.idle_templates = idle_templates
        self.active_templates = active_templates
        self.confidence_threshold = confidence_threshold
        self.min_confidence_gap = min_confidence_gap
        self.last_confidence = None
        self.last_idle_confidence = None
        self.last_active_confidence = None
        self._last_match_rect = None
        self._detection_history = []  # For state stability
        self._last_state_change = 0
        self._min_state_change_interval = MIN_STATE_CHANGE_INTERVAL
        self._required_confirmations = REQUIRED_CONFIRMATIONS
        
        # Load all template images
        self.idle_imgs = []
        self.active_imgs = []
        
        # Load idle templates
        for template_path in idle_templates:
            if not os.path.exists(template_path):
                print(f"[WARNING] Idle template not found: {template_path}")
                continue
            img = cv2.imread(template_path)
            if img is not None:
                self.idle_imgs.append((template_path, img))
                print(f"[INFO] Loaded idle template: {template_path} ({img.shape})")
            else:
                print(f"[ERROR] Failed to load idle template: {template_path}")
        
        # Load active templates
        for template_path in active_templates:
            if not os.path.exists(template_path):
                print(f"[WARNING] Active template not found: {template_path}")
                continue
            img = cv2.imread(template_path)
            if img is not None:
                self.active_imgs.append((template_path, img))
                print(f"[INFO] Loaded active template: {template_path} ({img.shape})")
            else:
                print(f"[ERROR] Failed to load active template: {template_path}")
        
        if not self.idle_imgs or not self.active_imgs:
            raise RuntimeError("Failed to load template images for both states")

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
        
        if DIAGNOSTIC_MODE and best_confidence > 0.5:  # Only show significant matches
            print(f"[DIAGNOSTIC] Best {state_name} match: {best_confidence:.2f} ({best_template_name})")
        
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

            if DIAGNOSTIC_MODE:
                print(f"[DIAGNOSTIC] Screenshot size: {screenshot.size}")
            
            # Match all templates for both states
            idle_confidence, idle_rect, idle_template = self._match_templates(screenshot, self.idle_imgs, "idle")
            active_confidence, active_rect, active_template = self._match_templates(screenshot, self.active_imgs, "active")
            
            # Store confidences for debugging
            self.last_idle_confidence = idle_confidence
            self.last_active_confidence = active_confidence
            
            # Determine the detected state based on confidence and thresholds
            detected_state = AgentState.UNKNOWN
            
            # Both need to meet minimum threshold
            idle_valid = idle_confidence >= self.confidence_threshold
            active_valid = active_confidence >= self.confidence_threshold
            
            if active_valid and idle_valid:
                # Both detected - use confidence gap to decide
                confidence_gap = abs(active_confidence - idle_confidence)
                if confidence_gap >= self.min_confidence_gap:
                    if active_confidence > idle_confidence:
                        detected_state = AgentState.ACTIVE
                        self.last_confidence = active_confidence
                        self._last_match_rect = active_rect
                    else:
                        detected_state = AgentState.IDLE
                        self.last_confidence = idle_confidence
                        self._last_match_rect = idle_rect
                else:
                    # Confidence too close - remain unknown to avoid flickering
                    detected_state = AgentState.UNKNOWN
                    if DIAGNOSTIC_MODE:
                        print(f"[DIAGNOSTIC] Confidence gap too small ({confidence_gap:.2f}) - staying unknown")
                        
            elif active_valid:
                detected_state = AgentState.ACTIVE
                self.last_confidence = active_confidence
                self._last_match_rect = active_rect
            elif idle_valid:
                detected_state = AgentState.IDLE
                self.last_confidence = idle_confidence
                self._last_match_rect = idle_rect
            
            # Apply state stability check
            stable_state = self._get_stable_state(detected_state)
            
            if DIAGNOSTIC_MODE:
                print(f"[DIAGNOSTIC] Detected: {detected_state}, Stable: {stable_state}")
                if detected_state != AgentState.UNKNOWN:
                    print(f"[DIAGNOSTIC] Active conf: {active_confidence:.2f}, Idle conf: {idle_confidence:.2f}")
            
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
            if "Start a new chat" in text or "Accept" in text:
                return AgentState.IDLE
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

# === Agent Monitor ===
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

    def scan_and_act(self):
        if not self.running or self.paused:
            return

        # Take screenshot once for all detectors
        self.last_screenshot = pyautogui.screenshot()
        self.last_detection_rect = None
        
        detection_successful = False

        for detector in self.detectors:
            state = detector.detect_state()
            
            # Update confidence if available
            if hasattr(detector, 'last_confidence'):
                self.last_confidence = detector.last_confidence
            
            # Store detection rectangle if available
            if hasattr(detector, '_last_match_rect'):
                self.last_detection_rect = detector._last_match_rect
            
            if state == AgentState.IDLE:
                if self.state != AgentState.IDLE:
                    self.state = AgentState.IDLE
                    self.current_state = AgentState.IDLE
                    
                    # Record detection with enhanced telemetry
                    self.telemetry.record_detection(
                        confidence=self.last_confidence,
                        detection_method=detector.__class__.__name__,
                        match_rect=self.last_detection_rect
                    )
                    
                    Notifier.notify("Agent idle – input may be needed", title="Agent Watcher")
                    if not self.muted:
                        self.sound_player.play_sound("idle")
                    if AUTO_CLICK_ENABLED:
                        pyautogui.press("enter")
                    if self.executor:
                        cmd = self.executor.process_next()
                        if cmd:
                            self.telemetry.log_event(f"Executed command: {cmd}")
                detection_successful = True
                return
            elif state == AgentState.ACTIVE:
                if self.state != AgentState.ACTIVE:
                    self.state = AgentState.ACTIVE
                    self.current_state = AgentState.ACTIVE
                    
                    # Record active detection with enhanced telemetry
                    self.telemetry.record_active_detection(
                        confidence=self.last_confidence,
                        detection_method=detector.__class__.__name__,
                        match_rect=self.last_detection_rect
                    )
                else:
                    self.current_state = AgentState.ACTIVE
                detection_successful = True
            elif state == AgentState.UNKNOWN:
                self.current_state = AgentState.UNKNOWN
                # Unknown state could indicate detection issues, but not necessarily a failure

        # Only record failure if we couldn't detect any state at all
        if not detection_successful and self.current_state == AgentState.UNKNOWN:
            self.telemetry.record_failure("Unable to detect any agent state")

    def toggle_running(self):
        self.paused = not self.paused
        if not self.muted:
            if not self.paused:
                self.sound_player.play_sound("success")
            else:
                self.sound_player.play_sound("error")

    def toggle_muted(self):
        self.muted = not self.muted
        
    def pause(self):
        self.paused = True
        
    def resume(self):
        self.paused = False

# === GUI Control Panel ===
class ControlPanel(NSObject):
    def initWithMonitor_(self, monitor):
        self = objc.super(ControlPanel, self).init()
        if self is None:
            return None
            
        self.monitor = monitor
        self.debug_window = None
        self.show_debug = False
        self.alpha = 0.95
        
        # Create the window - much more compact
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 240, 180),  # Compact size for overlay use
            AppKit.NSWindowStyleMaskTitled | 
            AppKit.NSWindowStyleMaskClosable | 
            AppKit.NSWindowStyleMaskResizable |
            AppKit.NSWindowStyleMaskFullSizeContentView,
            AppKit.NSBackingStoreBuffered,
            False
        )
        
        # Configure window properties
        self.window.setTitle_("Agent Monitor Compact")
        self.window.setTitlebarAppearsTransparent_(True)
        self.window.setLevel_(AppKit.NSFloatingWindowLevel)
        self.window.setMovableByWindowBackground_(True)
        
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
        """Create and layout UI components using Auto Layout - Compact Design."""
        self.stats_window = None
        self.show_stats = False
        
        # --- Helpers to create styled UI elements without frames ---
        def create_label(panel_self, text, size=12, is_bold=False, align='left'):
            label = panel_self.createStyledLabelWithFrame_text_(NSMakeRect(0,0,0,0), text) # Frame is dummy
            font = AppKit.NSFont.boldSystemFontOfSize_(size) if is_bold else AppKit.NSFont.systemFontOfSize_(size)
            label.setFont_(font)
            if align == 'right': label.setAlignment_(AppKit.NSTextAlignmentRight)
            elif align == 'center': label.setAlignment_(AppKit.NSTextAlignmentCenter)
            else: label.setAlignment_(AppKit.NSTextAlignmentLeft)
            label.setTranslatesAutoresizingMaskIntoConstraints_(False)
            panel_self.content_view.addSubview_(label)
            return label

        def create_compact_button(panel_self, title, size=11):
            button = panel_self.createStyledButtonWithFrame_title_(NSMakeRect(0,0,0,0), title) # Frame is dummy
            button.setFont_(AppKit.NSFont.systemFontOfSize_(size))
            button.setTranslatesAutoresizingMaskIntoConstraints_(False)
            panel_self.content_view.addSubview_(button)
            return button

        # --- Create Compact UI Elements ---
        # Header with title and settings
        title = create_label(self, "Agent Monitor", 14, is_bold=True, align='center')
        
        settings_btn = create_compact_button(self, "⚙️")
        settings_btn.setTarget_(self)
        settings_btn.setAction_(objc.selector(self.toggleAlphaSlider_, signature=b"v@:"))
        
        self.alpha_slider = AppKit.NSSlider.alloc().init()
        self.alpha_slider.setMinValue_(0.2)
        self.alpha_slider.setMaxValue_(1.0)
        self.alpha_slider.setFloatValue_(self.alpha)
        self.alpha_slider.setTarget_(self)
        self.alpha_slider.setAction_(objc.selector(self.changeAlpha_, signature=b"v@:"))
        self.alpha_slider.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.alpha_slider.setHidden_(True)
        self.content_view.addSubview_(self.alpha_slider)

        # Status display (improved formatting)
        self.status_state_label = create_label(self, "Unknown", 15, is_bold=True, align='center')
        self.confidence_label = create_label(self, "Confidence: -", 11, align='center')

        # Compact button row
        self.toggle_btn = create_compact_button(self, "⏸️")  # Pause/Resume
        self.toggle_btn.setTarget_(self)
        self.toggle_btn.setAction_(objc.selector(self.toggleMonitor_, signature=b"v@:"))
        
        self.mute_btn = create_compact_button(self, "🔊")  # Mute/Unmute
        self.mute_btn.setTarget_(self)
        self.mute_btn.setAction_(objc.selector(self.toggleMute_, signature=b"v@:"))
        
        self.stats_btn = create_compact_button(self, "📊")  # Stats popup
        self.stats_btn.setTarget_(self)
        self.stats_btn.setAction_(objc.selector(self.toggleStatsWindow_, signature=b"v@:"))
        
        self.debug_btn = create_compact_button(self, "🐛")  # Debug view
        self.debug_btn.setTarget_(self)
        self.debug_btn.setAction_(objc.selector(self.toggleDebugView_, signature=b"v@:"))

        # --- Activate Constraints - Compact Layout ---
        padding = 10
        small_padding = 5
        NSLayoutConstraint.activateConstraints_([
            # Header row
            title.topAnchor().constraintEqualToAnchor_constant_(self.content_view.topAnchor(), padding),
            title.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            title.trailingAnchor().constraintEqualToAnchor_constant_(settings_btn.leadingAnchor(), -small_padding),

            settings_btn.topAnchor().constraintEqualToAnchor_constant_(self.content_view.topAnchor(), padding),
            settings_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            settings_btn.widthAnchor().constraintEqualToConstant_(24),
            settings_btn.heightAnchor().constraintEqualToConstant_(24),

            # Alpha slider (hidden by default)
            self.alpha_slider.topAnchor().constraintEqualToAnchor_constant_(title.bottomAnchor(), small_padding),
            self.alpha_slider.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.alpha_slider.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),

            # Status display (improved spacing)
            self.status_state_label.topAnchor().constraintEqualToAnchor_constant_(self.alpha_slider.bottomAnchor(), padding + 5),
            self.status_state_label.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.status_state_label.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),

            self.confidence_label.topAnchor().constraintEqualToAnchor_constant_(self.status_state_label.bottomAnchor(), 4),
            self.confidence_label.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.confidence_label.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),

            # Button row (improved spacing and sizing)
            self.toggle_btn.topAnchor().constraintEqualToAnchor_constant_(self.confidence_label.bottomAnchor(), padding + 2),
            self.toggle_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.toggle_btn.widthAnchor().constraintEqualToConstant_(50),
            self.toggle_btn.heightAnchor().constraintEqualToConstant_(32),

            self.mute_btn.topAnchor().constraintEqualToAnchor_(self.toggle_btn.topAnchor()),
            self.mute_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.toggle_btn.trailingAnchor(), small_padding + 2),
            self.mute_btn.widthAnchor().constraintEqualToConstant_(50),
            self.mute_btn.heightAnchor().constraintEqualToConstant_(32),

            self.stats_btn.topAnchor().constraintEqualToAnchor_(self.toggle_btn.topAnchor()),
            self.stats_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.mute_btn.trailingAnchor(), small_padding + 2),
            self.stats_btn.widthAnchor().constraintEqualToConstant_(50),
            self.stats_btn.heightAnchor().constraintEqualToConstant_(32),

            self.debug_btn.topAnchor().constraintEqualToAnchor_(self.toggle_btn.topAnchor()),
            self.debug_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.stats_btn.trailingAnchor(), small_padding + 2),
            self.debug_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            self.debug_btn.heightAnchor().constraintEqualToConstant_(32),

            # Bottom constraint
            self.toggle_btn.bottomAnchor().constraintLessThanOrEqualToAnchor_constant_(self.content_view.bottomAnchor(), -padding),
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
        else:
            state_with_emoji = "❓ Unknown"
            
        self.status_state_label.setStringValue_(f"{state_with_emoji} • {status}")
        
        # Update confidence display
        confidence = f"{self.monitor.last_confidence:.2f}" if self.monitor.last_confidence is not None else "-"
        self.confidence_label.setStringValue_(f"Confidence: {confidence}")
        
        # Update button states
        self.toggle_btn.setTitle_("▶️" if self.monitor.paused else "⏸️")
        self.mute_btn.setTitle_("🔇" if self.monitor.muted else "🔊")
        
        # Update stats window if open
        if self.show_stats and hasattr(self, 'stats_detections_label'):
            self.stats_detections_label.setStringValue_(f"{self.monitor.telemetry.idle_detections}")
            self.stats_failures_label.setStringValue_(f"{self.monitor.telemetry.detection_failures}")
            last_detection_time = self._formatTime_(self.monitor.telemetry.last_idle_detection)
            self.stats_last_detection_label.setStringValue_(f"{last_detection_time}")
        
        self._updateDebugView_(None)

    def toggleMonitor_(self, sender):
        self.monitor.toggle_running()
        self.toggle_btn.setTitle_("Pause Monitor" if not self.monitor.paused else "Resume Monitor")

    def toggleMute_(self, sender):
        self.monitor.toggle_muted()
        self.mute_btn.setTitle_("Mute Sounds" if not self.monitor.muted else "Unmute Sounds")
        
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
        
        self.stats_window.setTitle_("Agent Monitor Statistics")
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
                
                if hasattr(self.monitor, 'last_detection_rect'):
                    rect = self.monitor.last_detection_rect
                    if rect is not None:
                        cv2.rectangle(img_array, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 2)
                
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
            
    def _formatTime_(self, timestamp):
        if timestamp is None:
            return "Never"
        return datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        
    def _createMenu(self):
        menubar = AppKit.NSMenu.alloc().init()
        app_menu_item = AppKit.NSMenuItem.alloc().init()
        menubar.addItem_(app_menu_item)
        app_menu = AppKit.NSMenu.alloc().init()
        quit_title = "Quit Agent Monitor"
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

def main():
    # Initialize NSApplication
    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
    
    # Initialize telemetry with dependency injection
    container = initialize_telemetry_system()
    telemetry_service = container.telemetry_service()
    
    # Initialize components
    telemetry = LegacyTelemetryAdapter(telemetry_service)
    executor = CommandExecutor() if COMMAND_QUEUE_ENABLED else None

    # Create detectors
    if USE_LEGACY_DETECTOR:
        # Fallback to legacy single-template detector
        detectors = [TemplateMatchDetector(IDLE_TEMPLATES[0], ACTIVE_TEMPLATES[0])]
    else:
        # Use enhanced multi-template detector with custom parameters
        detectors = [EnhancedTemplateMatchDetector(
            IDLE_TEMPLATES, 
            ACTIVE_TEMPLATES,
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
    panel = ControlPanel.alloc().initWithMonitor_(monitor)
    
    # Run the application
    AppKit.NSApp().run()

if __name__ == "__main__":
    main()