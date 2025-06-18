#!/bin/bash
set -e  # Exit on error

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
if [ ! -f "agent_monitor_poc.py" ]; then
    echo "Error: agent_monitor_poc.py not found!"
    exit 1
fi

if [ ! -f "idle_button.png" ] || [ ! -f "generating_button.png" ]; then
    echo "Warning: Template images not found. Make sure to have idle_button.png and generating_button.png in the current directory."
fi

# Run the application
echo "Starting Agent Monitor..."
python3 agent_monitor_poc.py
