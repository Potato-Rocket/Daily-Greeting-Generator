#!/bin/bash
# Sunrise checker script for daily greeting playback
# Runs every 5 minutes via cron
# Plays greeting if current time is past sunrise and hasn't been played yet

# Determine script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

SCHEDULE_FILE="$BASE_DIR/data/.playback_schedule"
PLAYED_FLAG="$BASE_DIR/data/.played"
GREETING_DIR="$BASE_DIR/data/greetings"
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

# Check if already played
if [ -f "$PLAYED_FLAG" ]; then
    exit 0
fi

# Check if current time is past sunrise
if [ "$NOW_EPOCH" -lt "$SUNRISE_EPOCH" ]; then
    exit 0
fi

log "INFO: Past sunrise time, playing greeting"

# Find most recent greeting file
GREETING_FILE=$(ls -t "$GREETING_DIR"/greeting_*.wav 2>/dev/null | head -n 1)

if [ -z "$GREETING_FILE" ]; then
    log "ERROR: No greeting file found"
    exit 1
fi

log "INFO: Playing $(basename "$GREETING_FILE")"

# Play greeting with aplay
if aplay "$GREETING_FILE" >> "$LOG_FILE" 2>&1; then
    log "INFO: Playback completed successfully"
    # Mark as played
    touch "$PLAYED_FLAG"
else
    log "ERROR: Playback failed"
    exit 1
fi
