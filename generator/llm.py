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


def send_ollama_request(prompt, temp=Temperature.MEDIUM, image_base64=None):
    """
    Send a prompt to Ollama and return the response text.

    Args:
        prompt: The text prompt to send
        temp: Temperature setting for generation
        image_base64: Optional base64-encoded image string for vision requests

    Returns:
        str: LLM response text, or None on failure
    """
    model = Config.instance().ollama.multimodal_model if image_base64 else Config.instance().ollama.text_model
    request_type = "vision " if image_base64 else ""

    start_time = time.time()
    logging.info(f"Sending {request_type}request to Ollama ({model})")

    try:
        kwargs = {
            "model": model,
            "prompt": prompt,
            "think": REASONING,
            "options": {"temperature": temp.value},
        }
        if image_base64:
            kwargs["images"] = [image_base64]

        response = _get_client().generate(**kwargs)
        api_time = time.time() - start_time
        logging.debug(f"Ollama {request_type}API call took {api_time:.2f}s")

        result = response.response
        logging.debug(f"Received {request_type}response ({len(result)} chars)")
        logging.info(f"Ollama {request_type}request completed successfully")

        return result

    except ollama.ResponseError as e:
        logging.error(f"Ollama API error (status {e.status_code}): {e.error}")
        return None
    except Exception as e:
        logging.exception(f"Ollama request error: {e}")
        return None
