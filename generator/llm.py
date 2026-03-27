"""
LLM Interface for Daily Greeting Generator

Handles communication with Ollama for text generation and vision tasks.
"""

import logging
import time
import ollama
from enum import Enum

from .config import Config

REASONING = False


class Temperature(Enum):
    LOW = 0.7
    MEDIUM = 1.0
    HIGH = 1.5


def _get_client():
    return ollama.Client(host=Config.instance().ollama.host)


def send_ollama_request(prompt, temp=Temperature.MEDIUM):
    """
    Send a prompt to Ollama and return the response text.

    Args:
        prompt: The text prompt to send

    Returns:
        str: LLM response text, or None on failure
    """
    start_time = time.time()
    logging.info(f"Sending request to Ollama ({Config.instance().ollama.text_model})")

    try:
        response = _get_client().generate(
            model=Config.instance().ollama.multimodal_model,
            prompt=prompt,
            think=REASONING,
            options={
                "temperature": temp.value
            }
        )
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


def send_ollama_image_request(prompt, image_base64, temp=Temperature.MEDIUM):
    """
    Send a prompt with an image to Ollama and return the response text.

    Args:
        prompt: The text prompt to send
        image_base64: Base64-encoded image string

    Returns:
        str: Vision model response text, or None on failure
    """
    start_time = time.time()
    logging.info(f"Sending vision request to Ollama ({Config.instance().ollama.multimodal_model})")

    try:
        response = _get_client().generate(
            model=Config.instance().ollama.multimodal_model,
            prompt=prompt,
            images=[image_base64],
            think=REASONING,
            options={
                "temperature": temp.value
            }
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
