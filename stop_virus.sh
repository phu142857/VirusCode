#!/bin/bash
# Script to COMPLETELY stop and disable virus (including persistence mechanisms)

cd "$(dirname "$0")"

echo "=== COMPLETELY STOPPING VIRUS ==="
echo ""

PID_FILE=".system_cache/virus.pid"
KILLED_COUNT=0
MAX_ATTEMPTS=3
HOME_DIR="$HOME"

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

# ============================================
# STEP 1: STOP AND DISABLE SYSTEMD SERVICE
# ============================================
echo "🔧 Step 1: Disabling systemd service..."
SYSTEMD_SERVICE="$HOME_DIR/.config/systemd/user/system-update.service"

if [ -f "$SYSTEMD_SERVICE" ]; then
    echo "   Found systemd service: $SYSTEMD_SERVICE"
    
    # Stop the service
    systemctl --user stop system-update.service 2>/dev/null
    echo "   ✅ Stopped systemd service"
    
    # Disable the service (prevents auto-start)
    systemctl --user disable system-update.service 2>/dev/null
    echo "   ✅ Disabled systemd service (will not auto-start)"
    
    # Reload systemd
    systemctl --user daemon-reload 2>/dev/null
    echo "   ✅ Reloaded systemd daemon"
else
    echo "   ℹ️  No systemd service found"
fi
echo ""

# ============================================
# STEP 2: DISABLE AUTOSTART DESKTOP FILE
# ============================================
echo "🔧 Step 2: Disabling autostart..."
AUTOSTART_FILE="$HOME_DIR/.config/autostart/system-update.desktop"

if [ -f "$AUTOSTART_FILE" ]; then
    echo "   Found autostart file: $AUTOSTART_FILE"
    
    # Disable by setting X-GNOME-Autostart-enabled=false
    if grep -q "X-GNOME-Autostart-enabled=true" "$AUTOSTART_FILE" 2>/dev/null; then
        sed -i 's/X-GNOME-Autostart-enabled=true/X-GNOME-Autostart-enabled=false/' "$AUTOSTART_FILE"
        echo "   ✅ Disabled autostart (set to false)"
    fi
    
    # Or remove it completely (uncomment to remove instead of disable)
    # rm -f "$AUTOSTART_FILE"
    # echo "   ✅ Removed autostart file"
else
    echo "   ℹ️  No autostart file found"
fi
echo ""

# ============================================
# STEP 3: KILL ALL VIRUS PROCESSES
# ============================================
echo "🔧 Step 3: Killing all virus processes..."

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

if [ -n "$VIRUS_PROCESSES" ]; then
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
            for attempt in $(seq 1 $MAX_ATTEMPTS); do
                if kill_process "$PID" "$attempt"; then
                    KILLED_COUNT=$((KILLED_COUNT + 1))
                    break
                fi
            done
        fi
    done <<< "$VIRUS_PROCESSES"
    echo ""
fi

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
    else
        echo "✅ All processes killed"
    fi
else
    if [ "$KILLED_COUNT" -eq 0 ]; then
        echo "ℹ️  No virus processes were running"
    else
        echo "✅ All virus processes stopped"
    fi
fi
echo ""

# ============================================
# STEP 4: WAIT AND VERIFY NO RESTART
# ============================================
echo "🔧 Step 4: Waiting 15 seconds to verify virus doesn't restart..."
sleep 15

REMAINING=$(ps -fA | grep -E "virus_core\.py" | grep -v grep)
if [ -n "$REMAINING" ]; then
    echo "⚠️  WARNING: Virus restarted! This means persistence is still active."
    echo "   Remaining processes:"
    echo "$REMAINING"
    echo ""
    echo "   Try running this script again, or manually check:"
    echo "   - systemctl --user status system-update.service"
    echo "   - cat $HOME_DIR/.config/autostart/system-update.desktop"
    echo "   - Check for injected files (testInjection_*)"
else
    echo "✅ Virus did not restart - persistence disabled successfully"
fi
echo ""

# Remove PID file if it still exists
rm -f "$PID_FILE"

echo "=========================================="
echo "✅ VIRUS STOPPED AND PERSISTENCE DISABLED"
echo "=========================================="
echo "   Total processes killed: $KILLED_COUNT"
echo ""
echo "ℹ️  Note: To permanently remove virus, also delete:"
echo "   - $SYSTEMD_SERVICE"
echo "   - $AUTOSTART_FILE"
echo "   - Replicated files in ~/.cache/, ~/.local/share/, /tmp/"
echo "   - Injected code in testInjection_* files"

