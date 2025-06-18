# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-12-19

### Added
- **Enhanced Visual Status Indicators** - Emoji status display for instant recognition
  - 💤 emoji for idle state detection
  - 🚀 emoji for active/generating state
  - ❓ emoji for unknown states
- **Professional Asset Organization** - Dedicated `/assets` directory structure
  - `/assets/ui/buttons/` for UI template images
  - `/assets/audio/alerts/` for sound notification files  
  - `/assets/audio/scripts/` for audio generation utilities
- **Enhanced Visual Hierarchy** - Improved typography and spacing throughout interface

### Changed
- **Improved UI Formatting** - Better spacing, typography, and layout design
  - Increased status text size from 13pt to 15pt for better readability
  - Enhanced button sizing from 45x28 to 50x32 pixels for improved usability
  - Better padding and spacing between UI elements for professional appearance
  - Optimized confidence display with 11pt sizing for secondary information
- **Project Structure Reorganization** - Clean separation of assets from source code
  - Moved button template images from root to organized asset directory
  - Consolidated audio files from scattered `/audio` directory to structured location
  - Updated all asset path references in codebase for new organization

### Updated
- **Asset Path References** - All file paths updated to new organized structure
- **Issues Documentation** - Marked completed UI improvements and asset organization
- **Root Directory Cleanup** - Removed asset files from main source directory

### Technical Improvements
- **Maintainable Code Structure** - Better organization for long-term project health
- **Asset Discoverability** - Clear, logical file organization by type and function
- **Enhanced User Experience** - Visual feedback improvements with emoji indicators

## [1.0.0] - 2024-12-19

### Added

#### Core Application
- **Agent Monitor POC** - Advanced macOS application for monitoring Cursor IDE agent states
- **Template Matching Detection** - High-confidence OpenCV-based UI element detection
- **OCR State Detection** - Pytesseract-based fallback detection method
- **Strategy Pattern Architecture** - Modular detection system with pluggable strategies
- **State Machine** - Intelligent agent interaction flow management
- **Native macOS GUI** - NSWindow-based control panel with real-time monitoring
- **Auto-click Functionality** - Optional automated interaction with idle agents

#### Telemetry & Analytics System
- **SQLite Database** - Persistent event logging and metrics storage
- **Repository Pattern** - Clean data access layer with configurable retention
- **Event Types** - Structured logging for idle detection, active states, and failures
- **Analytics Service** - Statistical analysis with hourly, daily, and custom time ranges
- **CLI Analytics Tool** - Command-line interface for data analysis and reporting
- **Data Export** - CSV and JSON export capabilities for telemetry data

#### Audio Alert System
- **10 Alert Sounds** - Professional audio notifications for different states
  - Idle detection, error states, success confirmations
  - Thinking/processing, completed tasks, warnings
  - Ascending/descending alerts, custom tada sound
- **Sound Generator** - Procedural audio creation utilities
- **Audio Examples** - Custom alert creation examples and utilities
- **Sound Player Integration** - Seamless audio feedback with state changes

#### Template Recognition
- **UI Template Images** - High-quality button detection templates
  - Idle state button recognition
  - Active/generating state button recognition  
  - Run button detection
- **Confidence Scoring** - Template matching with adjustable thresholds
- **Match Rectangle Tracking** - Precise UI element location detection

#### Development Tools
- **Setup Scripts** - Automated environment configuration
- **Run Scripts** - Easy application launch and execution
- **Test Suite** - Comprehensive telemetry system validation
- **Development Utilities** - Quickstart testing and debugging tools

#### Documentation
- **Comprehensive README** - Project overview, setup, and usage instructions
- **Developer Quickstart** - Fast-track guide for contributors
- **Telemetry Documentation** - Complete analytics system documentation
- **Known Issues Guide** - Gotchas and troubleshooting information
- **Issues Tracking** - Development roadmap and known limitations

#### Configuration
- **Dependency Management** - Complete requirements.txt with version pinning
- **Environment Setup** - Virtual environment configuration
- **VSCode Integration** - Optimized development settings and configuration
- **Git Configuration** - Professional .gitignore with Python/macOS/VSCode patterns

### Technical Features

#### Architecture
- **Dependency Injection** - Clean IoC container for service management
- **Protocol-Based Interfaces** - Type-safe service contracts
- **Modular Design** - Loosely coupled components for maintainability
- **Error Handling** - Robust exception management and logging

#### macOS Integration
- **AppKit Integration** - Native macOS UI components
- **Auto Layout** - Modern constraint-based UI layout
- **Window Management** - Floating panels with transparency controls
- **Menu Integration** - Native menu bar and keyboard shortcuts

#### Detection Engine
- **Multi-Strategy Detection** - Template matching + OCR fallback
- **Confidence Metrics** - Detailed matching confidence reporting
- **Diagnostic Mode** - Enhanced debugging and detection analysis
- **Real-time Processing** - Efficient screenshot analysis and state tracking

#### Performance
- **Optimized Screenshots** - Efficient image capture and processing
- **Cached Audio** - Sound file caching for instant playback
- **Background Processing** - Non-blocking state detection and UI updates
- **Memory Management** - Proper resource cleanup and lifecycle management

### Dependencies
- **pyautogui** - Cross-platform GUI automation
- **pync** - macOS notification center integration
- **pytesseract** - OCR text recognition
- **Pillow** - Image processing and manipulation
- **simpleaudio** - Cross-platform audio playback
- **numpy** - Numerical computing for image processing
- **opencv-python** - Computer vision and template matching
- **AppKit/Foundation** - macOS native UI frameworks

### Compatibility
- **macOS Only** - Optimized for macOS 10.14+ (Darwin 24.5.0 tested)
- **Python 3.8+** - Modern Python features and type hints
- **Cursor IDE** - Specifically designed for Cursor IDE agent monitoring
- **ARM64/Intel** - Universal compatibility with Apple Silicon and Intel Macs

[1.1.0]: https://github.com/your-repo/agent-monitor-poc/releases/tag/v1.1.0
[1.0.0]: https://github.com/your-repo/agent-monitor-poc/releases/tag/v1.0.0 