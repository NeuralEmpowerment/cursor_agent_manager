#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip using python -m pip (works better with pyenv)
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements using python -m pip (works better with pyenv)
echo "Installing dependencies from requirements.txt..."
python -m pip install -r requirements.txt

# Make run script executable
chmod +x run.sh

echo "Setup complete!"
echo "To run the program, use: ./run.sh" 