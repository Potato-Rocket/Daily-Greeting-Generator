SERVER="oscar@fitpc3-music-server"
REMOTE_PATH="/home/oscar/notifications"

echo "Deploying notification script to $SERVER:$REMOTE_PATH"

# Create remote directory if it doesn't exist
ssh "$SERVER" "mkdir -p $REMOTE_PATH"

# Copy files using scp
echo "Copying files..."
scp play_chime.py "$SERVER:$REMOTE_PATH/"
scp -r resources "$SERVER:$REMOTE_PATH/"

echo "Deployment complete!"
