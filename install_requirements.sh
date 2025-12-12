#!/bin/bash
# Standalone script to install requirements with error handling

cd "$(dirname "$0")"

# Activate venv if exists, otherwise use system python
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Using virtual environment"
else
    echo "⚠️  No virtual environment found. Using system Python."
    echo "   Consider creating venv first: python3 -m venv venv"
fi

# Clear pip cache to avoid corrupted wheel files
echo "Clearing pip cache..."
pip cache purge 2>/dev/null || rm -rf ~/.cache/pip/wheels/* 2>/dev/null

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --no-cache-dir

# Install packages one by one to identify problematic packages
echo "Installing requirements..."
packages=(
    "pygame>=2.6.0"
    "pynput>=1.7.6"
    "psutil>=5.9.0"
    "Pillow>=10.0.0"
    "pyperclip>=1.8.2"
    "requests>=2.31.0"
    "python-xlib>=0.33"
    "cryptography>=41.0.0"
)

# Try to install evdev separately (may fail on some systems)
echo "Attempting to install evdev..."
pip install --no-cache-dir evdev>=1.9.0 2>&1 | grep -v "ERROR" || {
    echo "⚠️  evdev installation failed (may require system packages)"
    echo "   On Ubuntu/Debian: sudo apt-get install python3-evdev"
    echo "   On Fedora: sudo dnf install python3-evdev"
}

# Install other packages
for package in "${packages[@]}"; do
    echo "Installing $package..."
    pip install --no-cache-dir "$package" || {
        echo "⚠️  Failed to install $package"
    }
done

# Verify critical packages
echo ""
echo "Verifying installations..."
python3 -c "import cryptography; print('✓ cryptography')" || echo "✗ cryptography MISSING"
python3 -c "import pygame; print('✓ pygame')" || echo "✗ pygame MISSING"
python3 -c "import pynput; print('✓ pynput')" || echo "✗ pynput MISSING"
python3 -c "import psutil; print('✓ psutil')" || echo "✗ psutil MISSING"
python3 -c "import PIL; print('✓ Pillow')" || echo "✗ Pillow MISSING"

echo ""
echo "✅ Installation complete!"

