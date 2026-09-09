#!/usr/bin/env python3
"""
Test Album Art Analysis

Loads album data from a previously stored data file and runs the vision
model analysis. Useful for testing image analysis prompts without re-running
the full pipeline.

Usage:
    python tests/test_image.py [date]

    date  Date to load data from (YYYY-MM-DD). Defaults to the most recently
          generated greeting.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from generator.config import Config
from generator.io_manager import IOManager, setup_logging, get_paths, Mode
from generator.pipeline import analyze_album_art


def main():
    """Run album art analysis test using stored album data."""

    date_arg = sys.argv[1] if len(sys.argv) > 1 else None

    setup_logging()
    Config.load()

    paths, error = get_paths(date_arg or Mode.LAST)
    if error:
        print(f"Error: {error}")
        sys.exit(1)

    io_manager = IOManager(paths)

    logging.info("=== ALBUM ART ANALYSIS TEST START ===")
    logging.info(f"Loading data from {io_manager.paths.date_str}")

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
