"""
LLM Interface for Daily Greeting Generator

Handles communication with Ollama API for text generation and vision tasks.
"""

import requests
import logging
import time


# Ollama API configuration
OLLAMA_BASE = "http://192.168.1.134:11434"
MODEL = "llama3.2:3b"
IMAGE_MODEL = "gemma3:4b"


def send_ollama_request(prompt):
    """
    Send a prompt to the Ollama API and return the response text.

    Args:
        prompt: The text prompt to send

    Returns:
        str: LLM response text, or None on failure
    """
    unload_model(IMAGE_MODEL)
    start_time = time.time()
    logging.info(f"Sending request to Ollama ({MODEL})")

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_BASE + "/api/generate", json=payload)
        api_time = time.time() - start_time
        logging.debug(f"Ollama API call took {api_time:.2f}s")

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
    unload_model(MODEL)

    start_time = time.time()
    logging.info(f"Sending vision request to Ollama ({IMAGE_MODEL})")

    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_BASE + "/api/generate", json=payload)
        api_time = time.time() - start_time
        logging.debug(f"Ollama vision API call took {api_time:.2f}s")

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


def unload_model(model_name):
    """
    Explicitly unload a model from Ollama to free GPU memory.

    Sends a request with keep_alive=0 to immediately unload the model
    from memory. Useful for freeing resources between pipeline runs or
    when switching between models.

    Args:
        model_name: Name of the model to unload (e.g., "mistral:7b")

    Returns:
        bool: True if unload request succeeded, False on failure
    """
    logging.info(f"Unloading model from Ollama ({model_name})")

    payload = {
        "model": model_name,
        "keep_alive": 0
    }

    try:
        response = requests.post(OLLAMA_BASE + "/api/generate", json=payload)

        if response.status_code != 200:
            logging.error(f"Ollama unload API returned status {response.status_code}")
            return False

        logging.info(f"Model unloaded successfully ({model_name})")
        return True

    except Exception as e:
        logging.exception(f"Ollama unload error: {e}")
        return False


def unload_all_models():
    """
    Unload all models used by the pipeline from Ollama.

    Calls unload_model() for both the text model and vision model to free
    all GPU memory after pipeline completion.

    Returns:
        bool: True if all models unloaded successfully, False if any failed
    """
    logging.info("Unloading all pipeline models")

    text_success = unload_model(MODEL)
    vision_success = unload_model(IMAGE_MODEL)

    if text_success and vision_success:
        logging.info("All models unloaded successfully")
        return True
    else:
        logging.warning("Some models failed to unload")
        return False
