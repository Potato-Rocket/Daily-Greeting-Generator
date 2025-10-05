#!/bin/bash
# Deploy Daily Greeting to remote server
# Updates code files while preserving config and data

set -e

SERVER="oscar@media-center"
REMOTE_PATH="/home/oscar/daily-greeting"

echo "Deploying Daily Greeting to $SERVER:$REMOTE_PATH"

# Use rsync with include filters to sync only specified files
rsync -av --delete \
  --include='main.py' \
  --include='setup_generator.sh' \
  --include='generator_config.ini.example' \
  --include='generator/' \
  --include='generator/**' \
  --exclude='*' \
  ./ "$SERVER:$REMOTE_PATH/"

echo "Deployment complete!"
echo "Remember to run setup.sh on the server if this is first deployment"
