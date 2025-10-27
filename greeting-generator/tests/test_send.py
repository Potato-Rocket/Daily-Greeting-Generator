#!/usr/bin/env python3
"""
Test Audio Delivery

Loads generated audio file and sends it to the playback server.
Useful for testing the audio delivery endpoint without re-running the full pipeline.

Usage:
    python test_send.py
"""

import sys
import logging
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.config import load_config, apply_config
from generator.io_manager import IOManager, setup_logging
from generator.tts import send_to_playback_server

# Date to load data from
DATE = "2025-10-26"


def main():
    """Test sending audio to playback server using stored audio file."""

    # Setup basic logging first
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    base_dir = Path(__file__).parent.parent

    # Load configuration overrides
    config = load_config(base_dir)
    apply_config(config)

    # Initialize I/O manager and full logging
    io_manager = IOManager(base_dir, date_str=DATE)
    setup_logging(io_manager, logging.DEBUG)

    logging.info("=== AUDIO DELIVERY TEST START ===")
    logging.info(f"Looking for audio from {io_manager.date_str}")

    try:
        # Check if audio file exists
        audio_path = io_manager.data_dir / f"greeting_{io_manager.date_str}.wav"

        if not audio_path.exists():
            logging.error(f"Audio delivery test aborted: Audio file not found at {audio_path}")
            logging.info("Run test_tts.py first to generate audio, or specify a date with existing audio")
            return

        logging.info(f"Found audio file: {audio_path}")
        logging.info(f"File size: {audio_path.stat().st_size} bytes")

        # Load album data from today's data file
        data_path = io_manager.data_dir / f"data_{io_manager.date_str}.json"
        if not data_path.exists():
            logging.error(f"Audio delivery test aborted: Data file not found at {data_path}")
            logging.info("Run the full pipeline first to generate data")
            return

        with open(data_path, 'r') as f:
            data = json.load(f)
            album = data.get('album', {})

        logging.info(f"Loaded album data: {album.get('name')} by {album.get('artist')}")
        logging.info(f"Album has {len(album.get('songs', []))} songs")

        # Send to playback server
        send_to_playback_server(audio_path, album)

        logging.info("=== AUDIO DELIVERY TEST COMPLETE ===")

    except Exception as e:
        logging.exception(f"Audio delivery test error: {e}")
        raise


if __name__ == "__main__":
    main()
