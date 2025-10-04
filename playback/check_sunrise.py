#!/usr/bin/env python3
"""
Sunrise checker script for daily greeting playback.

Runs every 5 minutes via cron. Checks if current time is within the sunrise
window (configurable offset), and plays the most recent greeting if it hasn't
been played today.
"""

import os
import sys
import logging
import subprocess
import configparser
from pathlib import Path
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun

# Configuration paths
CONFIG_FILE = Path("/home/oscar/daily-greeting/playback_config.ini")
GREETING_DIR = Path("/home/oscar/daily-greeting/data/greetings")
LOG_FILE = Path("./data/log.txt")
PLAYED_FLAG = Path("/home/oscar/daily-greeting/data/.played_today")

# Default configuration
DEFAULT_LAT = 42.27
DEFAULT_LON = -71.81
DEFAULT_OFFSET = 0  # minutes after sunrise


def setup_logging():
    """Configure logging to file and console."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )


def load_config():
    """
    Load playback configuration from INI file.

    Returns:
        dict: Configuration with 'lat', 'lon', 'offset_minutes' keys
    """
    config = {
        'lat': DEFAULT_LAT,
        'lon': DEFAULT_LON,
        'offset_minutes': DEFAULT_OFFSET
    }

    if not CONFIG_FILE.exists():
        logging.warning(f"Config file not found: {CONFIG_FILE}, using defaults")
        return config

    try:
        parser = configparser.ConfigParser()
        parser.read(CONFIG_FILE)

        if 'playback' in parser:
            config['lat'] = parser['playback'].getfloat('lat', DEFAULT_LAT)
            config['lon'] = parser['playback'].getfloat('lon', DEFAULT_LON)
            config['offset_minutes'] = parser['playback'].getint('offset_minutes', DEFAULT_OFFSET)

        logging.debug(f"Loaded config: {config}")
        return config

    except Exception as e:
        logging.exception(f"Error loading config: {e}, using defaults")
        return config


def get_sunrise_time(lat, lon):
    """
    Calculate today's sunrise time for given coordinates.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        datetime: Sunrise time in local timezone
    """
    location = LocationInfo(latitude=lat, longitude=lon)
    s = sun(location.observer, date=datetime.now().date())
    sunrise = s['sunrise']
    logging.debug(f"Sunrise calculated: {sunrise.strftime('%H:%M:%S')}")
    return sunrise


def is_within_window(sunrise, offset_minutes):
    """
    Check if current time is within the playback window.

    Args:
        sunrise: Sunrise datetime
        offset_minutes: Minutes after sunrise to allow playback

    Returns:
        bool: True if within window
    """
    now = datetime.now(sunrise.tzinfo)
    window_start = sunrise
    window_end = sunrise + timedelta(minutes=offset_minutes)

    logging.debug(f"Current time: {now.strftime('%H:%M:%S')}")
    logging.debug(f"Window: {window_start.strftime('%H:%M:%S')} - {window_end.strftime('%H:%M:%S')}")

    return window_start <= now <= window_end


def already_played_today():
    """
    Check if greeting has already been played today.

    Uses a flag file that stores the last played date.

    Returns:
        bool: True if already played today
    """
    if not PLAYED_FLAG.exists():
        return False

    try:
        with open(PLAYED_FLAG, 'r') as f:
            last_played = f.read().strip()

        today = datetime.now().strftime("%Y-%m-%d")
        return last_played == today

    except Exception as e:
        logging.warning(f"Error reading played flag: {e}")
        return False


def mark_as_played():
    """Mark greeting as played for today."""
    try:
        PLAYED_FLAG.parent.mkdir(parents=True, exist_ok=True)
        with open(PLAYED_FLAG, 'w') as f:
            f.write(datetime.now().strftime("%Y-%m-%d"))
        logging.debug("Marked as played for today")
    except Exception as e:
        logging.error(f"Error writing played flag: {e}")


def get_most_recent_greeting():
    """
    Find the most recent greeting file.

    Returns:
        Path: Path to most recent greeting WAV file, or None if not found
    """
    if not GREETING_DIR.exists():
        logging.warning(f"Greeting directory not found: {GREETING_DIR}")
        return None

    wav_files = list(GREETING_DIR.glob("greeting_*.wav"))
    if not wav_files:
        logging.warning("No greeting files found")
        return None

    # Sort by modification time, most recent first
    wav_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    most_recent = wav_files[0]

    logging.debug(f"Most recent greeting: {most_recent.name}")
    return most_recent


def play_greeting(filepath):
    """
    Play greeting audio file using mpv.

    Args:
        filepath: Path to WAV file

    Returns:
        bool: True if playback succeeded
    """
    try:
        logging.info(f"Playing greeting: {filepath.name}")
        result = subprocess.run(
            ['mpv', '--no-video', str(filepath)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            logging.info("Playback completed successfully")
            return True
        else:
            logging.error(f"mpv failed with return code {result.returncode}")
            logging.error(f"mpv stderr: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logging.error("mpv playback timed out")
        return False
    except FileNotFoundError:
        logging.error("mpv not found - is it installed?")
        return False
    except Exception as e:
        logging.exception(f"Error playing greeting: {e}")
        return False


def main():
    """Main sunrise checker logic."""
    setup_logging()

    # Load configuration
    config = load_config()

    # Check if already played today
    if already_played_today():
        logging.debug("Greeting already played today, skipping")
        return

    # Calculate sunrise time
    try:
        sunrise = get_sunrise_time(config['lat'], config['lon'])
    except Exception as e:
        logging.exception(f"Error calculating sunrise: {e}")
        return

    # Check if within playback window
    if not is_within_window(sunrise, config['offset_minutes']):
        logging.debug("Not within playback window, skipping")
        return

    logging.info("Within sunrise playback window")

    # Find most recent greeting
    greeting_file = get_most_recent_greeting()
    if not greeting_file:
        logging.error("No greeting file available for playback")
        return

    # Play greeting
    if play_greeting(greeting_file):
        mark_as_played()
    else:
        logging.error("Playback failed, will retry on next check")


if __name__ == '__main__':
    main()
