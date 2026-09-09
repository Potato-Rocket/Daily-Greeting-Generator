"""
Test Pipeline Runner

Loads previously fetched data (weather, literature, album) from a stored data file
and runs only the synthesis and composition stages. Useful for testing prompt changes
without hitting external APIs.

Usage:
    python tests/test_llm.py [date]

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
from generator.pipeline import generate_greeting


def main():
    """Run the test pipeline using stored data."""

    date_arg = sys.argv[1] if len(sys.argv) > 1 else None

    setup_logging()
    Config.load()

    paths, error = get_paths(date_arg or Mode.LAST)
    if error:
        print(f"Error: {error}")
        sys.exit(1)

    io_manager = IOManager(paths)

    logging.info("=== TEST PIPELINE START ===")
    logging.info(f"Loading data from {io_manager.paths.date_str}")

    try:
        # Load stored data
        data = io_manager.load_data_file()
        if not data:
            logging.error("Test pipeline aborted: Could not load data file")
            return

        # Extract stored data
        weather = data.get('weather')
        literature = data.get('literature')
        album = data.get('album')

        if not weather or not literature or not album:
            logging.error("Test pipeline degraded: Incomplete data (missing weather, literature, or album)")

        # Stage 5: Synthesis layer
        logging.info("Stage 5: Synthesis")
        greeting = generate_greeting(io_manager, weather, literature, album)

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
