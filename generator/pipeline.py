"""
Pipeline Logic for Daily Greeting Generator

Multi-stage LLM pipeline:
1. Literature validation (with retry logic)
2. Album selection (from 5 random albums)
3. Album art analysis (default check + vision description)
4. Composition layer (transform to wake-up message)
"""

import re
import base64
import math
import random
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .config import Config
from .data_sources import *
from .llm import send_ollama_request, Temperature

_template_dir = Path(__file__).parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(_template_dir),
    lstrip_blocks=True,
    keep_trailing_newline=False,
)


def _render(template_name, **kwargs):
    return _jinja_env.get_template(template_name).render(**kwargs).strip()


def validate_literature(io_manager, max_attempts=5):
    """
    Fetch and validate literature excerpt using LLM evaluation.

    Args:
        io_manager: IOManager instance for output
        max_attempts: Maximum number of attempts to find suitable literature

    Returns:
        dict: Validated literature data with 'title', 'author', 'excerpt' keys, or None if max attempts reached
    """
    logging.info("Starting literature validation")

    for attempt in range(1, max_attempts + 1):
        logging.debug(f"Literature validation attempt {attempt}/{max_attempts}")
        literature, text = get_random_literature()

        if not literature:
            logging.warning(f"Literature fetch failed on attempt {attempt}, retrying")
            continue

        literature_prompt = _render("literature_validation.j2", literature=literature)

        io_manager.print_section("LITERATURE VALIDATION - PROMPT", literature_prompt)
        evaluation = send_ollama_request(literature_prompt, Temperature.LOW)

        if evaluation is None:
            logging.error("Ollama request failed during literature validation")
            return None

        io_manager.print_section("LITERATURE VALIDATION - RESPONSE", evaluation)

        if "VERDICT: YES" in evaluation.upper():
            logging.info(f"Suitable literature found (attempts: {attempt})")
            io_manager.save_book(text)
            return literature
        else:
            logging.debug(f"Literature rejected by LLM on attempt {attempt}")

    logging.error(f"Literature validation failed after {max_attempts} attempts")
    return None


def select_album(io_manager, literature):
    """
    Fetch 5 random albums and select the best pairing with literature using LLM.

    Args:
        io_manager: IOManager instance for output
        literature: Literature excerpt dict with info, or None if literature unavailable

    Returns:
        dict: Selected album with 'id', 'name', 'artist', 'year', 'genres' keys, or None if Navidrome unavailable
    """
    logging.info("Starting album selection")

    albums = get_navidrome_albums(count=5)

    # Graceful degradation: proceed without album data
    if not albums:
        logging.warning("Navidrome unavailable, skipping album selection")
        return None

    album_prompt = _render(
        "album_selection.j2",
        albums=albums,
        literature=literature,
    )

    io_manager.print_section("ALBUM SELECTION - PROMPT", album_prompt)
    evaluation = send_ollama_request(album_prompt, Temperature.LOW)

    if evaluation is None:
        logging.error("Ollama request failed during album selection")
        return None

    io_manager.print_section("ALBUM SELECTION - RESPONSE", evaluation)

    # Parse LLM verdict using regex
    match = re.search(r'VERDICT:\s*(\d+)', evaluation)
    if match:
        selection = int(match.group(1)) - 1
        if selection < 0 or selection >= len(albums):
            logging.warning(f"Album selection #{selection + 1} out of range, using random fallback")
            selection = random.randint(0, 4)
        else:
            logging.info(f"Selected album #{selection + 1}: '{albums[selection]['name']}' by {albums[selection]['artist']}")
    else:
        logging.warning("Failed to parse album selection, using random fallback")
        selection = random.randint(0, 4)
        logging.debug(f"Random fallback selected album #{selection + 1}")

    return albums[selection]


def analyze_album_art(io_manager, album):
    """
    Fetch album details and analyze cover art if available using vision model.
    Modifies album dict in place with 'songs' list and 'coverart' description.

    Args:
        io_manager: IOManager instance for output and file saving
        album: Album dict (modified in place with 'songs' and 'coverart' fields), or None if no album
    """
    logging.info("Starting album art analysis")

    # Graceful degradation: skip if no album selected
    if not album:
        logging.warning("No album available, skipping art analysis")
        return

    album_details = get_album_details(album['id'])

    # Graceful degradation: handle Navidrome failures during detail fetch
    if not album_details:
        logging.warning("Album details unavailable, skipping art analysis")
        album['songs'] = None
        album['coverart'] = None
        return

    album['songs'] = album_details.get('songs')

    if not album_details['coverart']:
        logging.warning("No cover art available, skipping analysis")
        album['coverart'] = None
        return

    # Save cover art to file
    coverart_bytes = base64.b64decode(album_details['coverart'])
    io_manager.save_coverart(coverart_bytes)

    art_prompt = _render("album_art.j2")

    io_manager.print_section("ALBUM ART - ANALYSIS PROMPT", art_prompt)
    analysis = send_ollama_request(art_prompt, image_base64=album_details['coverart'])

    if analysis is None:
        logging.error("Cover art analysis failed")
        album['coverart'] = None
    else:
        io_manager.print_section("ALBUM ART - ANALYSIS RESPONSE", analysis)
        album['coverart'] = analysis
        logging.info("Album art analysis complete")


def _choose_greeting_length():
    cfg = Config.instance().greeting
    mu = math.log(cfg.mean_length)
    sigma = math.log(cfg.mean_length) - math.log(cfg.q1_length)
    return max(int(random.lognormvariate(mu, sigma)), cfg.min_length)


def generate_greeting(io_manager, weather, literature, album):
    """
    Run synthesis layer to compose final greeting from inputs.

    Args:
        io_manager: IOManager instance for output
        weather: Weather data dict
        literature: Literature excerpt dict with info
        album: Album dict with details

    Returns:
        str: Final daily greeting message
    """
    logging.info("Starting synthesis layer")

    greeting_length = _choose_greeting_length()
    logging.debug(f"Chosen target greeting length: {greeting_length} words")

    synthesis_prompt = _render(
        "synthesis.j2",
        weather=weather,
        literature=literature,
        album=album,
        greeting_length=greeting_length,
    )
    
    io_manager.print_section("SYNTHESIS - PROMPT", synthesis_prompt)
    response = send_ollama_request(synthesis_prompt, Temperature.HIGH)

    if response is None:
        logging.error("Ollama request failed during synthesis")
        return None

    io_manager.print_section("SYNTHESIS - RESPONSE", response)

    # Parse REASONING and GREETING sections
    greeting_match = re.search(r'GREETING:\s*(.*)', response, re.DOTALL | re.IGNORECASE)

    if not greeting_match:
        logging.warning("Failed to parse GREETING from synthesis response, using full response")
        final_greeting = response.strip()
    else:
        final_greeting = greeting_match.group(1).strip()

    # Remove surrounding quotes if present
    if final_greeting.startswith('"') and final_greeting.endswith('"'):
        final_greeting = final_greeting[1:-1]

    logging.debug(f"Generated {len(final_greeting.split())} words")
    logging.info("Synthesis layer complete")

    return final_greeting
