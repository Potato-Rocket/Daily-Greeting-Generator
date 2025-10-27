#!/usr/bin/env python3
"""
Test Album Art Analysis

Loads album data from a previously stored data file and runs the vision
model analysis. Useful for testing image analysis prompts without re-running
the full pipeline.

Usage:
    python test_image.py
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.config import load_config, apply_config
from generator.io_manager import IOManager, setup_logging
from generator.pipeline import analyze_album_art

# Date to load data from
DATE = "2025-10-26"


def main():
    """Run album art analysis test using stored album data."""

    # Setup basic logging first
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    base_dir = Path(__file__).parent.parent

    # Load configuration overrides
    config = load_config(base_dir)
    apply_config(config)

    # Initialize I/O manager and full logging
    io_manager = IOManager(base_dir, date_str=DATE)
    setup_logging(io_manager, logging.DEBUG)

    logging.info("=== ALBUM ART ANALYSIS TEST START ===")
    logging.info(f"Loading data from {io_manager.date_str}")

    try:
        # Load stored data
        data = io_manager.load_data_file()
        if not data:
            logging.error("Test aborted: Could not load data file")
            return

        # Extract album data
        album = data.get('album')
        if not album:
            logging.error("Test aborted: No album found in data file")
            return

        logging.info(f"Found album: {album.get('name')} by {album.get('artist')}")

        # Run album art analysis
        analyze_album_art(io_manager, album)

        logging.info("=== ALBUM ART ANALYSIS TEST COMPLETE ===")

    except Exception as e:
        logging.exception(f"Album art test error: {e}")
        raise


if __name__ == "__main__":
    main()
