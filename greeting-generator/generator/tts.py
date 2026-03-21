"""
Text-to-Speech Module for Daily Greeting Generator

Handles audio rendering using Coqui TTS and delivery to playback server.
"""

import logging
import time
import random
from pathlib import Path
import wave
from piper import PiperVoice, download_voices


def synthesize_greeting(text, io_manager):
    """
    Convert greeting text to speech using Coqui TTS voice cloning and save as WAV file.

    Randomly selects a voice directory, then uses all clip*.wav files from that
    directory as references for voice cloning.

    Args:
        text: Greeting text to synthesize
        io_manager: The IOManager set up with the correct paths

    Returns:
        str: Path to generated audio file, or None on failure
    """
    output_path = io_manager.paths.audio_path

    try:
        logging.info("Initializing piper")

        # Glob for model files in the models directory
        logging.info("Searching for models")
        model_dir = io_manager.paths.model_dir
        models = [m for m in model_dir.glob("*.onnx") if (m.with_suffix(".onnx.json")).exists()]

        # Ensure at least one valid model is present
        if not models:
            logging.warning("No valid models found, downloading default model")
            download_voices.download_voice("en_US-lessac-high", model_dir, force_redownload=True)
            models = [m for m in model_dir.glob("*.onnx") if (m.with_suffix(".onnx.json")).exists()]

        logging.debug(f"Speaker options:\n- {chr(10).join(m.stem for m in models)}")
        speaker = random.choice(models)
        logging.info(f"Selected random speaker: {speaker.stem}")

        logging.info(f"Synthesizing greeting to {output_path}")
        start_time = time.time()

        # Synthesize with Piper TTS
        voice = PiperVoice.load(speaker)
        with wave.open(str(output_path), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)

        elapsed = time.time() - start_time
        logging.info(f"TTS synthesis complete ({elapsed:.2f}s)")
        return True

    except Exception as e:
        logging.exception(f"TTS synthesis failed: {e}")
        return False
