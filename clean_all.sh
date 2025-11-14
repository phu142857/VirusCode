#!/bin/bash
# Clean all generated data, logs, and cache files
# Keeps only code files (.py, .sh, .md, .txt config files, etc.)

cd "$(dirname "$0")"

# Check for dry-run flag
DRY_RUN=false
if [ "$1" == "--dry-run" ] || [ "$1" == "-n" ]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No files will be deleted"
    echo ""
fi

echo "=========================================="
echo "Cleaning All Generated Data"
echo "=========================================="
echo ""

# Function to remove file/directory
remove_item() {
    local item="$1"
    local description="$2"
    
    if [ -e "$item" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "   🔍 Would remove: $item"
        else
            rm -rf "$item"
            echo "   ✅ Removed: $description"
        fi
    else
        echo "   ℹ️  $description not found (already clean)"
    fi
}

# Remove .system_cache directory (all logs, data, screenshots)
echo "🗑️  Removing .system_cache/ directory..."
remove_item ".system_cache" ".system_cache/"

# Remove any other generated log files in root
echo ""
echo "🗑️  Removing log files..."
for file in keyboard_log.txt activity_log.txt screenshots; do
    remove_item "$file" "$file"
done

# Remove Python cache files (excluding venv/)
echo ""
echo "🗑️  Removing Python cache files..."
if [ "$DRY_RUN" = true ]; then
    find . -type d -name "__pycache__" ! -path "./venv/*" 2>/dev/null | while read dir; do
        echo "   🔍 Would remove: $dir"
    done
    find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".DS_Store" \) ! -path "./venv/*" 2>/dev/null | while read file; do
        echo "   🔍 Would remove: $file"
    done
else
    find . -type d -name "__pycache__" ! -path "./venv/*" -exec rm -rf {} + 2>/dev/null
    find . -type f -name "*.pyc" ! -path "./venv/*" -delete 2>/dev/null
    find . -type f -name "*.pyo" ! -path "./venv/*" -delete 2>/dev/null
    find . -type f -name ".DS_Store" ! -path "./venv/*" -delete 2>/dev/null
    echo "   ✅ Removed Python cache files (venv/ excluded)"
fi

# Remove any .pid files (excluding venv/)
echo ""
echo "🗑️  Removing PID files..."
if [ "$DRY_RUN" = true ]; then
    find . -type f -name "*.pid" ! -path "./venv/*" 2>/dev/null | while read file; do
        echo "   🔍 Would remove: $file"
    done
else
    find . -type f -name "*.pid" ! -path "./venv/*" -delete 2>/dev/null
    echo "   ✅ Removed PID files"
fi

# Remove any temporary files (excluding venv/)
echo ""
echo "🗑️  Removing temporary files..."
if [ "$DRY_RUN" = true ]; then
    find . -type f -name "*.tmp" ! -path "./venv/*" 2>/dev/null | while read file; do
        echo "   🔍 Would remove: $file"
    done
    find . -type f -name "*.log" ! -name "*.md" ! -path "./venv/*" 2>/dev/null | while read file; do
        echo "   🔍 Would remove: $file"
    done
else
    find . -type f -name "*.tmp" ! -path "./venv/*" -delete 2>/dev/null
    find . -type f -name "*.log" ! -name "*.md" ! -path "./venv/*" -delete 2>/dev/null
    echo "   ✅ Removed temporary files"
fi

echo ""
echo "=========================================="
if [ "$DRY_RUN" = true ]; then
    echo "🔍 Dry Run Complete - No files were deleted"
else
    echo "✅ Cleanup Complete!"
fi
echo "=========================================="
echo ""
echo "Files that are KEPT:"
echo "  📄 Code files (.py)"
echo "  📜 Scripts (.sh)"
echo "  📖 Documentation (.md)"
echo "  ⚙️  Config files (requirements.txt, virus_config.py, etc.)"
echo "  📁 venv/ (virtual environment)"
echo ""
if [ "$DRY_RUN" = false ]; then
    echo "All generated data, logs, and cache have been removed."
fi
echo ""

