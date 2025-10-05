#!/bin/bash
# Deploy playback server components to music server (FitPC3)
# Updates playback scripts while preserving config and data

set -e

SERVER="oscar@fitpc3-music-server"
REMOTE_PATH="/home/oscar/daily-greeting"

echo "Deploying playback server to $SERVER:$REMOTE_PATH"

# Use rsync with include filters to sync only playback files
rsync -av --delete \
  --include='greeting_playback.sh' \
  --include='setup_playback.sh' \
  --include='greeting.service' \
  --include='playback_config.ini.example' \
  --include='receive_greeting.py' \
  --include='requirements.txt' \
  --exclude='*' \
  ./ "$SERVER:$REMOTE_PATH/"

echo "Deployment complete!"
echo "Remember to run setup_playback.sh on the server if this is first deployment"
