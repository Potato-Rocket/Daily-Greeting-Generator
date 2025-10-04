"""
Pipeline Logic for Daily Greeting Generator

Multi-stage LLM pipeline:
1. Literature validation (with retry logic)
2. Album selection (from 5 random albums)
3. Album art analysis (default check + vision description)
4. Synthesis layer (extract themes, mood, sensory anchors)
5. Composition layer (transform to wake-up message) - TODO
"""

import re
import math
import base64
import random
import logging

from .data_sources import get_random_literature, get_navidrome_albums, get_album_details
from .formatters import format_literature, format_albums, format_album, format_weather
from .llm import send_ollama_request, send_ollama_image_request

MESSAGE_MEAN_LEN = 140
MESSAGE_Q1_LEN = 100
MESSAGE_MIN_LEN = 80


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
        literature = get_random_literature()

        if not literature:
            logging.warning(f"Literature fetch failed on attempt {attempt}, retrying")
            continue

        formatted_lit = format_literature(literature)
        literature_prompt = f"""Please evaluate whether the following literary excerpt is suitable material from which to source themes, mood, imagery, metaphor, or sensory details.

{formatted_lit}

Respond in this exact format strictly:
REASONING: One sentence reasoning about the suitability of the text.
VERDICT: YES if suitable NO if not"""

        io_manager.print_section("LITERATURE VALIDATION - PROMPT", literature_prompt)
        evaluation = send_ollama_request(literature_prompt)
        io_manager.print_section("LITERATURE VALIDATION - RESPONSE", evaluation)

        if "VERDICT: YES" in evaluation.upper():
            logging.info(f"Suitable literature found (attempts: {attempt})")
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
        literature: Literature excerpt dict with info

    Returns:
        dict: Selected album with 'id', 'name', 'artist', 'year', 'genres' keys
    """
    logging.info("Starting album selection")

    albums = get_navidrome_albums(count=5)
    formatted_albums = format_albums(albums)
    formatted_literature = format_literature(literature)

    album_prompt = f"""Please select one and only one of the following albums which would pair most interestingly with the selected literary excerpt, whether by contrast or by complement.

{formatted_albums}

{formatted_literature}

Respond in this exact format strictly:
REASONING: Two or three sentences considering different options before deciding on the best choice.
VERDICT: N (N is the number of the selected album from the list above) and nothing else"""

    io_manager.print_section("ALBUM SELECTION - PROMPT", album_prompt)
    evaluation = send_ollama_request(album_prompt)
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
        album: Album dict (modified in place with 'songs' and 'coverart' fields)
    """
    logging.info("Starting album art analysis")

    album_details = get_album_details(album['id'])
    album['songs'] = album_details.get('songs')

    if not album_details['coverart']:
        logging.warning("No cover art available, skipping analysis")
        album['coverart'] = None
        return

    # Save cover art to file
    coverart_bytes = base64.b64decode(album_details['coverart'])
    io_manager.save_coverart(coverart_bytes)

    # Check if cover art is Navidrome default placeholder
    default_prompt = """Determine whether this image matches the default album cover image for Navidrome, a blue vinyl record on a blank background with the word "Navidrome" on it.

Respond with the following exact format strictly:
DESCRIPTION: One sentence description of the image.
REASONING: One sentence reasoning about whether the cover art matches not.
VERDICT: YES if it matches NO if it does not"""

    io_manager.print_section("ALBUM ART - DEFAULT CHECK PROMPT", default_prompt)
    response = send_ollama_image_request(default_prompt, album_details['coverart'])

    if response is None:
        logging.error("Cover art default check failed, skipping analysis")
        album['coverart'] = None
        return

    io_manager.print_section("ALBUM ART - DEFAULT CHECK RESPONSE", response)

    if "VERDICT: YES" in response.upper():
        logging.info("Cover art is Navidrome default placeholder, discarding")
        album['coverart'] = None
        return

    # Cover art is custom, proceed with detailed analysis
    logging.info("Cover art is custom, proceeding with analysis")

    art_prompt = """Provide a detailed description of the provided album cover art, including colors, composition, and style. Use three to five bullet points.

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


def synthesize_materials(io_manager, weather, literature, album):
    """
    Run synthesis layer to extract thematic/atmospheric elements from all sources.

    Args:
        io_manager: IOManager instance for output
        weather: Weather data dict
        literature: Literature excerpt dict with info
        album: Album dict with details

    Returns:
        str: Synthesis output with THEMES, MOOD, SENSORY ANCHORS, and SYMBOLIC ELEMENTS sections
    """
    logging.info("Starting synthesis layer")

    synthesis_prompt = f"""Analyze the following inputs and extract key thematic, atmospheric, and sensory elements. Focus on identifying abstract patterns, emotional textures, and symbolic resonances that tie the sources together.

{format_weather(weather)}

{format_literature(literature)}

{format_album(album)}

Do not create a narrative or draw conclusions, only identify raw materials.

Respond in this exact format strictly. Use markdown bullets:
THEMES: Three to five abstract themes or concepts present across the sources
MOOD: Two to four mood descriptors capturing the overall emotional texture
SENSORY ANCHORS: Three to five concrete sensory details that could serve as metaphorical touchpoints
SYMBOLIC ELEMENTS: Two to four symbols, images, or metaphors with potential for reinterpretation
DISTINCTIVE LANGUAGE: One to three notable phrases, word patterns, structuring quirks, or stylistic features (i.e. literary period/era) from the literature. Omit if generic/unremarkable."""

    io_manager.print_section("SYNTHESIS - PROMPT", synthesis_prompt)
    synthesis = send_ollama_request(synthesis_prompt)
    io_manager.print_section("SYNTHESIS - RESPONSE", synthesis)

    logging.info("Synthesis layer complete")

    return synthesis


def compose_greeting(io_manager, synthesis_output):
    """
    Run composition layer to transform synthesis into wake-up message.

    Args:
        io_manager: IOManager instance for output
        synthesis_output: Synthesis layer output string

    Returns:
        str: Final greeting message, or None if not yet implemented
    """
    mu = math.log(MESSAGE_MEAN_LEN)
    sigma = math.log(MESSAGE_MEAN_LEN/MESSAGE_Q1_LEN)
    logging.debug(f"Lognormal with mu={mu:.2f}, sigma={sigma:.2f}")
    length = int(random.lognormvariate(mu, sigma))
    if length < MESSAGE_MIN_LEN:
        logging.debug(f"Clamping length of {length} to {MESSAGE_MIN_LEN}")
        length = MESSAGE_MIN_LEN
    logging.debug(f"Length target is {length} words")
    length_bounds = [length - random.randint(1, 10), length + random.randint(1, 10)]
    logging.debug(f"Length bounds are {length_bounds[0]} to {length_bounds[1]} words")

    logging.info("Starting composition layer")
    
    greeting_prompt = f"""Compose an urgent, motivating morning wake-up call. Please base your writing strongly on the following elements:

{synthesis_output}

You have studied these synthesis materials. Now FORGET the details. What emotions, images, or messages linger? Write from this residue only, keep it abstract.
Keep it coherent, with a cohesive thread.
Be sure to maintain an impersonal voice throughout.

Please keep the response between {length_bounds[0]} and {length_bounds[1]} words in length. Respond with only the wake-up call and no other text."""
    
    io_manager.print_section("COMPOSITION - PROMPT", greeting_prompt)
    greeting = send_ollama_request(greeting_prompt)
    io_manager.print_section("COMPOSITION - RESPONSE", greeting)

    logging.info("Composition layer complete")

    return greeting
