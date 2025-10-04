"""
Text-to-Speech Module for Daily Greeting Generator

Handles audio rendering using Piper TTS.
"""

import wave
import logging
import time

from piper.voice import PiperVoice
from piper.config import SynthesisConfig


# Piper TTS configuration
MODEL_PATH = "models/en_US-ryan-high.onnx"
LENGTH_SCALE = 1.15  # Speech speed (< 1 faster, > 1 slower, try 1.1-1.2 for ponderous)


def synthesize_greeting(text, output_path, model_path=MODEL_PATH):
    """
    Convert greeting text to speech using Piper TTS and save as WAV file.

    Args:
        text: Greeting text to synthesize
        output_path: Path to save WAV file
        model_path: Path to .onnx model file (default: MODEL_PATH)

    Returns:
        str: Path to generated audio file, or None on failure
    """

    try:
        logging.info(f"Loading Piper voice model from {model_path}")
        voice = PiperVoice.load(model_path)

        logging.info(f"Synthesizing greeting to {output_path}")

        # Configure synthesis parameters
        syn_config = SynthesisConfig(length_scale=LENGTH_SCALE)

        start_time = time.time()
        with wave.open(str(output_path), 'wb') as wav_file:
            # Use synthesize_wav to handle audio generation and WAV writing
            voice.synthesize_wav(text, wav_file, syn_config=syn_config)

        elapsed = time.time() - start_time
        logging.info(f"TTS synthesis complete ({elapsed:.2f}s)")
        return str(output_path)

    except Exception as e:
        logging.exception(f"TTS synthesis failed: {e}")
        return None
