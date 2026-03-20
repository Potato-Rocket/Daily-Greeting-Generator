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
import random
import logging

from .data_sources import get_random_literature, get_navidrome_albums, get_album_details
from .formatters import format_literature, format_albums, format_album, format_weather
from .llm import send_ollama_request, send_ollama_image_request


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

        formatted_lit = format_literature(literature)
        literature_prompt = f"""Please evaluate whether the following literary excerpt is interesting material from which to source literary style or elements for creative writing.

{formatted_lit}

Respond in the following format exactly:
REASONING: One sentence reasoning about the suitability of the text.
VERDICT: YES if suitable NO if not"""

        io_manager.print_section("LITERATURE VALIDATION - PROMPT", literature_prompt)
        evaluation = send_ollama_request(literature_prompt)

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

    formatted_albums = format_albums(albums)

    # Adapt prompt based on literature availability
    if literature:
        formatted_literature = format_literature(literature)
        album_prompt = f"""Please select one and only one of the following albums which would pair most interestingly with the selected literary excerpt, whether by contrast or by complement.

{formatted_albums}

{formatted_literature}

Respond in the following format exactly:
REASONING: Two or three sentences considering different options before deciding on the best choice.
VERDICT: [number only] (just the number 1-5, nothing else)"""
    else:
        # Select album without literature context
        album_prompt = f"""Please select one and only one of the following albums which would be most interesting for a morning wake-up greeting.

{formatted_albums}

Respond in the following format exactly:
REASONING: Two or three sentences considering different options before deciding on the best choice.
VERDICT: [number only] (just the number 1-5, nothing else)"""

    io_manager.print_section("ALBUM SELECTION - PROMPT", album_prompt)
    evaluation = send_ollama_request(album_prompt)

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

    art_prompt = """Provide a detailed, factual description of the provided album cover art. Avoid any inference. Use three to five bullet points.

Respond with only the description, no other text. Use markdown bullet points."""

    io_manager.print_section("ALBUM ART - ANALYSIS PROMPT", art_prompt)
    analysis = send_ollama_image_request(art_prompt, album_details['coverart'])

    if analysis is None:
        logging.error("Cover art analysis failed")
        album['coverart'] = None
    else:
        io_manager.print_section("ALBUM ART - ANALYSIS RESPONSE", analysis)
        album['coverart'] = analysis
        logging.info("Album art analysis complete")


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

    synthesis_prompt = "Compose a motivating morning wake-up call for Oscar."

    # Only use this blurb
    if album or weather or literature:
        synthesis_prompt += " Write based on the following source material:"
        
        if weather:
            synthesis_prompt += f"\n\n{format_weather(weather)}"

        if literature:
            synthesis_prompt += f"\n\n{format_literature(literature)}"

        if album:
            synthesis_prompt += f"\n\n{format_album(album)}"

        synthesis_prompt += "\n"

        if weather:
            synthesis_prompt += "\nThe listener can see and feel the current weather outside. Consider what imagery these conditions might invoke."
            
        if literature:
            synthesis_prompt += "\nThe listener has NOT read the literature excerpt. Consider whether it has any distinctive structural or stylistic elements."
            
        if album:
            synthesis_prompt += "\nThe listener has NOT seen or heard the album yet. Consider the vibes it might cultivate."

        synthesis_prompt += "\n\nAvoid references that are too specific or out of context, weave these elements into a unified vision.\n\nRespond with the final greeting only and no other text, avoid enclosing quotes."
    
    io_manager.print_section("SYNTHESIS - PROMPT", synthesis_prompt)
    greeting = send_ollama_request(synthesis_prompt)

    if greeting is None:
        logging.error("Ollama request failed during synthesis")
        return None

    io_manager.print_section("SYNTHESIS - RESPONSE", greeting)

    final_greeting = greeting.strip()
    # Remove surrounding quotes if present
    if final_greeting.startswith('"') and final_greeting.endswith('"'):
        final_greeting = final_greeting[1:-1]

    logging.debug(f"Generated {len(final_greeting.split())} words")
    logging.info("Synthesis layer complete")

    return final_greeting
