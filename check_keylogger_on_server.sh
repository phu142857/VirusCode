#!/bin/bash
# Script to check if keylogger logs are present in received data on server

DATA_DIR="received_data"

echo "============================================================"
echo "🔍 CHECKING KEYLOGGER LOGS ON SERVER"
echo "============================================================"
echo ""

if [ ! -d "$DATA_DIR" ]; then
    echo "❌ Directory $DATA_DIR not found"
    exit 1
fi

# Find all folders (new structure) or plain JSON files (old structure)
FOLDERS=$(ls -td "$DATA_DIR"/*/ 2>/dev/null | head -5)
OLD_FILES=$(find "$DATA_DIR" -maxdepth 1 -name "*_plain.json" 2>/dev/null | sort -r | head -5)

if [ -z "$FOLDERS" ] && [ -z "$OLD_FILES" ]; then
    echo "❌ No data folders or files found in $DATA_DIR"
    exit 1
fi

# Check new folder structure first
if [ -n "$FOLDERS" ]; then
    echo "📁 Found $(echo "$FOLDERS" | wc -l) folder(s) (new structure)"
    echo ""
    
    for folder in $FOLDERS; do
        folder_name=$(basename "$folder")
        echo "============================================================"
        echo "📁 Folder: $folder_name"
        echo "============================================================"
        
        # Check keyboard_log.txt (extracted file)
        kb_file="$folder/keyboard_log.txt"
        if [ -f "$kb_file" ]; then
            KB_SIZE=$(wc -c < "$kb_file" 2>/dev/null || echo 0)
            KB_LINES=$(wc -l < "$kb_file" 2>/dev/null || echo 0)
            
            echo "✅ keyboard_log.txt: EXISTS"
            echo "   Size: $KB_SIZE characters"
            echo "   Lines: $KB_LINES"
            echo "   File: $kb_file"
            
            if [ "$KB_SIZE" -gt 0 ]; then
                echo "✅ keyboard_log.txt has CONTENT"
                echo ""
                echo "📝 First 200 characters:"
                head -c 200 "$kb_file"
                echo ""
                echo ""
                echo "📝 Last 200 characters:"
                tail -c 200 "$kb_file"
                echo ""
            else
                echo "❌ keyboard_log.txt is EMPTY"
            fi
        else
            echo "❌ keyboard_log.txt: NOT FOUND"
        fi
        
        # Also check exploited_data.json for keyboard_logs field
        data_file="$folder/exploited_data.json"
        if [ -f "$data_file" ] && command -v jq &> /dev/null; then
            HAS_KEYBOARD_LOGS=$(jq -r 'has("keyboard_logs")' "$data_file" 2>/dev/null)
            if [ "$HAS_KEYBOARD_LOGS" = "true" ]; then
                KB_SIZE_JSON=$(jq -r '.keyboard_logs_size // 0' "$data_file" 2>/dev/null)
                echo "✅ keyboard_logs field in exploited_data.json: $KB_SIZE_JSON chars"
            fi
        fi
        echo ""
    done
fi

# Check old file structure (backward compatibility)
if [ -n "$OLD_FILES" ] && [ -z "$FOLDERS" ]; then
    echo "📁 Found $(echo "$OLD_FILES" | wc -l) file(s) (old structure)"
    echo ""
    
    for file in $OLD_FILES; do
        echo "============================================================"
        echo "📄 File: $(basename "$file")"
        echo "============================================================"
        
        if command -v jq &> /dev/null; then
            HAS_KEYBOARD_LOGS=$(jq -r 'has("keyboard_logs")' "$file" 2>/dev/null)
            KB_SIZE=$(jq -r '.keyboard_logs_size // 0' "$file" 2>/dev/null)
            KB_LINES=$(jq -r '.keyboard_logs_lines // 0' "$file" 2>/dev/null)
            
            if [ "$HAS_KEYBOARD_LOGS" = "true" ]; then
                echo "✅ keyboard_logs field: EXISTS"
                echo "   Size: $KB_SIZE characters"
                echo "   Lines: $KB_LINES"
                
                KB_CONTENT=$(jq -r '.keyboard_logs' "$file" 2>/dev/null)
                if [ -n "$KB_CONTENT" ] && [ "$KB_CONTENT" != "null" ] && [ ${#KB_CONTENT} -gt 0 ]; then
                    echo "✅ keyboard_logs has CONTENT: ${#KB_CONTENT} chars"
                    echo ""
                    echo "📝 First 200 characters:"
                    echo "$KB_CONTENT" | head -c 200
                    echo ""
                    echo ""
                    echo "📝 Last 200 characters:"
                    echo "$KB_CONTENT" | tail -c 200
                    echo ""
                else
                    echo "❌ keyboard_logs is EMPTY or NULL"
                fi
            else
                echo "❌ keyboard_logs field: NOT FOUND"
            fi
        else
            echo "⚠️  jq not installed. Install with: sudo apt install jq"
        fi
        echo ""
    done
fi

echo "============================================================"
echo "💡 To view full keyboard logs:"
if [ -n "$FOLDERS" ]; then
    echo "   cat $DATA_DIR/*/keyboard_log.txt | less"
else
    echo "   cat $DATA_DIR/*_plain.json | jq -r '.keyboard_logs' | less"
fi
echo "============================================================"
