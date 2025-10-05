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
CONFIG_FILE = BASE_DIR / "config.ini"
SCHEDULE_FILE = DATA_DIR / ".playback_schedule"

# Default configuration
DEFAULT_PORT = 7000
DEFAULT_LAT = 0.0
DEFAULT_LON = 0.0
DEFAULT_OFFSET = 0

app = Flask(__name__)

# Setup logging using Flask's app logger
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Configure Flask's logger to write to our log file
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)


def load_config():
    """
    Load playback configuration from INI file.

    Returns:
        dict: Configuration with 'port', 'lat', 'lon', 'offset_minutes' keys
    """
    config = {
        'port': DEFAULT_PORT,
        'lat': DEFAULT_LAT,
        'lon': DEFAULT_LON,
        'offset_minutes': DEFAULT_OFFSET
    }

    if not CONFIG_FILE.exists():
        app.logger.warning(f"Config file not found: {CONFIG_FILE}, using defaults")
        return config

    try:
        parser = configparser.ConfigParser()
        parser.read(CONFIG_FILE)

        # Load server configuration
        if 'server' in parser:
            config['port'] = parser['server'].getint('port', DEFAULT_PORT)

        # Load location configuration
        if 'location' in parser:
            config['lat'] = parser['location'].getfloat('lat', DEFAULT_LAT)
            config['lon'] = parser['location'].getfloat('lon', DEFAULT_LON)

        # Load playback configuration
        if 'playback' in parser:
            config['offset_minutes'] = parser['playback'].getint('offset_minutes', DEFAULT_OFFSET)

        app.logger.debug(f"Loaded config: {config}")
        return config

    except Exception as e:
        app.logger.exception(f"Error loading config: {e}, using defaults")
        return config


def get_sunrise_time(config):
    """
    Calculate today's sunrise time with configured offset, then sves to a file for the checker script.

    Since greetings are generated at 2am, "today" refers to the upcoming
    sunrise later this morning.

    Args:
        config: Configuration dict with lat, lon, offset_minutes
    """
    try:
        location = LocationInfo(latitude=config['lat'], longitude=config['lon'])

        # calculate sunrise time
        s = sun(location.observer, date=datetime.now())
        app.logger.info(f"Calculating sunrise for today ({datetime.now().strftime('%Y-%m-%d')})")

        # get the sunrise for today plus offset
        sunrise = s['sunrise'] + timedelta(minutes=config['offset_minutes'])

        # if the sunrise for today has already passed
        if sunrise.time() < datetime.now().time().replace(tzinfo=None):
            app.logger.info(f"Sunrise has already happened today!")
            time = datetime.now() + timedelta(days=1)
            app.logger.info(f"Calculating sunrise for tomorrow ({time.strftime('%Y-%m-%d')})")
            s = sun(location.observer, time)

        app.logger.info(f"Sunrise time calculated: {sunrise.strftime('%Y-%m-%d %H:%M')} UTC")

    except Exception as e:
        app.logger.exception(f"Error calculating sunrise: {e}")
        return
    
    try:
        sunrise_epoch = int(sunrise.timestamp())

        with open(SCHEDULE_FILE, 'w') as f:
            f.write(f"{sunrise_epoch}\n")

        app.logger.debug(f"Sunrise time saved: {sunrise_epoch}")

    except Exception as e:
        app.logger.error(f"Error saving sunrise time: {e}")


@app.route('/receive', methods=['POST'])
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
            app.logger.warning("Empty request body")
            return jsonify({
                'status': 'error',
                'message': 'No audio data received'
            }), 400

        # Ensure directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Save audio file (overwrites previous)
        with open(GREETING_FILE, 'wb') as f:
            f.write(audio_data)

        app.logger.info("Greeting received and saved")

        # Calculate sunrise time and save schedule
        config = load_config()
        get_sunrise_time(config)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        app.logger.exception(f"Error receiving greeting: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    config = load_config()
    port = config['port']
    app.logger.info(f"Starting Flask greeting receiver on port {port}")
    app.run(host='0.0.0.0', port=port, use_reloader=False)
