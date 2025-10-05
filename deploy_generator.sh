#!/bin/bash
# Deploy Daily Greeting to remote server
# Updates code files while preserving config and data

set -e

SERVER="oscar@media-center"
REMOTE_PATH="/home/oscar/daily-greeting"

echo "Deploying generator to $SERVER:$REMOTE_PATH"

# Create remote directory if it doesn't exist
ssh "$SERVER" "mkdir -p $REMOTE_PATH"

# Copy files using scp
echo "Copying files..."
scp main.py \
    requirements.txt \
    setup_generator.sh \
    generator_config.ini.example \
    "$SERVER:$REMOTE_PATH/"

echo "Copying generator module..."
scp -r generator "$SERVER:$REMOTE_PATH/"

echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "1. SSH to server: ssh $SERVER"
echo "2. cd $REMOTE_PATH"
echo "3. Run setup (first time only): ./setup_generator.sh"
echo "4. Edit config: nano config.ini"
