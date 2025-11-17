#!/bin/bash
# Script to stop/kill ALL virus processes

cd "$(dirname "$0")"

echo "=== Stopping Virus ==="
echo ""

PID_FILE=".system_cache/virus.pid"
KILLED_COUNT=0
MAX_ATTEMPTS=3

# Function to kill a process
kill_process() {
    local pid=$1
    local attempt=$2
    
    if [ -z "$pid" ] || ! ps -p "$pid" > /dev/null 2>&1; then
        return 1
    fi
    
    echo "   Attempting to kill PID: $pid"
    
    # Try graceful kill first
    kill "$pid" 2>/dev/null
    sleep 0.5
    
    # Check if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
            echo "   ⚠️  Process still running, force killing (attempt $attempt)..."
            kill -9 "$pid" 2>/dev/null
            sleep 0.5
        else
            echo "   ❌ Failed to kill process $pid after $MAX_ATTEMPTS attempts"
            return 1
        fi
    fi
    
    # Verify it's dead
    if ps -p "$pid" > /dev/null 2>&1; then
        return 1
    else
        echo "   ✅ Process $pid killed successfully"
        return 0
    fi
}

# Method 1: Kill process from PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        echo "📄 Found PID file: $PID_FILE"
        echo "🔢 Process ID from file: $PID"
        echo ""
        
        if kill_process "$PID" 1; then
            KILLED_COUNT=$((KILLED_COUNT + 1))
        fi
        
        # Remove PID file
        rm -f "$PID_FILE"
        echo "✅ PID file removed"
        echo ""
    else
        echo "⚠️  PID file exists but process is not running"
        echo "   Removing stale PID file..."
        rm -f "$PID_FILE"
        echo ""
    fi
fi

# Method 2: Find and kill ALL virus processes
echo "🔍 Searching for ALL virus processes..."
VIRUS_PROCESSES=$(ps -fA | grep -E "virus_core\.py" | grep -v grep)

if [ -z "$VIRUS_PROCESSES" ]; then
    if [ "$KILLED_COUNT" -eq 0 ]; then
        echo "❌ No virus processes found"
        echo "   Virus is not running"
    else
        echo "✅ All virus processes stopped"
    fi
    exit 0
fi

echo "Found virus processes:"
echo "$VIRUS_PROCESSES" | while read -r line; do
    echo "   $line"
done
echo ""

# Kill all found processes
echo "Killing all virus processes..."
while IFS= read -r line; do
    PID=$(echo "$line" | awk '{print $2}')
    if [ -n "$PID" ]; then
        # Skip if we already killed this one from PID file
        if [ "$KILLED_COUNT" -eq 0 ] || [ "$PID" != "$(cat "$PID_FILE" 2>/dev/null)" ]; then
            for attempt in $(seq 1 $MAX_ATTEMPTS); do
                if kill_process "$PID" "$attempt"; then
                    KILLED_COUNT=$((KILLED_COUNT + 1))
                    break
                fi
            done
        fi
    fi
done <<< "$VIRUS_PROCESSES"

echo ""

# Final check - make sure all are dead
echo "🔍 Final check for remaining processes..."
REMAINING=$(ps -fA | grep -E "virus_core\.py" | grep -v grep)

if [ -n "$REMAINING" ]; then
    echo "⚠️  Warning: Some processes may still be running:"
    echo "$REMAINING"
    echo ""
    echo "Trying one more time with force kill..."
    
    # Force kill all remaining
    echo "$REMAINING" | awk '{print $2}' | while read -r pid; do
        if [ -n "$pid" ]; then
            echo "   Force killing PID: $pid"
            kill -9 "$pid" 2>/dev/null
            sleep 0.3
        fi
    done
    
    sleep 1
    
    # Check again
    REMAINING=$(ps -fA | grep -E "virus_core\.py" | grep -v grep)
    if [ -n "$REMAINING" ]; then
        echo "❌ Some processes could not be killed:"
        echo "$REMAINING"
        exit 1
    fi
fi

# Remove PID file if it still exists
rm -f "$PID_FILE"

echo "✅ All virus processes stopped successfully"
echo "   Total processes killed: $KILLED_COUNT"

