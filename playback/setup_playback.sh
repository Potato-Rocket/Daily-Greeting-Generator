#!/bin/bash
# Setup script for playback server (FitPC3 music server)
# Run this once after first deployment of playback components

set -e

echo "Setting up Daily Greeting playback server..."

# Create required directories
echo "Creating directories..."
mkdir -p /home/oscar/daily-greeting/data/greetings
mkdir -p /home/oscar/daily-greeting/playback

# Copy config template if config doesn't exist
if [ ! -f /home/oscar/daily-greeting/playback_config.ini ]; then
    echo "Creating playback_config.ini from template..."
    cp /home/oscar/daily-greeting/playback/playback_config.ini.example /home/oscar/daily-greeting/playback_config.ini
    echo ""
    echo "IMPORTANT: Edit /home/oscar/daily-greeting/playback_config.ini with your settings:"
    echo "   - Location coordinates (lat/lon)"
    echo "   - Sunrise offset in minutes"
    echo ""
else
    echo "playback_config.ini already exists, skipping..."
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install --user flask astral

# Make scripts executable
echo "Making scripts executable..."
chmod +x /home/oscar/daily-greeting/playback/receive_greeting.py
chmod +x /home/oscar/daily-greeting/playback/check_sunrise.py

# Install systemd service
echo ""
echo "Installing systemd service..."
sudo cp /home/oscar/daily-greeting/playback/greeting.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable greeting.service
sudo systemctl start greeting.service

echo ""
echo "Checking service status..."
sudo systemctl status greeting.service --no-pager

# Setup cron job for sunrise checker
echo ""
echo "Setting up cron job for sunrise checker..."
CRON_LINE="*/5 * * * * /usr/bin/python3 /home/oscar/daily-greeting/playback/check_sunrise.py"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "check_sunrise.py"; then
    echo "Cron job already exists, skipping..."
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job added (runs every 5 minutes)"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /home/oscar/daily-greeting/playback_config.ini with your coordinates and offset"
echo "2. Test Flask API: curl http://localhost:7000/health"
echo "3. Send test greeting from generation server"
echo "4. Monitor logs: tail -f /home/oscar/daily-greeting/data/log.txt"
echo ""
echo "Service commands:"
echo "   sudo systemctl status greeting.service"
echo "   sudo systemctl restart greeting.service"
echo "   sudo systemctl stop greeting.service"
