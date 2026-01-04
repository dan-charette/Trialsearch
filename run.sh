#!/bin/bash

# Clinical Trials Search - Run Script
# Creates/activates venv and runs the Flask application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# Run the application
echo "Starting Clinical Trials Search on http://localhost:5000"
python "$SCRIPT_DIR/run.py"
