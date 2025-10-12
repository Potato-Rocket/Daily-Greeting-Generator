#!/usr/bin/env python3
"""
Test Album Details Fetcher

Loads album ID from previously stored data file and fetches detailed information
including tracklist and cover art from Navidrome. Useful for testing album
details fetching and cover art analysis without re-running the full pipeline.

Usage:
    python test_album.py [YYYY-MM-DD]

If date is omitted, uses today's date.
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.config import load_config, apply_config
from generator.io_manager import IOManager, setup_logging
from generator.data_sources import get_album_details


def main():
    """Run album details fetch test using stored album ID."""

    # Setup basic logging first
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    base_dir = Path(__file__).parent.parent

    # Load configuration overrides
    config = load_config(base_dir)
    apply_config(config)

    # Initialize I/O manager with context manager to ensure pipeline file is opened/closed
    with IOManager(base_dir) as io_manager:
        setup_logging(io_manager, logging.DEBUG)

        logging.info("=== ALBUM DETAILS TEST START ===")
        logging.info(f"Loading data from {io_manager.date_str}")

        try:
            # Load stored data
            data = io_manager.load_data_file()
            if not data:
                logging.error("Album test aborted: Could not load data file")
                return

            # Extract album data
            album = data.get('album')
            if not album:
                logging.error("Album test aborted: No album found in data file")
                return

            album_id = album.get('id')
            if not album_id:
                logging.error("Album test aborted: No album ID found in album data")
                return

            logging.info(f"Found album: {album.get('name')} by {album.get('artist')}")

            # Fetch album details
            album_details = get_album_details(album_id)

            if not album_details:
                logging.error("Album details fetch failed")
                return

            # Display results as JSON
            print(json.dumps(album_details, indent=2))

            logging.info("=== ALBUM DETAILS TEST COMPLETE ===")

        except Exception as e:
            logging.exception(f"Album test error: {e}")
            raise


if __name__ == "__main__":
    main()
