"""
Configuration Module for Daily Greeting Generator

Loads settings from config.yaml with typed defaults via dataclasses.
Env vars (GREETING_BASE_DIR, GREETING_CONFIG_DIR) set paths; everything
else lives in config.yaml and is re-read each generation.
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional

import yaml


@dataclass
class WeatherConfig:
    lat: float = 0.0
    lon: float = 0.0
    user_agent: str = "DailyGreeting/1.0"


@dataclass
class OllamaConfig:
    host: str = "http://localhost:11434"
    model: str = "mistral:7b"
    image_model: str = "llava:7b"


@dataclass
class NavidromeConfig:
    base_url: str = "http://localhost:4533"
    username: str = "username"
    password: str = "password"
    client_name: str = "DailyGreeting"


@dataclass
class LiteratureConfig:
    length: int = 600
    padding: int = 2000


@dataclass
class PiperConfig:
    voice: str = "random"
    length_scale: float = 1.15
    noise_scale: float = 0.667
    noise_w_scale: float = 0.8


@dataclass
class Config:
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    navidrome: NavidromeConfig = field(default_factory=NavidromeConfig)
    literature: LiteratureConfig = field(default_factory=LiteratureConfig)
    piper: PiperConfig = field(default_factory=PiperConfig)

    _instance: ClassVar[Optional["Config"]] = None

    @classmethod
    def load(cls) -> "Config":
        """Load config from YAML, creating/updating the singleton."""
        config_dir = Path(os.environ.get("GREETING_CONFIG_DIR", "/config/"))
        config_path = config_dir / "config.yaml"

        if not config_path.exists():
            logging.info("No config file found, using defaults")
            cls._instance = cls()
            return cls._instance

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        cls._instance = cls(
            weather=WeatherConfig(**data.get("weather", {})),
            ollama=OllamaConfig(**data.get("ollama", {})),
            navidrome=NavidromeConfig(**data.get("navidrome", {})),
            literature=LiteratureConfig(**data.get("literature", {})),
            piper=PiperConfig(**data.get("piper", {})),
        )
        logging.debug(f"Loaded config from {config_path}")
        return cls._instance

    @classmethod
    def instance(cls) -> "Config":
        """Get the current config singleton. Loads defaults if not yet loaded."""
        if cls._instance is None:
            cls.load()
        return cls._instance
