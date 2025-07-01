#!/bin/bash
set -e  # Exit on error

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    python -m pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if required files exist
if [ ! -f "agent_monitor_poc.py" ]; then
    echo "Error: agent_monitor_poc.py not found!"
    exit 1
fi

# Run the application using python (which will be the venv python after activation)
echo "Starting Agent Monitor..."
python agent_monitor_poc.py
