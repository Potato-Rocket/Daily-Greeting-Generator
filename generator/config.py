"""
Configuration Module for Daily Greeting Generator

Three-layer config: code defaults → config.yaml → env vars (highest priority).
Env vars control infrastructure and secrets; config.yaml controls behavioral tuning.
See .env.example for the full list of supported env vars.
"""

import os
import yaml
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional


@dataclass
class WeatherConfig:
    lat: float = 0.0
    lon: float = 0.0
    user_agent: str = "DailyGreeting/1.0"


@dataclass
class OllamaConfig:
    host: str = "http://localhost:11434"
    text_model: str = "mistral:7b"
    multimodal_model: str = "llava:7b"


@dataclass
class NavidromeConfig:
    base_url: str = "http://localhost:4533"
    username: str = "username"
    password: str = "password"
    client_name: str = "DailyGreeting"


@dataclass
class GreetingConfig:
    min_length: int = 50
    q1_length: int = 100
    mean_length: int = 140


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
    greeting: GreetingConfig = field(default_factory=GreetingConfig)
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
            instance = cls()
            cls._apply_env_overrides(instance)
            cls._instance = instance
            return cls._instance

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        instance = cls(
            weather=WeatherConfig(**data.get("weather", {})),
            ollama=OllamaConfig(**data.get("ollama", {})),
            navidrome=NavidromeConfig(**data.get("navidrome", {})),
            greeting=GreetingConfig(**data.get("greeting", {})),
            literature=LiteratureConfig(**data.get("literature", {})),
            piper=PiperConfig(**data.get("piper", {})),
        )
        cls._apply_env_overrides(instance)
        logging.debug(f"Loaded config from {config_path}")
        cls._instance = instance
        return cls._instance

    # Maps env var name → (section, field, cast)
    _ENV_OVERRIDES = {
        "GREETING_WEATHER_LAT":    ("weather",   "lat",      float),
        "GREETING_WEATHER_LON":    ("weather",   "lon",      float),
        "GREETING_OLLAMA_HOST":    ("ollama",    "host",     str),
        "GREETING_NAVIDROME_URL":  ("navidrome", "base_url", str),
        "GREETING_NAVIDROME_USER": ("navidrome", "username", str),
        "GREETING_NAVIDROME_PASS": ("navidrome", "password", str),
    }

    @classmethod
    def _apply_env_overrides(cls, instance: "Config") -> None:
        for var, (section, field_name, cast) in cls._ENV_OVERRIDES.items():
            if val := os.environ.get(var):
                setattr(getattr(instance, section), field_name, cast(val))
                logging.debug(f"Config override from env: {var}")

    @classmethod
    def instance(cls) -> "Config":
        """Get the current config singleton. Loads defaults if not yet loaded."""
        if cls._instance is None:
            cls.load()
        return cls._instance
