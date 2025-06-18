# UI Template Organization

This directory contains organized template images for the Agent Monitor detection system.

## Directory Structure

```
assets/ui-cursor/
├── agent_active/           # Templates for when the agent is actively generating
│   ├── generating_button.png
│   └── [add more screenshots here]
│
├── agent_idle/             # Templates for when the agent is idle/waiting
│   ├── idle_button.png
│   └── [add more screenshots here]
│
└── run_command/           # Templates for when ready to run commands
    ├── run_button.png
    └── [add more screenshots here]
```

## How to Add New Templates

### Easy Template Management! 🎯

1. **Take a screenshot** when Cursor is in the desired state
2. **Crop the image** to show just the relevant UI element (button, indicator, etc.)
3. **Drop the image** into the appropriate folder:
   - `agent_active/` - When AI is actively generating code/responses
   - `agent_idle/` - When AI is waiting for input or idle
   - `run_command/` - When there's a run/execute button ready to click
4. **Restart the monitor** - It will automatically load all images from these folders

### Supported Image Formats
- PNG (recommended)
- JPG/JPEG
- BMP
- TIFF

### Template Guidelines
- **Keep templates small** - Focus on the specific button/indicator
- **High contrast** - Ensure clear, distinct features
- **Multiple variations** - Add different lighting conditions, states, etc.
- **Avoid surrounding UI** - Don't include elements that might change

## State Detection Logic

- **IDLE State**: Detected when templates from `agent_idle/` OR `run_command/` match
- **ACTIVE State**: Detected when templates from `agent_active/` match
- **Confidence-based**: Uses the highest confidence match from all templates in relevant folders

## Benefits of This Organization

✅ **Easy Management**: Just drop new images into folders
✅ **Automatic Loading**: No need to edit configuration files
✅ **Multiple Variations**: Support many template variations per state
✅ **Clear Organization**: Obvious where each type of template belongs
✅ **Scalable**: Easy to add new states or template types

## Testing Your Templates

Run the test script to validate your templates:
```bash
python3 test_detection.py
```

This will show:
- Which templates loaded successfully
- Current detection confidence
- Template matching performance

## Troubleshooting

### No Detection
- Add more template variations to the relevant folder
- Check image quality and clarity
- Use the test script to see confidence scores

### False Positives
- Ensure templates are distinct between folders
- Crop templates more precisely
- Remove ambiguous templates

### State Switching
- Check confidence gaps in test script
- Add more clear template examples
- Consider adjusting confidence thresholds in configuration 