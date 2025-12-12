#!/bin/bash

# Activate virtual environment and run the virus
cd "$(dirname "$0")"

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "Installing requirements..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Virtual environment created and requirements installed."
else
    # Activate existing virtual environment
    source venv/bin/activate
fi

# Run the virus core
python3 virus_core.py

