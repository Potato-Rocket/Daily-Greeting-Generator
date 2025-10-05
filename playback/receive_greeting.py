#!/usr/bin/env python3
"""
Flask API for receiving daily greeting audio files.

Receives WAV files from the generation server and stores them in dated files.
Also calculates sunrise time and playback window for the checker script.
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
SCRIPT_DIR = Path(__file__).parent.parent
GREETING_DIR = SCRIPT_DIR / "data/greetings"
LOG_FILE = SCRIPT_DIR / "data/receiver.log"
CONFIG_FILE = SCRIPT_DIR / "playback_config.ini"
SCHEDULE_FILE = SCRIPT_DIR / "data/.playback_schedule"
PORT = 7000

# Default configuration
DEFAULT_LAT = 42.27
DEFAULT_LON = -71.81
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
        # Calculate for tomorrow since greeting is generated at 2am for next morning
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        s = sun(location.observer, date=tomorrow)
        sunrise = s['sunrise'] + timedelta(minutes=config['offset_minutes'])

        logging.info(f"Sunrise time calculated: {sunrise.strftime('%Y-%m-%d %H:%M')}")
        return sunrise

    except Exception as e:
        logging.exception(f"Error calculating sunrise: {e}")
        return None


def save_sunrise_time(sunrise_time):
    """
    Save sunrise epoch time to file for checker script.

    Also resets the played flag by deleting it.

    Args:
        sunrise_time: Sunrise datetime
    """
    try:
        sunrise_epoch = int(sunrise_time.timestamp())

        SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULE_FILE, 'w') as f:
            f.write(f"{sunrise_epoch}\n")

        logging.debug(f"Sunrise time saved: {sunrise_epoch}")

        # Reset played flag for new greeting
        played_flag = SCRIPT_DIR / "data/.played"
        if played_flag.exists():
            played_flag.unlink()
            logging.debug("Played flag reset")

    except Exception as e:
        logging.error(f"Error saving sunrise time: {e}")


@app.route('/greeting', methods=['POST'])
def receive_greeting():
    """
    Receive greeting audio file from generation server.

    Expects WAV file in request body with Content-Type: audio/wav
    Saves to data/greetings/greeting_YYYY-MM-DD.wav

    Returns:
        JSON response with status and filename
    """
    try:
        # Validate content type
        if request.content_type != 'audio/wav':
            logging.warning(f"Invalid content type: {request.content_type}")
            return jsonify({
                'status': 'error',
                'message': 'Content-Type must be audio/wav'
            }), 400

        # Get audio data
        audio_data = request.data
        if not audio_data:
            logging.warning("Empty request body")
            return jsonify({
                'status': 'error',
                'message': 'No audio data received'
            }), 400

        # Create filename with current date
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"greeting_{date_str}.wav"
        filepath = GREETING_DIR / filename

        # Ensure directory exists
        GREETING_DIR.mkdir(parents=True, exist_ok=True)

        # Save audio file
        with open(filepath, 'wb') as f:
            f.write(audio_data)

        file_size = len(audio_data) / 1024  # KB
        logging.info(f"Greeting received and saved: {filename} ({file_size:.1f} KB)")

        # Calculate sunrise time and save schedule
        config = load_config()
        sunrise = calculate_sunrise_time(config)
        if sunrise:
            save_sunrise_time(sunrise)

        return jsonify({
            'status': 'success',
            'filename': filename,
            'size_kb': round(file_size, 1)
        }), 200

    except Exception as e:
        logging.exception(f"Error receiving greeting: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    logging.info(f"Starting Flask greeting receiver on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)
