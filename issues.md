# Issues and Enhancements

## ✅ Current
- Working state machine and detector engine
- Control panel UI with improved formatting and emojis
- Telemetry logs (text)
- Organized asset structure (images and audio files properly organized)
- Enhanced UI formatting with better spacing, larger buttons, and visual state indicators

## 🚀 Next Steps - Agent Automation Loop
- **Expanded State Detection:**
  - Detect "command approval" state (when agent asks permission to run commands)
  - Detect "waiting for user input" state
  - Detect "error/failed command" state
  - Detect "tool selection" state
  - Detect "code generation complete" state
  - Detect "active awaiting action" state (run_button.png - agent ready but waiting for user)
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
