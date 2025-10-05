#!/usr/bin/env python3
"""
Flask API for receiving daily greeting audio files.

Receives WAV files from the generation server and stores to data/greeting.wav.
Calculates tomorrow's sunrise time for the checker script.
Runs as a systemd service on the music playback server.
"""

import logging
import configparser
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from astral import LocationInfo
from astral.sun import sun

# Configuration - paths relative to script location
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
GREETING_FILE = DATA_DIR / "greeting.wav"
LOG_FILE = DATA_DIR / "receiver.log"
CONFIG_FILE = BASE_DIR / "playback_config.ini"
SCHEDULE_FILE = DATA_DIR / ".playback_schedule"
PORT = 7000

# Default configuration
DEFAULT_LAT = 0.0
DEFAULT_LON = 0.0
DEFAULT_OFFSET = 0

# Setup logging
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

app = Flask(__name__)


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


def calculate_sunrise_time(config):
    """
    Calculate tomorrow's sunrise time.

    Args:
        config: Configuration dict with lat, lon, offset_minutes

    Returns:
        datetime: Sunrise time (with offset), or None on error
    """
    try:
        location = LocationInfo(latitude=config['lat'], longitude=config['lon'])
        # Calculate for today
        s = sun(location.observer, date=datetime.now())
        sunrise = s['sunrise'] + timedelta(minutes=config['offset_minutes'])

        logging.info(f"Sunrise time calculated: {sunrise.strftime('%Y-%m-%d %H:%M')}")
        return sunrise

    except Exception as e:
        logging.exception(f"Error calculating sunrise: {e}")
        return None


def save_sunrise_time(sunrise_time):
    """
    Save sunrise epoch time to file for checker script.

    Args:
        sunrise_time: Sunrise datetime
    """
    try:
        sunrise_epoch = int(sunrise_time.timestamp())

        with open(SCHEDULE_FILE, 'w') as f:
            f.write(f"{sunrise_epoch}\n")

        logging.debug(f"Sunrise time saved: {sunrise_epoch}")

    except Exception as e:
        logging.error(f"Error saving sunrise time: {e}")


@app.route('/greeting', methods=['POST'])
def receive_greeting():
    """
    Receive greeting audio file from generation server.

    Saves to data/greeting.wav (overwrites previous)
    Calculates and saves tomorrow's sunrise time

    Returns:
        JSON response with status
    """
    try:
        # Get audio data
        audio_data = request.data
        if not audio_data:
            logging.warning("Empty request body")
            return jsonify({
                'status': 'error',
                'message': 'No audio data received'
            }), 400

        # Ensure directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Save audio file (overwrites previous)
        with open(GREETING_FILE, 'wb') as f:
            f.write(audio_data)

        logging.info("Greeting received and saved")

        # Calculate sunrise time and save schedule
        config = load_config()
        sunrise = calculate_sunrise_time(config)
        if sunrise:
            save_sunrise_time(sunrise)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        logging.exception(f"Error receiving greeting: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    logging.info(f"Starting Flask greeting receiver on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)
