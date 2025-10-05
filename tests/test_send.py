#!/usr/bin/env python3
"""
Test Audio Delivery

Loads today's generated audio file and sends it to the playback server.
Useful for testing the audio delivery endpoint without re-running the full pipeline.

Usage:
    python test_send.py
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.config import load_config, apply_config
from generator.io_manager import IOManager, setup_logging
from generator.tts import send_to_playback_server


def main():
    """Test sending audio to playback server using today's audio file."""

    # Setup basic logging first
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    # Load configuration overrides
    config = load_config()
    apply_config(config)

    # Initialize I/O manager and full logging
    io_manager = IOManager()
    setup_logging(io_manager, logging.DEBUG)

    logging.info("=== AUDIO DELIVERY TEST START ===")
    logging.info(f"Looking for audio from {io_manager.date_str}")

    try:
        # Check if audio file exists
        audio_path = io_manager.run_dir / f"greeting_{io_manager.date_str}.wav"

        if not audio_path.exists():
            logging.error(f"Audio delivery test aborted: Audio file not found at {audio_path}")
            logging.info("Run test_tts.py first to generate audio, or specify a date with existing audio")
            return

        logging.info(f"Found audio file: {audio_path}")
        logging.info(f"File size: {audio_path.stat().st_size} bytes")

        # Send to playback server
        send_to_playback_server(audio_path)

        logging.info("=== AUDIO DELIVERY TEST COMPLETE ===")

    except Exception as e:
        logging.exception(f"Audio delivery test error: {e}")
        raise


if __name__ == "__main__":
    main()
