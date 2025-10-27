#!/usr/bin/env python3
"""
Test TTS Runner

Loads previously generated greeting text from stored data file and synthesizes
to audio using Coqui XTTS-v2. Useful for testing TTS changes without re-running
the full pipeline.

Usage:
    python test_tts.py
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.config import load_config, apply_config
from generator.io_manager import IOManager, setup_logging
from generator.tts import synthesize_greeting

# Date to load data from
DATE = "2025-10-26"


def main():
    """Run TTS synthesis test using stored greeting text."""

    # Setup basic logging first
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    base_dir = Path(__file__).parent.parent

    # Load configuration overrides
    config = load_config(base_dir)
    apply_config(config)

    # Initialize I/O manager and full logging
    io_manager = IOManager(base_dir, date_str=DATE)
    setup_logging(io_manager, logging.DEBUG)

    logging.info("=== TTS TEST START ===")
    logging.info(f"Loading data from {io_manager.date_str}")

    try:
        # Load stored data
        data = io_manager.load_data_file()
        if not data:
            logging.error("TTS test aborted: Could not load data file")
            return

        # Extract greeting text
        greeting = data.get('greeting')
        if not greeting:
            logging.error("TTS test aborted: No greeting found in data file")
            return

        logging.info(f"Loaded greeting ({len(greeting)} chars)")

        # Synthesize to audio
        result = synthesize_greeting(greeting, io_manager)

        if result:
            logging.info(f"Audio saved successfully")
            # Update data file with audio path
            io_manager.update_data_file(audio_path=str(result))
        else:
            logging.error("TTS synthesis failed")

        logging.info("=== TTS TEST COMPLETE ===")

    except Exception as e:
        logging.exception(f"TTS test error: {e}")
        raise


if __name__ == "__main__":
    main()
