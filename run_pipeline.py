#!/usr/bin/env python3
"""
Daily Greeting Pipeline Runner

Executes the full multi-stage LLM pipeline for generating personalized wake-up messages.

Stages:
1. Weather data fetching
2. Literature validation
3. Album selection
4. Album art analysis
5. Synthesis layer
6. Composition layer (TODO)

Outputs saved to: ./tmp/{YYYY-MM-DD}/
"""

import json
import logging

from generator.io_manager import IOManager, setup_logging
from generator.data_sources import get_weather_data
from generator.pipeline import (
    validate_literature,
    select_album,
    analyze_album_art,
    synthesize_materials,
    compose_greeting,
)


def main():
    """Run the full pipeline iteration."""

    # Initialize I/O manager and logging
    io_manager = IOManager()
    setup_logging(io_manager)

    logging.info("=== PIPELINE START ===")

    # Use context manager to ensure pipeline file is closed
    with io_manager:
        try:
            # Stage 1: Weather data
            logging.info("Stage 1: Weather data")
            weather = get_weather_data()
            logging.debug(f"Weather data: {json.dumps(weather, indent=2)}")
            io_manager.update_data_file(weather=weather)

            # Stage 2: Literature validation
            logging.info("Stage 2: Literature validation")
            literature = validate_literature(io_manager, max_attempts=5)
            if not literature:
                logging.error("Pipeline aborted: No suitable literature found")
                return
            io_manager.update_data_file(literature=literature)

            # Stage 3: Album selection
            logging.info("Stage 3: Album selection")
            album = select_album(io_manager, literature)

            # Stage 4: Album art analysis
            logging.info("Stage 4: Album art analysis")
            analyze_album_art(io_manager, album)
            io_manager.update_data_file(album=album)

            # Stage 5: Synthesis layer
            logging.info("Stage 5: Synthesis")
            synthesis = synthesize_materials(io_manager, weather, literature, album)
            io_manager.update_data_file(synthesis=synthesis)

            # Stage 6: Composition layer (TODO)
            logging.info("Stage 6: Composition")
            greeting = compose_greeting(io_manager, synthesis)

            if greeting:
                io_manager.save_greeting(greeting)
                io_manager.update_data_file(greeting=greeting)
                logging.info("Greeting generated and saved")

            logging.info("=== PIPELINE COMPLETE ===")

        except Exception as e:
            logging.exception(f"Pipeline error: {e}")
            raise


if __name__ == "__main__":
    main()
