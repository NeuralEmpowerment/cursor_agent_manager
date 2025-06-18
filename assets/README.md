# Assets Directory

This directory contains all static assets for the Agent Monitor POC application, organized by type and purpose.

## Directory Structure

```
assets/
├── audio/
│   ├── alerts/          # Sound files for different alert types
│   │   ├── alert_*.wav  # Various alert sound files
│   └── scripts/         # Python scripts for audio generation
│       ├── sound_generator.py
│       ├── create_alert.py
│       └── custom_alert_example.py
└── ui-cursor/           # Cursor IDE UI element images
    ├── run_button.png
    ├── generating_button.png
    └── idle_button.png
```

## Organization Principles

- **By Type**: Assets are first organized by their media type (audio, ui-cursor)
- **By Application**: UI assets are organized by the specific application they target (Cursor IDE)
- **By Function**: Within each type, assets are further organized by their specific function
- **Descriptive Names**: All files use descriptive names that indicate their purpose

## Usage

When referencing these assets in code, use the full path from the project root:
- Audio alerts: `assets/audio/alerts/alert_*.wav`
- Cursor UI elements: `assets/ui-cursor/*_button.png`
- Audio scripts: `assets/audio/scripts/*.py`

This organization keeps the main source directory clean while making assets easy to find and manage. 