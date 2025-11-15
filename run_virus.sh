#!/bin/bash
# Wrapper script to run virus with venv if available

cd "$(dirname "$0")"

# Check if venv exists and activate it
if [ -d "venv" ]; then
    source venv/bin/activate
    python3 virus_core.py "$@"
else
    # No venv, use system Python
    python3 virus_core.py "$@"
fi

