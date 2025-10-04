#!/usr/bin/env python3
"""
Flask API for receiving daily greeting audio files.

Receives WAV files from the generation server and stores them in dated files.
Runs as a systemd service on the music playback server.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify

# Configuration
GREETING_DIR = Path("/home/oscar/daily-greeting/data/greetings")
LOG_FILE = Path("/home/oscar/daily-greeting/data/log.txt")
PORT = 7000

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
