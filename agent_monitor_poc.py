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

# === Config ===
IDLE_IMAGE = "idle_button.png"
ACTIVE_IMAGE = "generating_button.png"
CHECK_INTERVAL_SEC = 2
TELEMETRY_FILE = "telemetry.json"
AUTO_CLICK_ENABLED = False
OCR_ENABLED = True
COMMAND_QUEUE_ENABLED = True
DIAGNOSTIC_MODE = True

# Sound configuration
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
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

# === Double Template Matcher ===
class TemplateMatchDetector:
    def __init__(self, idle_template: str, generating_template: str):
        self.idle_template = idle_template
        self.generating_template = generating_template
        self.last_confidence = None
        self._last_match_rect = None
        
        # Verify template files exist
        if not os.path.exists(idle_template):
            raise FileNotFoundError(f"Idle template not found: {idle_template}")
        if not os.path.exists(generating_template):
            raise FileNotFoundError(f"Generating template not found: {generating_template}")
            
        # Load template images
        try:
            self.idle_img = cv2.imread(idle_template)
            self.generating_img = cv2.imread(generating_template)
            
            if self.idle_img is None or self.generating_img is None:
                raise RuntimeError("Failed to load one or more template images")
                
            print(f"[INFO] Successfully loaded template images:")
            print(f"  - Idle template: {idle_template} ({self.idle_img.shape})")
            print(f"  - Generating template: {generating_template} ({self.generating_img.shape})")
        except Exception as e:
            raise RuntimeError(f"Failed to load template images: {e}")

    def _match_template(self, img, template, threshold=0.8):
        """Match template in image using OpenCV."""
        # Convert PIL image to OpenCV format
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Get dimensions
        h, w = template.shape[:2]
        
        # Template matching
        result = cv2.matchTemplate(img_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        self.last_confidence = max_val  # Store the confidence
        
        if DIAGNOSTIC_MODE:
            print(f"[DIAGNOSTIC] Template match confidence: {max_val:.2f}")
        
        if max_val >= threshold:
            rect = (max_loc[0], max_loc[1], w, h)
            self._last_match_rect = rect  # Store the match rectangle
            return rect
        self._last_match_rect = None
        return None

    def detect_state(self) -> str:
        try:
            # Take a screenshot
            screenshot = pyautogui.screenshot()

            if DIAGNOSTIC_MODE:
                print(f"[DIAGNOSTIC] Screenshot size: {screenshot.size}")
            
            # Look for the templates
            active = self._match_template(screenshot, self.generating_img, 0.8)
            if not active:  # Only check for idle if not active
                idle = self._match_template(screenshot, self.idle_img, 0.8)
            else:
                idle = None

            if DIAGNOSTIC_MODE:
                if active:
                    print(f"[DIAGNOSTIC] Found active button at: {active}")
                if idle:
                    print(f"[DIAGNOSTIC] Found idle button at: {idle}")
                if not active and not idle:
                    print("[DIAGNOSTIC] No buttons found in current screenshot")

            if active:
                return AgentState.ACTIVE
            elif idle:
                return AgentState.IDLE
            return AgentState.UNKNOWN
                
        except Exception as e:
            print(f"[ERROR] Template matching error: {str(e)}")
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
            if isinstance(detector, TemplateMatchDetector) and hasattr(detector, '_last_match_rect'):
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

        if self.state == AgentState.IDLE:
            self.state = AgentState.ACTIVE
            if not self.muted:
                self.sound_player.play_sound("thinking")
        
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
        
        # Create the window
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 320, 580),  # Initial size
            AppKit.NSWindowStyleMaskTitled | 
            AppKit.NSWindowStyleMaskClosable | 
            AppKit.NSWindowStyleMaskResizable |
            AppKit.NSWindowStyleMaskFullSizeContentView,
            AppKit.NSBackingStoreBuffered,
            False
        )
        
        # Configure window properties
        self.window.setTitle_("Agent Monitor Control")
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
        """Create and layout UI components using Auto Layout."""
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

        def create_button(panel_self, title):
            button = panel_self.createStyledButtonWithFrame_title_(NSMakeRect(0,0,0,0), title) # Frame is dummy
            button.setTranslatesAutoresizingMaskIntoConstraints_(False)
            panel_self.content_view.addSubview_(button)
            return button

        def create_box(panel_self, title):
            box = panel_self.createStyledBoxWithFrame_title_(NSMakeRect(0,0,0,0), title) # Frame is dummy
            box.setTranslatesAutoresizingMaskIntoConstraints_(False)
            panel_self.content_view.addSubview_(box)
            return box

        # --- Create UI Elements ---
        title = create_label(self, "Agent Monitor", 24, is_bold=True, align='center')
        
        settings_btn = create_button(self, "⚙️")
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

        status_box = create_box(self, "Status")
        self.status_label = create_label(self, "Running", 24, align='center')
        self.status_label.setTranslatesAutoresizingMaskIntoConstraints_(False)
        status_box.contentView().addSubview_(self.status_label)

        controls_box = create_box(self, "Controls")
        self.toggle_btn = create_button(self, "Pause Monitor")
        self.toggle_btn.setTarget_(self)
        self.toggle_btn.setAction_(objc.selector(self.toggleMonitor_, signature=b"v@:"))
        self.toggle_btn.setTranslatesAutoresizingMaskIntoConstraints_(False)
        controls_box.contentView().addSubview_(self.toggle_btn)
        
        self.mute_btn = create_button(self, "Mute Sounds")
        self.mute_btn.setTarget_(self)
        self.mute_btn.setAction_(objc.selector(self.toggleMute_, signature=b"v@:"))
        self.mute_btn.setTranslatesAutoresizingMaskIntoConstraints_(False)
        controls_box.contentView().addSubview_(self.mute_btn)

        stats_box = create_box(self, "Statistics")
        self.detections_label = self._add_key_value_labels(stats_box, "Idle Detections:", "0")
        self.failures_label = self._add_key_value_labels(stats_box, "Detection Failures:", "0")
        self.last_detection_label = self._add_key_value_labels(stats_box, "Last Idle:", "Never")

        diag_box = create_box(self, "Diagnostics")
        self.match_confidence_label = self._add_key_value_labels(diag_box, "Match Confidence:", "-")
        self.current_state_label = self._add_key_value_labels(diag_box, "Current State:", "Unknown")
        
        self.debug_btn = create_button(self, "Show Debug View")
        self.debug_btn.setTarget_(self)
        self.debug_btn.setAction_(objc.selector(self.toggleDebugView_, signature=b"v@:"))

        # --- Activate Constraints ---
        padding = 20
        box_padding = 10
        NSLayoutConstraint.activateConstraints_([
            title.topAnchor().constraintEqualToAnchor_constant_(self.content_view.topAnchor(), padding),
            title.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            title.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),

            settings_btn.topAnchor().constraintEqualToAnchor_constant_(self.content_view.topAnchor(), padding),
            settings_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            settings_btn.widthAnchor().constraintEqualToConstant_(30),
            settings_btn.heightAnchor().constraintEqualToConstant_(30),

            self.alpha_slider.topAnchor().constraintEqualToAnchor_constant_(settings_btn.bottomAnchor(), box_padding),
            self.alpha_slider.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.alpha_slider.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),

            status_box.topAnchor().constraintEqualToAnchor_constant_(self.alpha_slider.bottomAnchor(), padding),
            status_box.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            status_box.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            self.status_label.centerXAnchor().constraintEqualToAnchor_(status_box.contentView().centerXAnchor()),
            self.status_label.centerYAnchor().constraintEqualToAnchor_(status_box.contentView().centerYAnchor()),
            self.status_label.heightAnchor().constraintEqualToConstant_(40),

            controls_box.topAnchor().constraintEqualToAnchor_constant_(status_box.bottomAnchor(), padding),
            controls_box.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            controls_box.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            self.toggle_btn.topAnchor().constraintEqualToAnchor_constant_(controls_box.contentView().topAnchor(), box_padding),
            self.toggle_btn.leadingAnchor().constraintEqualToAnchor_constant_(controls_box.contentView().leadingAnchor(), box_padding),
            self.toggle_btn.trailingAnchor().constraintEqualToAnchor_constant_(controls_box.contentView().trailingAnchor(), -box_padding),
            self.mute_btn.topAnchor().constraintEqualToAnchor_constant_(self.toggle_btn.bottomAnchor(), box_padding),
            self.mute_btn.leadingAnchor().constraintEqualToAnchor_constant_(controls_box.contentView().leadingAnchor(), box_padding),
            self.mute_btn.trailingAnchor().constraintEqualToAnchor_constant_(controls_box.contentView().trailingAnchor(), -box_padding),
            self.mute_btn.bottomAnchor().constraintEqualToAnchor_constant_(controls_box.contentView().bottomAnchor(), -box_padding),
            self.toggle_btn.heightAnchor().constraintEqualToConstant_(30),
            self.mute_btn.heightAnchor().constraintEqualToConstant_(30),

            stats_box.topAnchor().constraintEqualToAnchor_constant_(controls_box.bottomAnchor(), padding),
            stats_box.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            stats_box.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            
            self.detections_label.topAnchor().constraintEqualToAnchor_constant_(stats_box.contentView().topAnchor(), 10),
            self.failures_label.topAnchor().constraintEqualToAnchor_constant_(self.detections_label.bottomAnchor(), 10),
            self.last_detection_label.topAnchor().constraintEqualToAnchor_constant_(self.failures_label.bottomAnchor(), 10),
            self.last_detection_label.bottomAnchor().constraintEqualToAnchor_constant_(stats_box.contentView().bottomAnchor(), -10),

            diag_box.topAnchor().constraintEqualToAnchor_constant_(stats_box.bottomAnchor(), padding),
            diag_box.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            diag_box.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),

            self.match_confidence_label.topAnchor().constraintEqualToAnchor_constant_(diag_box.contentView().topAnchor(), 10),
            self.current_state_label.topAnchor().constraintEqualToAnchor_constant_(self.match_confidence_label.bottomAnchor(), 10),
            self.current_state_label.bottomAnchor().constraintEqualToAnchor_constant_(diag_box.contentView().bottomAnchor(), -10),
            
            self.debug_btn.topAnchor().constraintEqualToAnchor_constant_(diag_box.bottomAnchor(), padding),
            self.debug_btn.leadingAnchor().constraintEqualToAnchor_constant_(self.content_view.leadingAnchor(), padding),
            self.debug_btn.trailingAnchor().constraintEqualToAnchor_constant_(self.content_view.trailingAnchor(), -padding),
            self.debug_btn.heightAnchor().constraintEqualToConstant_(30),
            self.debug_btn.bottomAnchor().constraintLessThanOrEqualToAnchor_constant_(self.content_view.bottomAnchor(), -padding),
        ])

    def _add_key_value_labels(self, view, key_text, value_text):
        key_label = self.createStyledLabelWithFrame_text_(NSMakeRect(0,0,0,0), key_text)
        key_label.setAlignment_(AppKit.NSTextAlignmentLeft)
        key_label.setTranslatesAutoresizingMaskIntoConstraints_(False)
        view.contentView().addSubview_(key_label)

        value_label = self.createStyledLabelWithFrame_text_(NSMakeRect(0,0,0,0), value_text)
        value_label.setAlignment_(AppKit.NSTextAlignmentRight)
        value_label.setTranslatesAutoresizingMaskIntoConstraints_(False)
        view.contentView().addSubview_(value_label)

        NSLayoutConstraint.activateConstraints_([
            key_label.leadingAnchor().constraintEqualToAnchor_constant_(view.contentView().leadingAnchor(), 10),
            value_label.trailingAnchor().constraintEqualToAnchor_constant_(view.contentView().trailingAnchor(), -10),
            key_label.topAnchor().constraintEqualToAnchor_(value_label.topAnchor()),
            key_label.trailingAnchor().constraintEqualToAnchor_constant_(value_label.leadingAnchor(), -10),
        ])
        
        key_label.setContentHuggingPriority_forOrientation_(251, AppKit.NSLayoutConstraintOrientationHorizontal)
        value_label.setContentCompressionResistancePriority_forOrientation_(751, AppKit.NSLayoutConstraintOrientationHorizontal)

        return value_label

    def updateDisplay_(self, timer):
        """Update the display with current status."""
        status = "Paused" if self.monitor.paused else "Running"
        self.status_label.setStringValue_(status)
        
        self.detections_label.setStringValue_(f"{self.monitor.telemetry.idle_detections}")
        self.failures_label.setStringValue_(f"{self.monitor.telemetry.detection_failures}")
        last_detection_time = self._formatTime_(self.monitor.telemetry.last_idle_detection)
        self.last_detection_label.setStringValue_(f"{last_detection_time}")
        
        confidence = f"{self.monitor.last_confidence:.2f}" if self.monitor.last_confidence is not None else "-"
        self.match_confidence_label.setStringValue_(confidence)
        
        state = self.monitor.current_state if self.monitor.current_state else "Unknown"
        self.current_state_label.setStringValue_(state)
        
        self._updateDebugView_(None)

    def toggleMonitor_(self, sender):
        self.monitor.toggle_running()
        self.toggle_btn.setTitle_("Pause Monitor" if not self.monitor.paused else "Resume Monitor")

    def toggleMute_(self, sender):
        self.monitor.toggle_muted()
        self.mute_btn.setTitle_("Mute Sounds" if not self.monitor.muted else "Unmute Sounds")
        
    def toggleDebugView_(self, sender):
        self.show_debug = not self.show_debug
        if self.show_debug:
            if not self.debug_window:
                self._createDebugWindow()
            self.debug_window.makeKeyAndOrderFront_(None)
            self.debug_btn.setTitle_("Hide Debug View")
        else:
            if self.debug_window:
                self.debug_window.orderOut_(None)
            self.debug_btn.setTitle_("Show Debug View")
            
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
    detectors = [TemplateMatchDetector(IDLE_IMAGE, ACTIVE_IMAGE)]
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