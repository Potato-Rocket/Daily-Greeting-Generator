"""
Text-to-Speech Module for Daily Greeting Generator

Handles audio rendering using Piper TTS.
"""

import logging
import time
import random
import wave
from piper import PiperVoice, download_voices
from piper.config import SynthesisConfig

from .config import Config

DEFAULT_VOICE = "en_US-lessac-high"


def _available_models(model_dir):
    """Return list of valid .onnx model paths that have matching .onnx.json configs."""
    return [m for m in model_dir.glob("*.onnx") if m.with_suffix(".onnx.json").exists()]


def _download_model(name, model_dir):
    """Attempt to download a Piper voice model. Returns True on success."""
    try:
        logging.info(f"Downloading Piper model: {name}")
        download_voices.download_voice(name, model_dir, force_redownload=True)
        return True
    except Exception as e:
        logging.warning(f"Failed to download model '{name}': {e}")
        return False


def _select_model(model_dir, voice=None):
    """Select a Piper model, falling back recursively on failure.

    Resolution: "random" picks from available (falling back to default if none).
    A specific name uses it if local, tries downloading, then recurses to default.
    Default recurses to "random" (any available model). "random" with nothing raises.
    """
    if voice is None:
        voice = Config.instance().piper.voice

    models = _available_models(model_dir)

    if voice == "random":
        if not models:
            logging.warning("No models available, downloading default model")
            _download_model(DEFAULT_VOICE, model_dir)
            models = _available_models(model_dir)
        if not models:
            raise RuntimeError("No Piper models available and all download attempts failed")
        choice = random.choice(models)
        logging.info(f"Selected random speaker: {choice.stem}")
        return choice

    # Specific voice — use if available
    matching = [m for m in models if m.stem == voice]
    if matching:
        logging.info(f"Using voice: {voice}")
        return matching[0]

    # Try downloading
    logging.info(f"Voice '{voice}' not found locally, attempting download")
    if _download_model(voice, model_dir):
        models = _available_models(model_dir)
        matching = [m for m in models if m.stem == voice]
        if matching:
            logging.info(f"Using downloaded voice: {voice}")
            return matching[0]

    # Fall back: specific -> default -> random
    if voice != DEFAULT_VOICE:
        logging.warning(f"Could not obtain '{voice}', falling back to default ({DEFAULT_VOICE})")
        return _select_model(model_dir, DEFAULT_VOICE)

    logging.warning(f"Could not obtain default, falling back to any available model")
    return _select_model(model_dir, "random")


def synthesize_greeting(text, io_manager):
    """
    Convert greeting text to speech using Piper TTS and save as WAV file.

    Args:
        text: Greeting text to synthesize
        io_manager: The IOManager set up with the correct paths

    Returns:
        bool: True on success, False on failure
    """
    output_path = io_manager.paths.audio_path

    try:
        logging.info("Initializing Piper TTS")
        piper_cfg = Config.instance().piper

        syn_config = SynthesisConfig(
            length_scale=piper_cfg.length_scale,
            noise_scale=piper_cfg.noise_scale,
            noise_w_scale=piper_cfg.noise_w_scale,
        )
        logging.debug(
            f"Piper config: voice={piper_cfg.voice}, "
            f"length_scale={piper_cfg.length_scale}, "
            f"noise_scale={piper_cfg.noise_scale}, "
            f"noise_w_scale={piper_cfg.noise_w_scale}"
        )

        from .io_manager import MODEL_DIR
        speaker = _select_model(MODEL_DIR)

        logging.info(f"Synthesizing greeting to {output_path}")
        start_time = time.time()

        voice = PiperVoice.load(speaker)
        with wave.open(str(output_path), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=syn_config)

        elapsed = time.time() - start_time
        logging.info(f"TTS synthesis complete ({elapsed:.2f}s)")
        return True

    except Exception as e:
        logging.exception(f"TTS synthesis failed: {e}")
        return False
