"""
LLM Interface for Daily Greeting Generator

Handles communication with Ollama API for text generation and vision tasks.
"""

import requests
import logging


# Ollama API configuration
OLLAMA_BASE = "http://192.168.1.134:11434"
MODEL = "mistral:7b"
# MODEL = "llama3.2:3b"  # Alternative text model
IMAGE_MODEL = "gemma3:4b"
# IMAGE_MODEL = "llama3.2-vision:11b"  # Alternative vision model


def send_ollama_request(prompt):
    """
    Send a prompt to the Ollama API and return the response text.

    Args:
        prompt: The text prompt to send

    Returns:
        str: LLM response text, or None on failure
    """
    logging.info(f"Sending request to Ollama ({MODEL})")

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_BASE + "/api/generate", json=payload)

        if response.status_code != 200:
            logging.error(f"Ollama API returned status {response.status_code}")
            return None

        result = response.json()['response']
        logging.debug(f"Received response ({len(result)} chars)")
        logging.info("Ollama request completed successfully")

        return result

    except Exception as e:
        logging.exception(f"Ollama request error: {e}")
        return None


def send_ollama_image_request(prompt, image_base64):
    """
    Send a prompt with an image to the Ollama API and return the response text.

    Args:
        prompt: The text prompt to send
        image_base64: Base64-encoded image string

    Returns:
        str: Vision model response text, or None on failure
    """
    logging.info(f"Sending vision request to Ollama ({IMAGE_MODEL})")

    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_BASE + "/api/generate", json=payload)

        if response.status_code != 200:
            logging.error(f"Ollama vision API returned status {response.status_code}")
            return None

        result = response.json()['response']
        logging.debug(f"Received vision response ({len(result)} chars)")
        logging.info("Ollama vision request completed successfully")

        return result

    except Exception as e:
        logging.exception(f"Ollama vision request error: {e}")
        return None
