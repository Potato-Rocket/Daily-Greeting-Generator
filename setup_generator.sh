#!/bin/bash
# Initial setup script for Daily Greeting on server
# Run this once after first deployment

set -e

echo "Setting up Daily Greeting..."

# Create required directories
echo "Creating directories..."
mkdir -p data models

# Copy config template if config doesn't exist
if [ ! -f config.ini ]; then
    echo "Creating config.ini from template..."
    cp generator_config.ini.example config.ini
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

# Download Piper TTS models
echo ""
echo "Downloading Piper TTS models..."

# Ryan (high quality)
if [ ! -f models/en_US-ryan-high.onnx ]; then
    echo "Downloading en_US-ryan-high..."
    curl -L -o models/en_US-ryan-high.onnx \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx"
    curl -L -o models/en_US-ryan-high.onnx.json \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json"
else
    echo "en_US-ryan-high already exists, skipping..."
fi

# Lessac (high quality)
if [ ! -f models/en_US-lessac-high.onnx ]; then
    echo "Downloading en_US-lessac-high..."
    curl -L -o models/en_US-lessac-high.onnx \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx"
    curl -L -o models/en_US-lessac-high.onnx.json \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx.json"
else
    echo "en_US-lessac-high already exists, skipping..."
fi

# Create virtual environment if it doesn't exist
echo ""
if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Determine script directory for absolute paths in cron
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Setup cron job for daily execution at 2am
echo ""
echo "Setting up cron job for daily execution..."
CRON_LINE="0 2 * * * cd $SCRIPT_DIR && $SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py"

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
echo "2. Test with: $SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py"
echo "3. Monitor execution: tail -f $SCRIPT_DIR/data/\$(date +%Y-%m-%d)/log_\$(date +%Y-%m-%d).txt"
