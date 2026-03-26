"""
LLM Interface for Daily Greeting Generator

Handles communication with Ollama for text generation and vision tasks.
"""

import os
import logging
import time
import ollama

# Ollama API configuration
OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = "mistral:7b"
IMAGE_MODEL = "llava:7b"


def _get_client():
    return ollama.Client(host=OLLAMA_BASE)


def send_ollama_request(prompt):
    """
    Send a prompt to Ollama and return the response text.

    Args:
        prompt: The text prompt to send

    Returns:
        str: LLM response text, or None on failure
    """
    start_time = time.time()
    logging.info(f"Sending request to Ollama ({MODEL})")

    try:
        response = _get_client().generate(model=MODEL, prompt=prompt)
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
    logging.info(f"Sending vision request to Ollama ({IMAGE_MODEL})")

    try:
        response = _get_client().generate(
            model=IMAGE_MODEL,
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
