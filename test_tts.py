#!/usr/bin/env python3
"""
Test TTS Runner

Loads previously generated greeting text from stored data file and synthesizes
to audio using Piper TTS. Useful for testing TTS changes without re-running
the full pipeline.

Usage:
    python test_tts.py [YYYY-MM-DD]

If date is omitted, uses today's date.
"""

import sys
import logging

from generator.io_manager import IOManager, setup_logging
from generator.tts import synthesize_greeting


def main():
    """Run TTS synthesis test using stored greeting text."""

    # Initialize I/O manager and logging
    io_manager = IOManager()
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
        audio_path = io_manager.run_dir / f"greeting_{io_manager.date_str}.wav"
        result = synthesize_greeting(greeting, audio_path)

        if result:
            logging.info(f"Audio saved successfully")
            # Update data file with audio path
            io_manager.update_data_file(audio_path=str(audio_path))
        else:
            logging.error("TTS synthesis failed")

        logging.info("=== TTS TEST COMPLETE ===")

    except Exception as e:
        logging.exception(f"TTS test error: {e}")
        raise


if __name__ == "__main__":
    main()
