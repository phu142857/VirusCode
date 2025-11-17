#!/bin/bash
# Script to COMPLETELY REMOVE all virus files and persistence mechanisms

cd "$(dirname "$0")"

echo "=== COMPLETE VIRUS CLEANUP ==="
echo ""
echo "⚠️  WARNING: This will remove ALL virus files and persistence mechanisms!"
echo "   Press Ctrl+C within 5 seconds to cancel..."
sleep 5
echo ""

HOME_DIR="$HOME"

# ============================================
# STEP 1: STOP VIRUS FIRST
# ============================================
echo "🔧 Step 1: Stopping virus..."
if [ -f "./stop_virus.sh" ]; then
    bash ./stop_virus.sh
    sleep 2
else
    echo "   ⚠️  stop_virus.sh not found, trying manual stop..."
    pkill -f virus_core.py 2>/dev/null
    sleep 2
fi
echo ""

# ============================================
# STEP 2: REMOVE SYSTEMD SERVICE
# ============================================
echo "🔧 Step 2: Removing systemd service..."
SYSTEMD_SERVICE="$HOME_DIR/.config/systemd/user/system-update.service"
SYSTEMD_DIR="$HOME_DIR/.config/systemd/user"

if [ -f "$SYSTEMD_SERVICE" ]; then
    systemctl --user stop system-update.service 2>/dev/null
    systemctl --user disable system-update.service 2>/dev/null
    rm -f "$SYSTEMD_SERVICE"
    echo "   ✅ Removed: $SYSTEMD_SERVICE"
    
    systemctl --user daemon-reload 2>/dev/null
    echo "   ✅ Reloaded systemd daemon"
else
    echo "   ℹ️  No systemd service found"
fi
echo ""

# ============================================
# STEP 3: REMOVE AUTOSTART FILE
# ============================================
echo "🔧 Step 3: Removing autostart file..."
AUTOSTART_FILE="$HOME_DIR/.config/autostart/system-update.desktop"

if [ -f "$AUTOSTART_FILE" ]; then
    rm -f "$AUTOSTART_FILE"
    echo "   ✅ Removed: $AUTOSTART_FILE"
else
    echo "   ℹ️  No autostart file found"
fi
echo ""

# ============================================
# STEP 4: REMOVE REPLICATED FILES
# ============================================
echo "🔧 Step 4: Removing replicated virus files..."
REPLICATED_FILES=(
    "$HOME_DIR/.cache/system-update.py"
    "$HOME_DIR/.local/share/system-service.py"
    "/tmp/.system-update.py"
)

REMOVED_COUNT=0
for file in "${REPLICATED_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "   ✅ Removed: $file"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
    fi
done

if [ "$REMOVED_COUNT" -eq 0 ]; then
    echo "   ℹ️  No replicated files found"
fi
echo ""

# ============================================
# STEP 5: REMOVE INJECTED CODE FROM FILES
# ============================================
echo "🔧 Step 5: Removing injected code from testInjection_* files..."
INJECTED_FILES=$(find "$HOME_DIR" -name "testInjection_*" -type f 2>/dev/null | head -20)

if [ -n "$INJECTED_FILES" ]; then
    echo "   Found injected files:"
    echo "$INJECTED_FILES" | while read -r file; do
        if grep -q "VIRUS_INJECTED_MARKER" "$file" 2>/dev/null; then
            # Remove injected code (between VIRUS_INJECTED_MARKER and END VIRUS_INJECTED_MARKER)
            sed -i '/# VIRUS_INJECTED_MARKER/,/# END VIRUS_INJECTED_MARKER/d' "$file" 2>/dev/null
            sed -i '/\/\/ VIRUS_INJECTED_MARKER/,/\/\/ END VIRUS_INJECTED_MARKER/d' "$file" 2>/dev/null
            echo "   ✅ Cleaned: $file"
        fi
    done
else
    echo "   ℹ️  No testInjection_* files found"
fi
echo ""

# ============================================
# STEP 6: REMOVE VIRUS DATA DIRECTORY
# ============================================
echo "🔧 Step 6: Removing virus data directory..."
DATA_DIR=".system_cache"

if [ -d "$DATA_DIR" ]; then
    echo "   ⚠️  Found data directory: $DATA_DIR"
    echo "   This contains: keyboard logs, screenshots, collected data, etc."
    read -p "   Delete this directory? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm -rf "$DATA_DIR"
        echo "   ✅ Removed: $DATA_DIR"
    else
        echo "   ℹ️  Skipped: $DATA_DIR (kept for reference)"
    fi
else
    echo "   ℹ️  No data directory found"
fi
echo ""

# ============================================
# STEP 7: FINAL VERIFICATION
# ============================================
echo "🔧 Step 7: Final verification..."
sleep 2

# Check for running processes
REMAINING_PROCESSES=$(ps -fA | grep -E "virus_core\.py" | grep -v grep)
if [ -n "$REMAINING_PROCESSES" ]; then
    echo "   ⚠️  WARNING: Virus processes still running:"
    echo "$REMAINING_PROCESSES"
    echo ""
    echo "   Try running: pkill -9 -f virus_core.py"
else
    echo "   ✅ No virus processes running"
fi

# Check for remaining persistence
REMAINING_FILES=0
[ -f "$SYSTEMD_SERVICE" ] && REMAINING_FILES=$((REMAINING_FILES + 1))
[ -f "$AUTOSTART_FILE" ] && REMAINING_FILES=$((REMAINING_FILES + 1))

if [ "$REMAINING_FILES" -gt 0 ]; then
    echo "   ⚠️  WARNING: Some persistence files still exist"
else
    echo "   ✅ No persistence files found"
fi
echo ""

echo "=========================================="
echo "✅ CLEANUP COMPLETE"
echo "=========================================="
echo ""
echo "ℹ️  Summary:"
echo "   - Systemd service: $( [ -f "$SYSTEMD_SERVICE" ] && echo "⚠️  STILL EXISTS" || echo "✅ REMOVED" )"
echo "   - Autostart file: $( [ -f "$AUTOSTART_FILE" ] && echo "⚠️  STILL EXISTS" || echo "✅ REMOVED" )"
echo "   - Replicated files: ✅ REMOVED"
echo "   - Injected code: ✅ CLEANED"
echo ""
echo "ℹ️  Note: The virus source code in this directory is NOT removed."
echo "   To completely remove, delete the entire VirusCode directory."

