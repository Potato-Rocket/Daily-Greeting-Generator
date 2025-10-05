#!/bin/bash
# Deploy playback server components to music server (FitPC3)
# Updates playback scripts while preserving config and data

set -e

SERVER="oscar@fitpc3-music-server"
REMOTE_PATH="/home/oscar/daily-greeting"

echo "Deploying playback server to $SERVER:$REMOTE_PATH"

# Create remote directory if it doesn't exist
ssh "$SERVER" "mkdir -p $REMOTE_PATH"

# Copy files using scp
echo "Copying files..."
scp check_sunrise.sh \
    setup_playback.sh \
    greeting.service \
    playback_config.ini.example \
    receive_greeting.py \
    requirements.txt \
    "$SERVER:$REMOTE_PATH/"

echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "1. SSH to server: ssh $SERVER"
echo "2. cd $REMOTE_PATH"
echo "3. Run setup (first time only): ./setup_playback.sh"
echo "4. Edit config: vim playback_config.ini"
