#!/bin/bash
# Deploy playback server components to music server (FitPC3)
# Updates playback scripts while preserving config and data

set -e

SERVER="oscar@fitpc3"
REMOTE_PATH="/home/oscar/daily-greeting"

echo "Deploying playback server to $SERVER:$REMOTE_PATH"

# Use rsync with include filters to sync only playback files
rsync -av --delete \
  --include='playback/' \
  --include='playback/**' \
  --exclude='*' \
  ./ "$SERVER:$REMOTE_PATH/"

echo "Deployment complete!"
echo "Remember to run playback/setup_playback.sh on the server if this is first deployment"
