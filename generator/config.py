"""
Configuration Module for Daily Greeting Generator

Loads settings from config.ini file with fallback to module defaults.
"""

import configparser
import logging
from pathlib import Path


def load_config():
    """
    Load configuration from config.ini file.

    Reads config.ini from project root and returns all settings as a
    flat dictionary with dot-notation keys (e.g., "weather.lat").

    Returns:
        dict: Configuration values as {"section.key": "value"}, or empty dict if no config file
    """
    config_path = Path(__file__).parent.parent / "config.ini"

    if not config_path.exists():
        return {}

    config = configparser.ConfigParser()
    config.read(config_path)

    # Flatten config to dot-notation dictionary
    config_dict = {}
    for section in config.sections():
        for key, value in config[section].items():
            config_dict[f"{section}.{key}"] = value

    logging.debug(f"Loaded {len(config_dict)} config values from {config_path}")
    return config_dict


def apply_config(config_dict):
    """
    Apply configuration values to module constants.

    Updates constants in data_sources, llm, tts, and io_manager modules
    based on loaded configuration.

    Args:
        config_dict: Dictionary from load_config() with dot-notation keys
    """
    if not config_dict:
        logging.info("No config file found, using defaults")
        return

    from . import data_sources, llm, tts, io_manager

    # Weather configuration
    if "weather.lat" in config_dict:
        data_sources.LAT = float(config_dict["weather.lat"])
    if "weather.lon" in config_dict:
        data_sources.LON = float(config_dict["weather.lon"])
    if "weather.user_agent" in config_dict:
        data_sources.USER_AGENT = config_dict["weather.user_agent"]

    # Ollama configuration
    if "ollama.base_url" in config_dict:
        llm.OLLAMA_BASE = config_dict["ollama.base_url"]
    if "ollama.model" in config_dict:
        llm.MODEL = config_dict["ollama.model"]
    if "ollama.image_model" in config_dict:
        llm.IMAGE_MODEL = config_dict["ollama.image_model"]

    # Navidrome configuration
    if "navidrome.base_url" in config_dict:
        data_sources.NAVIDROME_BASE = config_dict["navidrome.base_url"]
    if "navidrome.username" in config_dict:
        data_sources.NAVIDROME_USER = config_dict["navidrome.username"]
    if "navidrome.password" in config_dict:
        data_sources.NAVIDROME_PASS = config_dict["navidrome.password"]
    if "navidrome.client_name" in config_dict:
        data_sources.NAVIDROME_CLIENT = config_dict["navidrome.client_name"]

    # TTS configuration
    if "tts.model_path" in config_dict:
        tts.MODEL_PATH = config_dict["tts.model_path"]
    if "tts.length_scale" in config_dict:
        tts.LENGTH_SCALE = float(config_dict["tts.length_scale"])

    # I/O configuration
    if "io.base_dir" in config_dict:
        io_manager.BASE_DIR = config_dict["io.base_dir"]

    logging.info(f"Applied {len(config_dict)} configuration overrides")
