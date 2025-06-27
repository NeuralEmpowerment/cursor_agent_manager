#!/bin/bash

echo "🔍 Bad Template Detector & Fixer"
echo "================================="

# The problematic template from the logs
BAD_TEMPLATE="idle_template_20250627_101801.png"
TEMPLATE_PATH="assets/ui-cursor/agent_idle/$BAD_TEMPLATE"

echo ""
echo "Based on your diagnostic logs, this template is causing problems:"
echo "  📁 $TEMPLATE_PATH"
echo ""
echo "This idle template is getting 1.00 confidence when you're in ACTIVE mode!"
echo "This means it's too generic and matches active UI states."
echo ""

if [ -f "$TEMPLATE_PATH" ]; then
    echo "✅ Found the problematic template!"
    echo ""
    echo "Options:"
    echo "1. 🗑️  Delete the bad template (recommended)"
    echo "2. 📦 Move it to backup folder"
    echo "3. 👀 Just show me where it is"
    echo "4. ❌ Do nothing"
    echo ""
    
    read -p "Choose option (1-4): " choice
    
    case $choice in
        1)
            echo "🗑️  Deleting bad template..."
            rm "$TEMPLATE_PATH"
            echo "✅ Deleted: $TEMPLATE_PATH"
            echo "🔄 Restart the monitor with ./run.sh to see the fix!"
            ;;
        2)
            echo "📦 Creating backup folder..."
            mkdir -p "assets/ui-cursor/backup"
            mv "$TEMPLATE_PATH" "assets/ui-cursor/backup/"
            echo "✅ Moved to: assets/ui-cursor/backup/$BAD_TEMPLATE"
            echo "🔄 Restart the monitor with ./run.sh to see the fix!"
            ;;
        3)
            echo "📍 Location: $TEMPLATE_PATH"
            echo "You can manually delete or move this file."
            ;;
        4)
            echo "❌ No changes made."
            ;;
        *)
            echo "Invalid choice!"
            ;;
    esac
else
    echo "❌ Template not found at: $TEMPLATE_PATH"
    echo "Maybe it was already deleted or moved?"
fi

echo ""
echo "💡 Next steps:"
echo "1. Delete/move the bad template (if not done)"
echo "2. Restart monitor: ./run.sh"
echo "3. Capture a better idle template: ./run_capture_tool.sh"
echo "   - Make sure Cursor is clearly in IDLE state"
echo "   - Focus on unique UI elements that only appear when idle" 