#!/bin/bash
# Deploy Daily Greeting to remote server
# Updates code files while preserving config and data

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

echo "Deploying generator to $SERVER:$REMOTE_PATH"

# Create remote directory if it doesn't exist
ssh "$SERVER" "mkdir -p $REMOTE_PATH/generator"

# Copy files using scp
echo "Copying files..."
scp main.py \
    environment.yml \
    setup.sh \
    config.ini.example \
    "$SERVER:$REMOTE_PATH"
scp generator/*.py "$SERVER:$REMOTE_PATH/generator"

echo "Deployment complete!"
echo ""
echo "To complete setup:"
echo "    ssh $SERVER  # SSH to server"
echo "    cd $REMOTE_PATH  # enter program directory"
echo "    ./setup_generator.sh  # run setup script (first time only)"
echo "    vim config.ini  # edit config file"
