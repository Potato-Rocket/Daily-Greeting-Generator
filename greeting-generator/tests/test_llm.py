#!/usr/bin/env python3
"""
Test Pipeline Runner

Loads previously fetched data (weather, literature, album) from a stored data file
and runs only the synthesis and composition stages. Useful for testing prompt changes
without hitting external APIs.

Usage:
    python test_pipeline.py [YYYY-MM-DD]

If date is omitted, uses today's date.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.config import load_config, apply_config
from generator.io_manager import IOManager, setup_logging
from generator.pipeline import synthesize_materials


def main():
    """Run the test pipeline using stored data."""

    # Parse date argument if provided
    date_str = sys.argv[1] if len(sys.argv) > 1 else None

    # Setup basic logging first
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    base_dir = Path(__file__).parent.parent

    # Load configuration overrides
    config = load_config(base_dir)
    apply_config(config)

    # Initialize I/O manager and full logging
    io_manager = IOManager(base_dir)
    setup_logging(io_manager, logging.DEBUG)

    logging.info("=== TEST PIPELINE START ===")
    if date_str:
        logging.info(f"Loading data from {date_str}")

    # Use context manager to ensure pipeline file is closed
    with io_manager:
        try:
            # Load stored data
            data = io_manager.load_data_file(date_str)
            if not data:
                logging.error("Test pipeline aborted: Could not load data file")
                return

            # Extract stored data
            weather = data.get('weather')
            literature = data.get('literature')
            album = data.get('album')

            if not weather or not literature or not album:
                logging.error("Test pipeline aborted: Incomplete data (missing weather, literature, or album)")
                return

            # Stage 5: Synthesis layer
            logging.info("Stage 5: Synthesis")
            greeting = synthesize_materials(io_manager, weather, literature, album)

            if greeting:
                io_manager.save_greeting(greeting)
                io_manager.update_data_file(greeting=greeting)
                logging.info("Greeting generated and saved")

            logging.info("=== TEST PIPELINE COMPLETE ===")

        except Exception as e:
            logging.exception(f"Test pipeline error: {e}")
            raise


if __name__ == "__main__":
    main()
