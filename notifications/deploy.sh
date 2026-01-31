#!/bin/bash
# Deploy notification chime component to playback server

set -e

if [ $1 ]; then
    SERVER=$1
    echo "Host is $SERVER"
else
    echo "Host must be specified!"
    echo ""
    echo "Example usage:"
    echo "    ./deploy.sh user@host"
    exit 1
fi
REMOTE_PATH="~/notifications"

echo "Deploying notification script to $SERVER:$REMOTE_PATH"

# Create remote directory if it doesn't exist
ssh "$SERVER" "mkdir -p $REMOTE_PATH"

# Copy files using scp
echo "Copying files..."
scp play_chime.py "$SERVER:$REMOTE_PATH/"
scp -r resources "$SERVER:$REMOTE_PATH/"

echo "Deployment complete!"
