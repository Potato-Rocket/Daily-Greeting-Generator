"""
Pipeline Logic for Daily Greeting Generator

Multi-stage LLM pipeline:
1. Literature validation (with retry logic)
2. Album selection (from 5 random albums)
3. Album art analysis (default check + vision description)
4. Synthesis layer (extract themes, mood, sensory anchors)
5. Composition layer (transform to wake-up message)
"""

import re
import math
import base64
import random
import logging

from .data_sources import get_random_literature, get_navidrome_albums, get_album_details
from .formatters import format_literature, format_albums, format_album, format_weather, format_jabberwocky
from .llm import send_ollama_request, send_ollama_image_request
from .jabberwocky import generate_words

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


def select_words(io_manager, literature, greeting_length=MESSAGE_MEAN_LEN):
    """
    Generate jabberwocky words and use LLM to select the most interesting subset.

    Args:
        io_manager: IOManager instance for output
        literature: Literature excerpt dict (used as source for word generation), or None
        generate_count: Number of target words in the greeting
    """
    # Check if literature is available for word generation
    if not literature:
        logging.warning("No literature available, skipping jabberwocky word generation")
        return
    
    logging.info("Starting jabberwocky word selection")

    select_count = int(0.5 * (greeting_length ** 0.5))
    generate_count = select_count * 3

    # Generate candidate words
    generated_words = generate_words(io_manager, generate_count)

    if not generated_words:
        logging.warning("Jabberwocky word generation failed, skipping word selection")
        return

    logging.info(f"Generated {len(generated_words)} candidate words")

    # Format words as numbered list for LLM
    formatted_words = format_jabberwocky(generated_words)
    formatted_literature = format_literature(literature)

    selection_prompt = f"""Select {select_count} of the {generate_count} randomly generated, Jabberwocky-style nonsense words. Try to make an interesting and varied selection which most reflects the writing style of the following literature excerpt.

{formatted_literature}
    
Avoid nonsense words which might sound too close to real words.

{formatted_words}

Repond with your chosen words only and no other text. Transcribe exactly."""

    io_manager.print_section("WORD SELECTION - PROMPT", selection_prompt)
    selection_response = send_ollama_request(selection_prompt)

    if selection_response is None:
        logging.error("Ollama request failed during word selection")
        return

    io_manager.print_section("WORD SELECTION - RESPONSE", selection_response)

    # Parse response: extract words (one per line, strip whitespace)
    selected_words = []
    for line in selection_response.strip().split('\n'):
        word = line.strip()
        if word and word in generated_words:
            selected_words.append(word)
        elif word:
            logging.debug(f"Ignoring invalid word from LLM: '{word}'")

    if not selected_words:
        logging.warning("Failed to parse word selection, using random fallback")
        selected_words = random.sample(generated_words, min(select_count, len(generated_words)))
        logging.debug(f"Random fallback selected {len(selected_words)} words")
    else:
        logging.debug(f"Selected {len(selected_words)} words: {', '.join(selected_words)}")

    literature['jabberwocky'] = selected_words


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

    art_prompt = """Provide a detailed, factual description of the provided album cover art. Use three to five bullet points.

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


def calculate_greeting_length():
    """
    Calculate target greeting length using lognormal distribution.

    Uses module-level MESSAGE_MEAN_LEN, MESSAGE_Q1_LEN, and MESSAGE_MIN_LEN
    to generate natural length variation while enforcing minimum.

    Returns:
        int: Target greeting length in words
    """
    mu = math.log(MESSAGE_MEAN_LEN)
    sigma = math.log(MESSAGE_MEAN_LEN/MESSAGE_Q1_LEN)
    logging.debug(f"Lognormal with mu={mu:.2f}, sigma={sigma:.2f}")

    length = int(random.lognormvariate(mu, sigma))
    if length < MESSAGE_MIN_LEN:
        logging.debug(f"Clamping length of {length} to {MESSAGE_MIN_LEN}")
        length = MESSAGE_MIN_LEN

    logging.debug(f"Length target is {length} words")
    return length


def synthesize_materials(io_manager, weather, literature, album, greeting_length=MESSAGE_MEAN_LEN):
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
    # Calculate target greeting length
    length = greeting_length
    length_bounds = [length - random.randint(1, 10), length + random.randint(1, 10)]
    logging.debug(f"Length bounds are {length_bounds[0]} to {length_bounds[1]} words")

    logging.info("Starting synthesis layer")

    synthesis_prompt = "Compose a motivating morning wake-up call."

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
            synthesis_prompt += "\nThe listener can see and feel the current weather."
            
        if literature:
            synthesis_prompt += "\nThe listener has NOT read the literature excerpt."
            
        if album:
            synthesis_prompt += "\nThe listener has NOT seen or heard the album yet."

        synthesis_prompt += "\n\n"

        if literature:
            synthesis_prompt += "Consider whether the literature excerpt has any distinctive structural or stylistic elements. "

        synthesis_prompt += """Avoid references that are too specific or out of context.

Weave these elements into a unified vision. Avoid scattered fragments."""

    if literature['jabberwocky']:
        synthesis_prompt += f"""

Furthermore, please use the integrate the following Jabberwocky-style nonsense words with the greeting, as naturally as possible.

{format_jabberwocky(literature['jabberwocky'])}"""

    synthesis_prompt += f"""
    
Maintain an impersonal voice.

Please keep the final greeting between {length_bounds[0]} and {length_bounds[1]} words in length. Respond in the following format exactly:

REASONING:"""
    
    if album or literature or weather:
        synthesis_prompt += "\n(A few paragraphs pondering the sources)"

    synthesis_prompt += """
(A few paragraphs planning the greeting)

GREETING:
(The final generated greeting)"""
    
    io_manager.print_section("SYNTHESIS - PROMPT", synthesis_prompt)
    greeting = send_ollama_request(synthesis_prompt)

    if greeting is None:
        logging.error("Ollama request failed during synthesis")
        return None

    io_manager.print_section("SYNTHESIS - RESPONSE", greeting)

    # Extract only the GREETING section from the response
    if "GREETING:" in greeting.upper():
        # Find the GREETING: marker and extract everything after it
        greeting_start = greeting.upper().find("GREETING:")
        final_greeting = greeting[greeting_start + len("GREETING:"):].strip()
        # Remove surrounding quotes if present
        if final_greeting.startswith('"') and final_greeting.endswith('"'):
            final_greeting = final_greeting[1:-1]
        logging.debug(f"Extracted greeting ({len(final_greeting.split())} words)")
    else:
        logging.warning("Could not find GREETING: marker in synthesis response, using full response")
        final_greeting = greeting.strip()

    logging.info("Synthesis layer complete")

    return final_greeting
