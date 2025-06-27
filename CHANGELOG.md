# Changelog

All notable changes to the Cursor Agent Monitor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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