#!/bin/bash
# Start virus independently (for testing)

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting virus..."
python3 virus_core.py

