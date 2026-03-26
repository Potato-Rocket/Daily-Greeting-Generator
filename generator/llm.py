"""
LLM Interface for Daily Greeting Generator

Handles communication with Ollama for text generation and vision tasks.
"""

import logging
import time
import ollama

from .config import Config


def _get_client():
    return ollama.Client(host=Config.instance().ollama.host)


def send_ollama_request(prompt):
    """
    Send a prompt to Ollama and return the response text.

    Args:
        prompt: The text prompt to send

    Returns:
        str: LLM response text, or None on failure
    """
    start_time = time.time()
    logging.info(f"Sending request to Ollama ({Config.instance().ollama.model})")

    try:
        response = _get_client().generate(model=Config.instance().ollama.model, prompt=prompt)
        api_time = time.time() - start_time
        logging.debug(f"Ollama API call took {api_time:.2f}s")

        result = response.response
        logging.debug(f"Received response ({len(result)} chars)")
        logging.info("Ollama request completed successfully")

        return result

    except ollama.ResponseError as e:
        logging.error(f"Ollama API error (status {e.status_code}): {e.error}")
        return None
    except Exception as e:
        logging.exception(f"Ollama request error: {e}")
        return None


def send_ollama_image_request(prompt, image_base64):
    """
    Send a prompt with an image to Ollama and return the response text.

    Args:
        prompt: The text prompt to send
        image_base64: Base64-encoded image string

    Returns:
        str: Vision model response text, or None on failure
    """
    start_time = time.time()
    logging.info(f"Sending vision request to Ollama ({Config.instance().ollama.image_model})")

    try:
        response = _get_client().generate(
            model=Config.instance().ollama.image_model,
            prompt=prompt,
            images=[image_base64],
        )
        api_time = time.time() - start_time
        logging.debug(f"Ollama vision API call took {api_time:.2f}s")

        result = response.response
        logging.debug(f"Received vision response ({len(result)} chars)")
        logging.info("Ollama vision request completed successfully")

        return result

    except ollama.ResponseError as e:
        logging.error(f"Ollama vision API error (status {e.status_code}): {e.error}")
        return None
    except Exception as e:
        logging.exception(f"Ollama vision request error: {e}")
        return None
