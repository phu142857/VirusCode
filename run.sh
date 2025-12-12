#!/bin/bash

# Activate virtual environment and run the virus
cd "$(dirname "$0")"

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and clear cache to avoid wheel cache issues
echo "Upgrading pip..."
pip install --upgrade pip --no-cache-dir

# Install requirements with cache disabled to avoid file not found errors
echo "Installing requirements..."
pip install --no-cache-dir -r requirements.txt

# Verify critical packages are installed
echo "Verifying critical packages..."
python3 -c "import cryptography; print('✓ cryptography installed')" 2>/dev/null || {
    echo "⚠️  cryptography not found, installing separately..."
    pip install --no-cache-dir cryptography
}

echo "✅ Setup complete!"

# Run the virus core
python3 virus_core.py

