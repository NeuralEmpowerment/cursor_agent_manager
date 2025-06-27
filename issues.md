# Issues and Enhancements

## 📋 Document Maintenance Guide

### How to Use This Document
This file tracks all bugs, enhancements, and feature requests for the Agent Monitor POC. It serves as the central hub for project planning and issue management.

### Status Types & Emoji System
Use these consistent status indicators for all issues:

- **✅ Completed**: Feature/fix has been implemented and tested
- **🚨 Critical Bug**: Urgent issues causing crashes, data loss, or major functionality breaks
- **🔴 Enhancement Request**: New features or improvements to existing functionality
- **🟡 In Progress**: Currently being worked on
- **🔵 Planning**: Defined requirements, ready for implementation
- **⚪ Future**: Good ideas for later consideration

### Section Organization
- **✅ Current**: Recently completed features and fixes
- **🚀 Next Steps**: Immediate priorities and planned work
- **🖥️ Multi-Monitor & Multi-Agent Support**: Scale-related enhancements
- **🔌 Integration & Extensibility**: API and plugin architecture
- **🔧 Architecture Issues**: Technical problems and system improvements
- **🧪 Upcoming Improvements**: Medium-term feature additions
- **🤖 AI Interaction Features**: Advanced automation capabilities
- **💡 Ideas**: Future possibilities and brainstorming

### Adding New Issues
1. **Choose the right section** based on priority and type
2. **Use consistent status emoji** from the system above
3. **Include clear problem statements** and requirements
4. **Add technical considerations** when relevant
5. **Update status** as work progresses

---

## ✅ Current
- Working state machine and detector engine
- Control panel UI with improved formatting and emojis
- Telemetry logs (text)
- Organized asset structure (images and audio files properly organized)
- Enhanced UI formatting with better spacing, larger buttons, and visual state indicators
- ✅ **Debug Window State Management**: Fixed window delegate handling and state synchronization

## 🚀 Next Steps - Agent Automation Loop
- **Multi-State Detection Architecture:**
  - **CRITICAL**: Fix run command detection as overlapping state (not exclusive)
    - Run command appears as a sub-state of active (both buttons present simultaneously)
    - Current single-state detection logic fails when multiple UI elements are present
    - Need composite state detection: "active + run_command" rather than just "run_command"
    - Requires priority/hierarchy system for overlapping states
    - Template matching needs to handle multiple simultaneous matches
- **Expanded State Detection:**
  - Detect "command approval" state (when agent asks permission to run commands)
  - Detect "waiting for user input" state
  - Detect "error/failed command" state
  - Detect "tool selection" state
  - Detect "code generation complete" state
  - Detect complex multi-button scenarios (active + run, active + error, etc.)
- **Interval-Based Audio Alerts:**
  - Play repeating sound alerts for persistent states (run button, idle mode)
  - Configurable alert intervals and duration
  - Auto-stop alerts when state changes
  - Different alert patterns for different waiting states
- **OCR Text Reading Engine:**
  - Full-screen text extraction using OCR (EasyOCR/Tesseract)
  - Parse agent dialog boxes and prompts
  - Extract command text from approval dialogs
  - Read error messages and status updates
  - Capture code snippets and file content
- **Agent Automation Loop:**
  - Auto-approve safe commands (configurable whitelist)
  - Auto-reject dangerous commands (configurable blacklist)
  - Respond to common prompts automatically
  - Chain multiple agent interactions
  - Smart decision making based on context
  - Loop detection and prevention

## 🖥️ Multi-Monitor & Multi-Agent Support

### Single Monitor Limitation
**Status**: 🔴 **Enhancement Request**

**Problem**: Currently only monitors the main laptop screen and cannot detect activity on external monitors.

**Requirements**:
- Detect and capture from external monitors
- Support for multiple display configurations
- Per-monitor template matching and state detection
- Unified state reporting across all monitors

### Multi-Agent Simultaneous Monitoring  
**Status**: 🔴 **Enhancement Request**

**Problem**: Can only run one instance at a time, limiting ability to monitor multiple agents/IDEs simultaneously.

**Requirements**:
- Run multiple instances simultaneously (up to 4 agents)
- Per-instance configuration and state management
- Isolated audio alerts per agent
- Coordinated telemetry collection
- Support for monitoring different IDEs:
  - Multiple Cursor instances
  - VS Code instances  
  - Other AI-powered editors
  - Different agent interfaces

**Technical Considerations**:
- Process isolation vs shared resources
- Port/socket management for multiple instances
- Resource usage optimization
- Cross-instance communication if needed

## 🔌 Integration & Extensibility

### MCP Server Integration
**Status**: 🔴 **Enhancement Request**

**Problem**: Need programmable hooks and server interface to enable agent automation and integration.

**Requirements**:
- **MCP Server Implementation**: Expose monitoring capabilities as Model Context Protocol server
- **Agent Hooks**: Allow agents to query current state, subscribe to state changes
- **Automation APIs**: Enable agents to trigger actions based on detected states
- **Event System**: Real-time state change notifications
- **Command Interface**: Allow external tools to control monitoring behavior

**Potential MCP Tools**:
```
get_current_state() -> {state, confidence, timestamp}
subscribe_to_changes() -> stream of state changes
trigger_action(action_type, parameters) -> success/failure
get_screen_capture() -> base64 image data
get_ocr_text() -> extracted text from current screen
```

**Integration Scenarios**:
- Agent automatically approves safe commands
- Agent chains multiple IDE interactions
- Agent responds to specific IDE states
- External monitoring dashboards
- Automated testing and validation

### Plugin Architecture
**Status**: 🔴 **Future Enhancement**

**Requirements**:
- Plugin system for custom detectors
- Custom state definitions
- User-defined automation rules
- Third-party integrations
- Custom audio/visual alerts

## 🔧 Architecture Issues

### Debug Window State Management Bug
**Status**: ✅ **Completed**

**Problem**: Debug window state management had critical issues causing UI inconsistency and application crashes.

**Issues Resolved**:
1. **Window State Desync**: Fixed window delegate handling to properly sync application state when window is closed
2. **Segmentation Fault**: Resolved memory management issues causing crashes after debug window interactions
3. **Resource Cleanup**: Implemented proper cleanup of debug window resources
4. **Button State Management**: Fixed debug button state synchronization

**Solution Implemented**:
- Added proper `NSWindowDelegate` to handle `windowWillClose:` events
- Implemented state synchronization between UI and internal application state
- Fixed PyObjC reference counting and object lifecycle management
- Added proper resource deallocation on window close

**Result**: Debug window now works reliably with no crashes or state inconsistencies.

### Multi-State Detection Problem
**Status**: 🚨 **Critical Bug**

**Problem**: The current detection system assumes mutually exclusive states, but the run command scenario reveals that multiple states can exist simultaneously:
- When run command appears, the **active button is still present**
- This creates **"active + run_command"** composite state
- Current logic tries to pick ONE winner, causing detection failures
- Confidence gap logic breaks when both states are legitimately present

**Current Behavior**:
```
idle: 1.00 | active: 0.89 | run_command: 0.45
→ Returns "unknown" (gap 0.11 < threshold 0.12)
```

**Required Architecture Changes**:
1. **Composite State Detection**: Return multiple states: `["active", "run_command"]`
2. **State Hierarchy System**: Define which states can coexist vs. which are exclusive  
3. **Priority Logic**: When overlapping states detected, determine primary vs. secondary
4. **UI Updates**: Display composite states (e.g., "🚀 active + ▶️ run")
5. **Alert Logic**: Handle alerts for composite states appropriately

**Impact**: 
- Run command detection currently unreliable
- State transitions may be missed
- User experience degraded when agent is waiting for command approval

## 🧪 Upcoming Improvements
- **~~Compact UI Design:~~** ✅ **COMPLETED**
  - ✅ ~~Smaller main control panel for better overlay experience~~
  - ✅ ~~Current state and match confidence prominently displayed~~ (enhanced with emojis)
  - ✅ ~~Essential controls (pause/resume, mute/unmute) more compact~~ (improved sizing and spacing)
  - ✅ ~~Statistics moved to popup window accessible via button~~ (already implemented)
  - ✅ ~~Optimized for screen overlay use while maintaining full functionality~~
- Bundle as a macOS .app (use `py2app` or `pyinstaller`)
- Export telemetry as JSON (added)
- Export telemetry as CSV (added)
- CLI args (e.g. `--mute`, `--headless`, `--debug`)
- Vision fallback engine (e.g. using CLIP or EasyOCR)

## 🤖 AI Interaction Features
- Enhanced OCR capabilities:
  - Extract text from agent responses
  - Real-time text detection and parsing
  - Support for multiple text regions
  - OCR-based state detection improvements
- Mouse automation and control:
  - Automated clicking on detected UI elements
  - Smart interaction with agent interface
  - Mouse position tracking and replay
  - Gesture-based commands

## 💡 Ideas
- Web dashboard for live telemetry
- Window-specific targeting (Cursor only)
- Timed disable/mute toggles
- Intelligent interaction patterns:
  - Learn from user interactions
  - Automate common response patterns
  - Context-aware clicking
