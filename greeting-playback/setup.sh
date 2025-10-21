#!/bin/bash
# Setup script for playback server (FitPC3 music server)
# Run this once after first deployment of playback components

set -e

# Determine script directory for relative paths
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TRIGGERS_DIR="/etc/triggerhappy/triggers.d"

echo "Setting up Daily Greeting playback server..."
echo "Base directory: $BASE_DIR"

# Create required directories
echo "Creating directories..."
mkdir -p "$BASE_DIR/data"

# Copy config template if config doesn't exist
if [ ! -f "$BASE_DIR/config.ini" ]; then
    echo "Creating config.ini from template..."
    cp "$BASE_DIR/config.ini.example" "$BASE_DIR/config.ini"
    echo ""
    echo "IMPORTANT: Edit $BASE_DIR/config.ini with your settings:"
    echo "   - Location coordinates (lat/lon)"
    echo "   - Sunrise offset in minutes"
    echo ""
else
    echo "config.ini already exists, skipping..."
fi

# Create virtual environment if it doesn't exist
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

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$BASE_DIR/receive_greeting.py"
chmod +x "$BASE_DIR/check_sunrise.sh"

# Install systemd service (needs to be updated with absolute paths)
echo ""
echo "Installing systemd service..."
# Create temporary service file with correct paths
sed "s|BASEDIR_PLACEHOLDER|$BASE_DIR|g" "$BASE_DIR/greeting.service" > /tmp/greeting.service.tmp
sudo cp /tmp/greeting.service.tmp /etc/systemd/system/greeting.service
rm /tmp/greeting.service.tmp
sudo systemctl daemon-reload
sudo systemctl enable greeting.service
sudo systemctl start greeting.service

echo ""
echo "Checking service status..."
sudo systemctl status greeting.service --no-pager

# Setup cron job for sunrise checker
echo ""
echo "Setting up cron job for sunrise checker..."
CRON_LINE="*/5 * * * * $BASE_DIR/check_sunrise.sh"

# Check if cron job already exists
if sudo crontab -l 2>/dev/null | grep -q "check_sunrise.sh"; then
    echo "Cron job already exists, skipping..."
else
    # Add cron job
    (sudo crontab -l 2>/dev/null; echo "$CRON_LINE") | sudo crontab -

    # Verify it was actually added
    if sudo crontab -l 2>/dev/null | grep -q "check_sunrise.sh"; then
        echo "Cron job added (runs every 5 minutes)"
    else
        echo "ERROR: Failed to add cron job. Please add manually:"
        echo "  echo '$CRON_LINE' | sudo crontab -"
        exit 1
    fi
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit $BASE_DIR/config.ini with your coordinates and offset"
echo "2. Test Flask API: curl -X POST http://localhost:7000/receive -d @test.wav -H 'Content-Type: audio/wav'"
echo "3. Send test greeting from generation server"
echo "4. Test mpv MPRIS on system bus:"
echo "   DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket mpv --no-video --playlist=data/song_urls.txt &"
echo "   busctl list | grep mpv  # Should show org.mpris.MediaPlayer2.mpv"
echo "5. Monitor logs:"
echo "   tail -f $BASE_DIR/data/receiver.log  # Flask API"
echo "   tail -f $BASE_DIR/data/checker.log   # Sunrise checker"
echo ""
echo "Service commands:"
echo "   sudo systemctl status greeting.service"
echo "   sudo systemctl restart greeting.service"
echo "   sudo systemctl stop greeting.service"
