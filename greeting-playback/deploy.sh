#!/bin/bash
# Deploy playback server components to music server
# Updates playback scripts while preserving config and data

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

REMOTE_PATH="~/daily-greeting"

echo "Deploying playback server to $SERVER:$REMOTE_PATH"

# Create remote directory if it doesn't exist
ssh "$SERVER" "mkdir -p $REMOTE_PATH"

# Copy files using scp
echo "Copying files..."
scp check_sunrise.sh \
    test_sound.sh \
    receive_greeting.py \
    requirements.txt \
    setup.sh \
    greeting.service \
    config.ini.example \
    "$SERVER:$REMOTE_PATH/"

echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "    ssh $SERVER  # SSH to server"
echo "    cd $REMOTE_PATH  # enter program directory"
echo "    ./setup.sh  # execute the setup script (first time only)"
echo "    vim config.ini  # edit the config file"
