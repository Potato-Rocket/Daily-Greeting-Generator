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
6. Composition layer
7. TTS synthesis
"""

import json
import logging
from pathlib import Path

from generator.config import load_config, apply_config
from generator.io_manager import IOManager, setup_logging
from generator.data_sources import get_weather_data
from generator.pipeline import (
    validate_literature,
    select_album,
    analyze_album_art,
    synthesize_materials
)
from generator.llm import unload_all_models
from generator.tts import synthesize_greeting, send_to_playback_server


def main():
    """Run the full pipeline iteration."""

    # Setup basic logging first (will be reconfigured after IOManager init)
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    base_dir = Path(__file__).parent

    # Load configuration overrides
    config = load_config(base_dir)
    apply_config(config)

    # Initialize I/O manager with context manager to ensure pipeline file is opened/closed
    with IOManager(base_dir) as io_manager:
        setup_logging(io_manager)

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
            io_manager.update_data_file(literature=literature)

            # Stage 3: Album selection
            logging.info("Stage 3: Album selection")
            album = select_album(io_manager, literature)

            if not album:
                logging.warning("Album selection unavailable, proceeding without music data")

            # Stage 4: Album art analysis
            logging.info("Stage 4: Album art analysis")
            analyze_album_art(io_manager, album)
            io_manager.update_data_file(album=album)

            # Stage 5: Synthesis layer
            logging.info("Stage 5: Synthesis")
            greeting = synthesize_materials(io_manager, weather, literature, album)

            if not greeting:
                logging.error("Pipeline aborted: Synthesis failed (Ollama unavailable)")
                return

            io_manager.save_greeting(greeting)
            io_manager.update_data_file(greeting=greeting)
            logging.info("Greeting generated and saved")

            # Stage 6: TTS synthesis
            logging.info("Stage 6: TTS synthesis")
            result = synthesize_greeting(greeting, io_manager)

            if result:
                logging.info("Audio saved successfully")

                logging.info("Stage 7: Sending to playback server")
                send_success = send_to_playback_server(result, album)

                if not send_success:
                    logging.warning("Failed to send audio to playback server")
            else:
                logging.error("TTS synthesis failed, greeting text saved but no audio generated")

            # Clean up Ollama
            unload_all_models()
            logging.info("=== PIPELINE COMPLETE ===")

        except Exception as e:
            logging.exception(f"Pipeline error: {e}")
            raise


if __name__ == "__main__":
    main()
