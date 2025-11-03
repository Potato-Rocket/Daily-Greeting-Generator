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
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from astral import LocationInfo
from astral.sun import sun

# Configuration - paths relative to script location
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
GREETING_FILE = DATA_DIR / "greeting.wav"
SONG_URLS_FILE = DATA_DIR / "song_urls.txt"
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
    Calculate today's sunrise time with configured offset, then saves to a file for the checker script.

    Since greetings are generated at 2am, "today" refers to the upcoming
    sunrise later this morning.

    Args:
        config: Configuration dict with lat, lon, offset_minutes
    """
    try:
        location = LocationInfo(latitude=config['lat'], longitude=config['lon'])

        # Get current time in UTC (to match astral's UTC output)
        now_utc = datetime.now(timezone.utc)

        # Calculate sunrise time for today
        s = sun(location.observer, date=now_utc)
        app.logger.info(f"Calculating sunrise for today ({now_utc.strftime('%Y-%m-%d')})")

        # Get the sunrise for today plus offset
        sunrise = s['sunrise'] + timedelta(minutes=config['offset_minutes'])

        # Compare full datetime objects (both are now UTC-aware)
        if sunrise < now_utc:
            app.logger.info(f"Sunrise has already passed today at {sunrise.strftime('%H:%M:%S')} UTC")
            # Calculate tomorrow's sunrise
            tomorrow = now_utc + timedelta(days=1)
            app.logger.info(f"Calculating sunrise for tomorrow ({tomorrow.strftime('%Y-%m-%d')})")
            s = sun(location.observer, date=tomorrow)
            sunrise = s['sunrise'] + timedelta(minutes=config['offset_minutes'])

        app.logger.info(f"Sunrise time calculated: {sunrise.strftime('%Y-%m-%d %H:%M:%S')} UTC")

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


@app.route('/greeting', methods=['POST'])
def receive_greeting():
    """
    Receive greeting audio file and song URLs from generation server.

    Saves audio to data/greeting.wav (overwrites previous)
    Saves song URLs to data/song_urls.txt (overwrites previous)
    Calculates and saves tomorrow's sunrise time

    Returns:
        JSON response with status
    """
    try:
        # Ensure directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Get audio file from multipart form
        if 'audio' not in request.files:
            app.logger.warning("No audio file in request")
            return jsonify({
                'status': 'error',
                'message': 'No audio file received'
            }), 400

        audio_file = request.files['audio']

        # Save audio file (overwrites previous)
        audio_file.save(GREETING_FILE)
        app.logger.info("Greeting audio received and saved")

        # Get and save song URLs if provided
        song_urls = request.form.get('song_urls', '')
        if song_urls:
            with open(SONG_URLS_FILE, 'w') as f:
                f.write(song_urls)

            num_songs = len(song_urls.strip().split('\n'))
            app.logger.info(f"Saved {num_songs} song URLs")
        else:
            app.logger.warning("No song URLs provided")

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
