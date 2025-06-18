# Issues and Enhancements

## ✅ Current
- Working state machine and detector engine
- Control panel UI with improved formatting and emojis
- Telemetry logs (text)
- Organized asset structure (images and audio files properly organized)
- Enhanced UI formatting with better spacing, larger buttons, and visual state indicators

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

## 🔧 Architecture Issues

### Multi-State Detection Problem
**Status**: 🚨 **Critical Issue**

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
