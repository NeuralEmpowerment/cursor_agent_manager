#!/bin/bash
set -e  # Exit on error

echo "🎯 Agent Monitor - Template Capture Tool"
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if required files exist
if [ ! -f "capture_template.py" ]; then
    echo "Error: capture_template.py not found!"
    exit 1
fi

if [ ! -f "agent_monitor_poc.py" ]; then
    echo "Error: agent_monitor_poc.py not found!"
    exit 1
fi

echo ""
echo "📸 Template Capture Tool Instructions:"
echo "-------------------------------------"
echo "This tool helps you capture new UI templates when detection isn't working."
echo ""
echo "Usage:"
echo "1. Get Cursor into the state you want to capture:"
echo "   • IDLE: Agent waiting for input"
echo "   • ACTIVE: Agent generating/thinking" 
echo "   • RUN_COMMAND: Ready to execute command"
echo ""
echo "2. Choose option 2 to save current screen as template"
echo "3. Select the appropriate state (1=idle, 2=active, 3=run_command)"
echo "4. Restart the monitor with ./run.sh to use new templates"
echo ""
echo "Templates are saved to:"
echo "   • assets/ui-cursor/agent_idle/"
echo "   • assets/ui-cursor/agent_active/"
echo "   • assets/ui-cursor/run_command/"
echo ""

# Run the capture template tool
python3 capture_template.py 