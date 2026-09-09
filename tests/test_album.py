"""
Test Album Details Fetcher

Loads album ID from previously stored data file and fetches detailed information
including tracklist and cover art from Navidrome. Useful for testing album
details fetching and cover art analysis without re-running the full pipeline.

Usage:
    python tests/test_album.py [date]

    date  Date to load data from (YYYY-MM-DD). Defaults to the most recently
          generated greeting.
"""

import sys
import json
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
from generator.data_sources import get_album_details


def main():
    """Run album details fetch test using stored album ID."""

    date_arg = sys.argv[1] if len(sys.argv) > 1 else None

    setup_logging()
    Config.load()

    paths, error = get_paths(date_arg or Mode.LAST)
    if error:
        print(f"Error: {error}")
        sys.exit(1)

    io_manager = IOManager(paths)

    logging.info("=== ALBUM DETAILS TEST START ===")
    logging.info(f"Loading data from {io_manager.paths.date_str}")

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
