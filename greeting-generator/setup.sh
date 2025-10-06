#!/bin/bash
# Initial setup script for Daily Greeting on server
# Run this once after first deployment

set -e

# Determine script directory for relative paths
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up Daily Greeting..."
echo "Base directory: $BASE_DIR"

# Create required directories
echo "Creating directories..."
mkdir -p "$BASE_DIR/data"

# Copy config template if config doesn't exist
if [ ! -f "$BASE_DIR/config.ini" ]; then
    echo "Creating config.ini from template..."
    cp "$BASE_DIR/config.ini.example" "$BASE_DIR/config.ini"
    echo ""
    echo "IMPORTANT: Edit config.ini with your settings:"
    echo "   - Weather coordinates"
    echo "   - Ollama server URL and models"
    echo "   - Navidrome credentials"
    echo "   - TTS model path"
    echo ""
else
    echo "config.ini already exists, skipping..."
fi

# Create virtual environment if it doesn't exist\
echo ""
if [ ! -d "$BASE_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$BASE_DIR/venv"
else
    echo "Virtual environment already exists"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
source "$BASE_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$BASE_DIR/requirements.txt"

# Setup cron job for daily execution at 2am
echo ""
echo "Setting up cron job for daily execution..."
CRON_LINE="0 2 * * * cd $BASE_DIR && $BASE_DIR/venv/bin/python $BASE_DIR/main.py"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "main.py"; then
    echo "Cron job already exists, skipping..."
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job added (runs daily at 2am)"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.ini with your settings"
echo "2. Test with: $BASE_DIR/venv/bin/python $BASE_DIR/main.py"
echo "3. Monitor execution: tail -f $BASE_DIR/data/\$(date +%Y-%m-%d)/log_\$(date +%Y-%m-%d).txt"
