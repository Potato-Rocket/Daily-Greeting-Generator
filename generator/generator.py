"""
Daily Greeting Pipeline Runner

Executes the full multi-stage LLM pipeline for generating personalized wake-up messages.
"""

import json
import logging

from .config import load_config, apply_config
from .io_manager import IOManager
from .data_sources import get_weather_data
from .pipeline import *
from .tts import synthesize_greeting


def run_pipeline():
    """
    Run the full pipeline iteration.
    Stages:
    1. Weather data fetching
    2. Literature validation
    3. Album selection
    4. Album art analysisYEs,
    5. Synthesis layer
    6. TTS synthesis
    """

    # Load configuration overrides
    config = load_config()
    apply_config(config)

    # Initialize I/O manager with context manager to ensure pipeline file is opened/closed
    with IOManager() as io_manager:
        logging.info("=== PIPELINE START ===")

        try:
            # Stage 1: Weather data
            logging.info("Stage 1: Weather data")
            weather = get_weather_data()

            if not weather:
                logging.warning("Weather data unavailable, proceeding with degraded greeting")

            logging.debug(f"Weather data: {json.dumps(weather, indent=2)}")
            io_manager.update_data_file(weather=weather)

            # Stage 2: Literature validation
            logging.info("Stage 2: Literature validation")
            literature = validate_literature(io_manager, max_attempts=5)

            if not literature:
                logging.warning("Literature unavailable after 5 attempts, proceeding without literary data")

            # Stage 3: Album selection
            logging.info("Stage 4: Album selection")
            album = select_album(io_manager, literature)

            if not album:
                logging.warning("Album selection unavailable, proceeding without music data")

            # Stage 4: Album art analysis
            logging.info("Stage 5: Album art analysis")
            analyze_album_art(io_manager, album)
            io_manager.update_data_file(album=album)

            # Stage 5: Synthesis layer
            logging.info("Stage 6: Final greeting")
            greeting = generate_greeting(io_manager, weather, literature, album)

            if not greeting:
                logging.error("Pipeline aborted: Final greeting generation failed")
                return

            io_manager.save_greeting(greeting)
            io_manager.update_data_file(greeting=greeting)
            logging.info("Greeting generated and saved")

            # Stage 6: TTS synthesis
            logging.info("Stage 7: TTS synthesis")
            synthesize_greeting(greeting, io_manager)

            logging.info("=== PIPELINE COMPLETE ===")

        except Exception as e:
            logging.exception(f"Pipeline error: {e}")
            raise
