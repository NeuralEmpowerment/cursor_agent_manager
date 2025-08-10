# Changelog

All notable changes to the Cursor Agent Monitor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-08-10

### ✨ Added
- **🖥️ Multi-Display Support (Quartz)**: Monitor a specific physical macOS display
  - New runtime button in the control panel: “🖥️ Choose Display” to switch displays on the fly
  - New CLI flags:
    - `--list-displays` to enumerate available displays and exit
    - `--display-index <n>` to select a display at startup (enables multiple instances targeting different monitors)
- **📸 Template Capture Integration**: `capture_template.py` now supports `--display-index` for per-display screenshots

### 🔧 Improved
- **Screenshot Abstraction**: Introduced `display_capture.py` with `ScreenshotProvider` for Quartz-based screenshots and display enumeration
- **UI Feedback**: Window title reflects the currently selected display
- **Backward Compatibility**: Defaults to main display when no selection is provided

### ⚠️ Notes
- **Mission Control Spaces**: macOS only permits capturing the currently visible Space on the selected display; off-screen Spaces cannot be captured until visible

---

## [2.0.4] - 2025-07-01

### 🔧 Improved
- **⏰ COMMAND_RUNNING Alert Timing**: Modified to only sound after 1 minute instead of immediately
  - **Issue**: Previously played alert sound immediately when entering COMMAND_RUNNING state, causing false positives for short-running commands
  - **Solution**: Removed immediate sound playback, first alert now only plays after 1 minute elapsed
  - **Benefit**: Eliminates noise from quick commands, only alerts for truly hanging/stalled processes
  - **User Experience**: Notification still shows immediately with message "Monitor will alert after 1 minute"
  - **Technical**: Enhanced repeat alert logic to properly handle first alert timing vs subsequent alerts

### 📋 Technical Details
- **Initial State Entry**: Shows notification but plays no sound
- **First Alert**: Plays after 1 minute since command started
- **Subsequent Alerts**: Continue every 60 seconds as before
- **Logic Enhancement**: Improved `_check_command_running_repeat_alert()` method with proper first-alert timing

---

## [2.0.3] - 2025-07-01

### 🛡️ CRITICAL - Fixed Segmentation Fault (Threading Safety)

This patch release resolves a critical segmentation fault that was causing the application to crash during idle state detection.

### 🔧 Fixed
- **💥 Segmentation Fault Resolution**: Completely eliminated threading-related crashes
  - **Root Cause**: `simpleaudio` library causing threading violations when called from background thread
  - **Solution**: Replaced with macOS native `NSSound` APIs for thread-safe audio playback
  - **Impact**: Application now runs indefinitely without crashes during state transitions

- **🔄 Thread-Safe Notification System**: Implemented queue-based cross-thread communication
  - Background thread queues notifications instead of direct GUI API calls
  - Main thread timer processes notification queue every 100ms
  - Eliminates all threading violations with macOS AppKit APIs
  - Uses `queue.Queue` for guaranteed thread safety

- **🎵 Audio System Overhaul**: Complete replacement of audio backend
  - Removed `simpleaudio` dependency causing segfaults
  - Implemented `ThreadSafeSoundPlayer` using `AppKit.NSSound`
  - Native macOS audio APIs are inherently thread-safe
  - Added comprehensive error handling and caching

### 🚀 Improved
- **🧵 Threading Architecture**: Robust cross-thread communication pattern
  - `NotificationQueue` class with thread-safe queuing
  - `ThreadSafeNotifier` for safe background thread notifications  
  - Main thread timer for GUI operation processing
  - Complete separation of background and GUI thread operations

- **🔍 Error Handling**: Enhanced stability and debugging
  - Comprehensive exception handling in monitor loop
  - Full stack traces for debugging threading issues
  - Graceful degradation when audio/notification systems fail
  - Application continues running even if individual components fail

### 📋 Technical Details
- **Threading Model**: Background monitoring → Queue → Main thread GUI operations
- **Audio Backend**: `simpleaudio` → `AppKit.NSSound` (native macOS)
- **Notification System**: Direct dispatch → Queue-based processing
- **Safety**: Zero cross-thread GUI API calls, all operations properly isolated

### 💥 Breaking Changes
- Removed `simpleaudio` dependency (replaced with native macOS audio)
- Audio initialization now uses `NSSound.alloc().initWithContentsOfFile_byReference_()`

### 🗑️ Removed
- `import simpleaudio as sa` - replaced with native macOS APIs
- Direct cross-thread GUI operations - replaced with queue system

---

## [2.0.2] - 2025-01-03

### 📋 Pre-Development Checkpoint
- **Project Planning**: Created comprehensive project plan for Enhanced Statistics System with Duration Tracking & Web Dashboard
- **Architecture Documentation**: Defined Domain Driven Design structure with clean architecture principles
- **Development Preparation**: Established SOLID principles implementation roadmap with dependency injection enhancements
- **Version Control**: Tagged stable checkpoint before major feature development

### 📊 Planned Features (Next Release)
- State duration tracking with second-level precision
- Interactive web dashboard with Chart.js visualizations
- Daily/weekly/monthly cumulative runtime views
- Clean hexagonal architecture with domain separation
- Enhanced dependency injection container
- Unified startup script for monitor and dashboard

---

## [2.0.1] - 2025-06-27

### ✨ Added
- **🧪 Comprehensive Test Infrastructure**: New priority logic testing framework
  - New `tests/test_priority_logic.py` with mock-based unit tests for all priority scenarios
  - Added priority logic tests to `run_tests.sh` test suite  
  - Created detailed acceptance criteria in `docs/acceptance-tests/priority-detection-tests.md`
  - Complete test coverage for edge cases, confidence gaps, thresholds, and priority scenarios

- **🎨 Debug Visualization System**: Enhanced visual debugging with dependency injection
  - New `telemetry/debug_visualization.py` with state-based color providers
  - `StateBasedColorProvider`: Active=Green, Idle=Yellow, Run Command=Blue, Unknown=Gray
  - `OpenCVDebugRenderer`: Clean rendering with SOLID design principles
  - Integrated debug renderer into control panel via dependency injection

### 🔧 Improved
- **🎯 Priority Logic Algorithm**: Completely refactored state selection logic
  - Fixed run_command always takes priority when above threshold (regardless of confidence vs other states)
  - Simplified logic: RUN_COMMAND → Highest Confidence → Unknown (if gap too small)
  - Removed complex multi-tier priority system in favor of clear binary priority
  - Enhanced diagnostic output with confidence gaps and selection reasoning

- **⚠️ Smart Template Quality Detection**: Enhanced template validation system
  - Warns when multiple states have suspiciously high confidence (≥0.95) 
  - Better diagnostic messages to help identify overly generic templates
  - Improved template matching accuracy through intelligent validation
  - Prevents false positive warnings for legitimate perfect matches

### 🔧 Fixed
- **🏗️ Architecture Improvements**: Better separation of concerns and dependency injection
  - Control panel now properly receives debug renderer via constructor injection
  - Enhanced telemetry container with debug visualization services
  - Cleaner initialization flow with proper dependency management

### 📋 Technical Details
- **Simplified Priority Logic**: Binary priority system (RUN_COMMAND vs confidence-based)
- **Enhanced Debug Visualization**: State-based coloring with proper OpenCV integration
- **Improved Testing**: Mock-based unit tests with controlled confidence injection
- **Better Diagnostics**: Enhanced logging with gap calculations and state selection reasoning
- **SOLID Design**: Debug visualization follows dependency injection and single responsibility principles

## [2.0.0] - 2025-06-27

### 🎉 MAJOR RELEASE - Production Ready Agent Monitor

This release represents a complete transformation from a basic POC to a robust, production-ready agent monitoring system with breaking changes and major new features.

### ✨ Added
- **🎯 Smart Priority Logic**: RUN_COMMAND state automatically takes priority over ACTIVE when both detected
- **⚡ Run Command Detection**: New state detection for Accept/Run buttons in Cursor IDE with urgent alerts
- **🔔 Recurring Alert System**: 
  - Run command alerts repeat every 60 seconds with escalating notifications
  - Idle alerts continue to repeat every 60 seconds
  - Shows elapsed time: *"🚨 COMMAND STILL WAITING - 2:15 elapsed"*
- **🎵 Distinct Alert Sounds**: 
  - `run_command`: Uses ascending alert tone (`alert_ascending.wav`) - urgent, attention-grabbing
  - `idle`: Uses simple two-note sound (`alert_idle_simple.wav`) - gentle, non-intrusive
  - `warning`: Alternative urgent sound for run_command alerts
- **🛠️ Enhanced Template Management**: 
  - New `./run_capture_tool.sh` script for easy template creation
  - Updated templates for better state detection accuracy
  - `active_template_20250627_101104.png` & `active_template_20250627_101308.png`
  - `idle_template_20250627_101801.png`
  - `run_command_template_20250627_103259.png` & `run_command_template_20250627_110953.png`
- **⚠️ Smart Template Validation**: Automatic detection of problematic templates with helpful warnings
- **🚪 Graceful Shutdown**: Proper Ctrl+C handling with signal management (SIGINT, SIGTERM)
- **📋 Professional Documentation**:
  - Comprehensive README with Quick Start guide (under 2 minutes setup)
  - Template management and troubleshooting sections
  - Git strategy and release management documentation (`docs/GIT_STRATEGY.md`)
  - Automated release script (`release.sh`) with semantic versioning
- **🔧 Development Tools**:
  - `fix_bad_template.sh` utility for template management
  - Enhanced diagnostic output with detector winner logging
  - Better debug modes with `[DETECTOR_WINNER]`, `[PRIORITY_LOGIC]`, `[STATE_LOGIC]` messages

### 🔧 Fixed
- **🛡️ Critical State Handling Bug**: Fixed state changes being trapped in diagnostic-only blocks
- **🔇 Sound Playback Issues**: Sounds now play regardless of diagnostic mode settings
- **⚖️ Confidence Gap Conflicts**: Resolved conflicts between priority logic and confidence gap checks
- **🔄 State Stability**: Fixed constant switching between active/unknown/run_command states
- **🧠 Detection Logic**: Moved priority logic to detector level for better stability and consistency
- **🚫 Template Issues**: Removed problematic templates causing false positives
- **📁 File Management**: Added `.DS_Store` to `.gitignore` for cleaner repository

### 🚀 Improved
- **🎯 Detection Accuracy**: Enhanced template matching with detector-level priority implementation
- **🔄 State Transitions**: Smoother transitions with proper tracking reset mechanisms
- **👤 User Experience**: More responsive and reliable notifications with distinct alert types
- **🏗️ Code Architecture**: Cleaner separation of concerns between detection and monitoring logic
- **📊 Error Handling**: Robust exception management and graceful degradation
- **📈 Telemetry**: Better logging and debugging capabilities

### 💥 Breaking Changes
- **Priority System**: Detection logic now uses RUN_COMMAND > ACTIVE > IDLE prioritization
- **Alert Behavior**: Different sounds and notification patterns for each state type
- **Template Structure**: Reorganized template files with new naming conventions
- **Configuration**: Updated sound mappings and alert timing configurations

### 📋 Technical Details
- **Detector-Level Priority**: Implementation moved to `EnhancedTemplateMatchDetector` for stability
- **Enhanced State Tracking**: Automatic reset mechanisms for `idle_start_time` and `run_command_start_time`
- **Signal Handling**: Proper cleanup with `AppKit.NSApp().terminate_()` for graceful shutdown
- **Template Validation**: Real-time warnings for templates with suspiciously high confidence scores
- **Release Management**: Professional semantic versioning with automated scripts

### 🗑️ Removed
- **Problematic Templates**: 
  - `idle_button.png` (redundant)
  - `idle_template_20250618_115844.png` (false positives)
  - `idle_template_20250618_120106.png` (false positives)
  - `run_button.png` (replaced with better templates)
- **Redundant Logic**: Conflicting detection logic that caused state instability
- **Debug Artifacts**: Cleaned up development files and improved `.gitignore`

---

## [1.0.0] - 2025-01-06

### 🎉 Major Release - Production Ready Agent Monitor

This release represents a complete transformation from a basic POC to a robust, production-ready agent monitoring system.

### ✨ Added
- **Smart Priority Logic**: RUN_COMMAND state now takes priority over ACTIVE state when both are detected
- **Run Command Detection**: New state detection for Accept/Run buttons in Cursor IDE
- **Distinct Alert Sounds**: 
  - `run_command`: Uses ascending alert tone (`alert_ascending.wav`)
  - `idle`: Uses simple two-note sound (`alert_idle_simple.wav`)
- **Recurring Alert System**: 
  - Run command alerts repeat every 60 seconds with escalating notifications
  - Idle alerts continue to repeat every 60 seconds
  - Shows elapsed time in repeat notifications
- **Enhanced Template Management**: New templates for better state detection
  - `active_template_20250627_101104.png`
  - `active_template_20250627_101308.png` 
  - `idle_template_20250627_101801.png`
  - `run_command_template_20250627_103259.png`
- **Smart Template Validation**: Automatic detection of problematic templates with warnings
- **Graceful Shutdown**: Proper Ctrl+C handling with signal management
- **Enhanced Capture Tool**: `run_capture_tool.sh` for easy template creation
- **Improved Debugging**: Better diagnostic output with detector winner logging

### 🔧 Fixed
- **Critical State Handling Bug**: Fixed state changes being trapped in diagnostic-only blocks
- **Sound Playback Issues**: Sounds now play regardless of diagnostic mode settings
- **Confidence Gap Conflicts**: Resolved conflicts between priority logic and confidence gap checks
- **State Stability**: Fixed constant switching between active/unknown/run_command states
- **Detection Logic**: Moved priority logic to detector level for better stability

### 🚀 Improved
- **Detection Accuracy**: Enhanced template matching with better confidence thresholds
- **State Transitions**: Smoother transitions between states with proper tracking reset
- **User Experience**: More responsive and reliable notifications
- **Code Architecture**: Cleaner separation of concerns between detection and monitoring logic

### 📋 Technical Details
- Detector-level priority implementation (RUN_COMMAND > ACTIVE > IDLE)
- Enhanced state tracking with automatic reset mechanisms
- Improved error handling and graceful degradation
- Better telemetry and logging for debugging

### 🗑️ Removed
- Problematic idle templates that were causing false positives
- Redundant detection logic that was causing state conflicts

---

## [0.x.x] - Previous Versions
- Initial POC development
- Basic template matching
- Simple idle detection
- Foundation UI and sound systems 