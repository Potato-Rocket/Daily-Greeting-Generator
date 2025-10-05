"""
Text-to-Speech Module for Daily Greeting Generator

Handles audio rendering using Piper TTS and delivery to playback server.
"""

import wave
import logging
import time
import requests
from pathlib import Path

from piper.voice import PiperVoice
from piper.config import SynthesisConfig

# Piper TTS configuration
MODEL_PATH = "models/en_US-ryan-high.onnx"
LENGTH_SCALE = 1.15  # Speech speed (< 1 faster, > 1 slower, try 1.1-1.2 for ponderous)

# Playback server address
SERVER_ADDR = "http://192.168.1.36:7000"


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


def send_to_playback_server(audio_path):
    """
    Send audio file to playback server via HTTP POST.

    Args:
        audio_path: Path to WAV file to send

    Returns:
        bool: True if successfully sent, False on failure
    """
    try:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            logging.error(f"Audio file not found: {audio_path}")
            return False

        endpoint = f"{SERVER_ADDR}/receive"

        logging.info(f"Sending audio to playback server: {endpoint}")

        with open(audio_path, 'rb') as f:
            response = requests.post(
                endpoint,
                data=f,
                headers={'Content-Type': 'audio/wav'},
                timeout=30
            )

        if response.status_code == 200:
            logging.info("Audio sent successfully to playback server")
            return True
        else:
            logging.error(f"Playback server returned status {response.status_code}: {response.text}")
            return False

    except requests.exceptions.Timeout:
        logging.error(f"Connection timeout after 30s - playback server may be unreachable at {endpoint}")
        return False
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error - cannot reach playback server at {endpoint}: {e}")
        return False
    except Exception as e:
        logging.exception(f"Unexpected error sending audio: {e}")
        return False
