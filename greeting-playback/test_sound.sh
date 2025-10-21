#!/bin/bash
# Sunrise checker script for daily greeting playback
# Runs every 5 minutes via cron
# Plays greeting if current time is past sunrise and hasn't been played yet

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

GREETING_FILE="$SCRIPT_DIR/data/greeting.wav"
SONG_URLS_FILE="$SCRIPT_DIR/data/song_urls.txt"

NOTIFICATION_PATH="/home/oscar/notifications/play_chime.py"

# Ensure audio is unmuted and at 100% volume
amixer sset Headphone unmute
amixer sset Headphone 100%

# Play chime sound first, chop off trailing silence
/usr/bin/env python3 "$NOTIFICATION_PATH"

# Play greeting with aplay (use plug device for automatic channel conversion)
aplay "$GREETING_FILE"
log "INFO: Playback completed successfully"

# Play another chime after the greeting is complete
/usr/bin/env python3 "$NOTIFICATION_PATH"

# Start playing the selected album
mpc clear
cat "$SONG_URLS_FILE" | while read url; do
    mpc add "$url"
done
mpc play
