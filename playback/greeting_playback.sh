#!/bin/bash
# Sunrise checker script for daily greeting playback
# Runs every 5 minutes via cron
# Plays greeting if current time is past sunrise and hasn't been played yet

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

SCHEDULE_FILE="$BASE_DIR/data/.playback_schedule"
GREETING_FILE="$BASE_DIR/data/greeting.wav"
LOG_FILE="$BASE_DIR/data/checker.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if schedule file exists
if [ ! -f "$SCHEDULE_FILE" ]; then
    exit 0
fi

# Read sunrise epoch time from schedule file
SUNRISE_EPOCH=$(cat "$SCHEDULE_FILE")
if [ -z "$SUNRISE_EPOCH" ]; then
    log "ERROR: Empty schedule file"
    exit 1
fi

# Get current epoch time
NOW_EPOCH=$(date +%s)

# Check if current time is past sunrise
if [ "$NOW_EPOCH" -lt "$SUNRISE_EPOCH" ]; then
    exit 0
fi

log "INFO: Past sunrise time, playing greeting"

# Check if greeting file exists
if [ ! -f "$GREETING_FILE" ]; then
    log "ERROR: No greeting file found"
    exit 1
fi

log "INFO: Playing greeting"

# Play greeting with aplay
if aplay "$GREETING_FILE" >> "$LOG_FILE" 2>&1; then
    log "INFO: Playback completed successfully"
    # Mark as played by adding 1 day (86400 seconds) to sunrise time
    NEW_EPOCH=$((SUNRISE_EPOCH + 86400))
    echo "$NEW_EPOCH" > "$SCHEDULE_FILE"
else
    log "ERROR: Playback failed"
    exit 1
fi
