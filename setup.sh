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
    cp config.ini.example config.ini
    echo ""
    echo "⚠️  IMPORTANT: Edit config.ini with your settings:"
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

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.ini with your settings"
echo "2. Test with: python run.py"
echo "3. Set up cron job for 2am daily execution"
