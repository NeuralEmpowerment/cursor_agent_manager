# Acceptance Tests

**Last Updated**: 2025-06-18  
**Version**: 1.1  

This document contains acceptance tests for the Cursor Agent Monitor project. Each test includes a user story and basic requirements that the application should meet.

## Table of Contents

- [Acceptance Tests](#acceptance-tests)
  - [Table of Contents](#table-of-contents)
  - [Test 1: Application Startup](#test-1-application-startup)
  - [Test 2: Application Shutdown](#test-2-application-shutdown)
  - [Test 3: Idle State Detection](#test-3-idle-state-detection)
  - [Test 4: Active State Detection](#test-4-active-state-detection)
  - [Test 5: Sound Alert Management](#test-5-sound-alert-management)
  - [Test 6: Visual Status Indicators](#test-6-visual-status-indicators)
  - [Test 7: Control Panel Operations](#test-7-control-panel-operations)
  - [Test 8: Data Recording](#test-8-data-recording)
  - [Test 9: Analytics CLI](#test-9-analytics-cli)
  - [Test 10: Template Image Configuration](#test-10-template-image-configuration)
  - [Test 11: Performance Under Load](#test-11-performance-under-load)
  - [Test 12: Error Recovery](#test-12-error-recovery)
  - [Test 13: OCR Fallback](#test-13-ocr-fallback)
  - [Test 14: Unknown State Handling](#test-14-unknown-state-handling)
  - [Test 15: Database Growth Management](#test-15-database-growth-management)
  - [Test 16: UI Layout and Responsiveness](#test-16-ui-layout-and-responsiveness)
  - [Test 17: Repeating Idle Alerts](#test-17-repeating-idle-alerts)


## Test 1: Application Startup

**User Story**: As a user, I want to start the Cursor agent monitor so I can begin tracking AI agent states.

**Requirements**:
- The app should start when I run `./run.sh`
- The app should display a control panel within 5 seconds
- The app should show an initial status (idle, active, or unknown)
- The app should create a database file if it doesn't exist
- The app should not show any error messages during startup

## Test 2: Application Shutdown

**User Story**: As a user, I want to cleanly shut down the monitor to ensure data is saved.

**Requirements**:
- The app should close when I close the control panel window
- The app should save all data before closing
- The app should exit within 3 seconds
- The app should not leave any background processes running
- The app should not corrupt the database

## Test 3: Idle State Detection

**User Story**: As a user, I want to know when the AI agent is idle so I can see when it's ready for new tasks.

**Requirements**:
- The app should detect when Cursor's AI agent is idle
- The app should show "💤 idle" status in the control panel
- The app should detect the idle state within 2 seconds
- The app should play a simple two-note idle alert sound (if enabled)
- The app should record the detection in the database
- The app should track idle duration for repeat alert functionality

## Test 4: Active State Detection

**User Story**: As a user, I want to know when the AI agent is actively processing so I don't interrupt it.

**Requirements**:
- The app should detect when Cursor's AI agent is generating/active
- The app should show "🚀 active" status in the control panel
- The app should detect state changes within 1 second
- The app should stop any repeating idle alerts when becoming active
- The app should track how long each session lasts

## Test 5: Sound Alert Management

**User Story**: As a user, I want to receive audio notifications for state changes but also be able to mute them.

**Requirements**:
- The app should play a simple two-note sound for idle states
- The app should have distinct sounds for different alert types
- The app should have a mute/unmute button that works immediately
- The app should remember the mute setting between sessions
- The app should respect the system volume settings
- The app should not play overlapping sounds
- The app should respect mute settings for repeating alerts

## Test 6: Visual Status Indicators

**User Story**: As a user, I want clear visual indicators to see the current state at a glance.

**Requirements**:
- The app should show emoji status indicators (💤, 🚀, ❓)
- The app should update the status within 100ms of detection
- The app should use consistent and intuitive symbols
- The app should keep the control panel always visible
- The app should handle window positioning properly
- The app should show confidence scores alongside state indicators

## Test 7: Control Panel Operations

**User Story**: As a user, I want an intuitive control panel to manage the monitor.

**Requirements**:
- The app should have responsive buttons (pause, mute, debug)
- The app should provide visual feedback for button clicks
- The app should maintain button states correctly (pressed/unpressed)
- The app should allow pausing and resuming monitoring
- The app should show a debug view when requested

## Test 8: Data Recording

**User Story**: As a user, I want all monitor activity recorded for later analysis.

**Requirements**:
- The app should save all detection events to a database
- The app should record timestamps, confidence scores, and coordinates
- The app should not lose data during normal operation
- The app should handle database errors gracefully
- The app should maintain data integrity across sessions

## Test 9: Analytics CLI

**User Story**: As a user, I want to analyze monitor performance through a command-line interface.

**Requirements**:
- The app should provide a `./run_analytics.sh` command
- The app should show basic statistics when requested
- The app should generate charts and visualizations
- The app should export data to CSV format
- The app should complete analytics operations within 10 seconds

## Test 10: Template Image Configuration

**User Story**: As a user, I want to customize template images for different UI themes.

**Requirements**:
- The app should load template images from `assets/ui-cursor/`
- The app should handle missing template files gracefully
- The app should use new templates when files are replaced
- The app should validate template image formats
- The app should provide clear error messages for invalid templates

## Test 11: Performance Under Load

**User Story**: As a user, I want the monitor to perform efficiently during extended use.

**Requirements**:
- The app should maintain consistent performance for hours of use
- The app should keep memory usage below 100MB
- The app should respond to UI interactions within 200ms
- The app should not slow down over time
- The app should handle rapid state changes correctly

## Test 12: Error Recovery

**User Story**: As a user, I want the system to recover gracefully from errors.

**Requirements**:
- The app should log errors with sufficient detail
- The app should continue monitoring after recoverable errors
- The app should show error status in the control panel
- The app should not crash on common errors
- The app should provide meaningful error messages

## Test 13: OCR Fallback

**User Story**: As a user, I want the system to use OCR when template matching fails.

**Requirements**:
- The app should automatically try OCR when templates fail
- The app should complete OCR analysis within 3 seconds
- The app should achieve >70% accuracy with OCR
- The app should record which detection method was used
- The app should handle OCR failures without crashing

## Test 14: Unknown State Handling

**User Story**: As a user, I want to see when the system cannot determine the state clearly.

**Requirements**:
- The app should show "❓ Unknown" when detection fails
- The app should not trigger false alerts during unknown states
- The app should continue trying to detect states
- The app should log diagnostic information for unknown states
- The app should recover when clear states return

## Test 15: Database Growth Management

**User Story**: As a user, I want the system to manage database size automatically.

**Requirements**:
- The app should provide database cleanup commands
- The app should not degrade performance with large datasets
- The app should maintain data integrity during cleanup
- The app should warn when database grows large
- The app should allow manual data export before cleanup

## Test 16: UI Layout and Responsiveness

**User Story**: As a user, I want a properly formatted and responsive control panel that adapts to window resizing.

**Requirements**:
- The app title should be properly centered without duplication or overlap
- The control panel should be resizable by the user
- Buttons should be arranged in a 2x2 grid layout for better space utilization
- When the window is resized, all content should remain properly centered
- UI elements should not overlay or clip each other at any window size
- Text and buttons should scale appropriately with window size
- The layout should maintain proper spacing and padding at all sizes
- Window should have reasonable minimum size constraints to prevent content overflow
- All UI elements should be accessible and clickable at any supported window size
- The control panel should maintain visual consistency across different screen resolutions

## Test 17: Repeating Idle Alerts

**User Story**: As a user, I want to receive periodic reminders when the agent has been idle for extended periods so I don't miss opportunities to provide input.

**Requirements**:
- The app should play the initial idle alert immediately when idle state is detected
- The app should repeat the idle alert every 60 seconds while remaining in idle state
- The app should show notifications with idle duration (e.g., "Still idle after 2:30")
- The app should stop repeating alerts immediately when leaving idle state
- The app should reset the idle timer when transitioning from active to idle
- The app should respect the mute setting for repeating alerts
- The app should not play repeating alerts when monitoring is paused
- The app should handle rapid state transitions without triggering false repeats
- The app should maintain accurate idle duration tracking across state changes
- The app should use the simple two-note sound for all idle alerts (initial and repeating) 