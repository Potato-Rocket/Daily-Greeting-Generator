"""
Text-to-Speech Module for Daily Greeting Generator

Handles audio rendering using Coqui TTS and delivery to playback server.
"""

import logging
import time
import random
import torch
import requests
from pathlib import Path
from TTS.api import TTS

# Playback server address
SERVER_ADDR = "http://192.168.1.36:7000"


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
    output_path = io_manager.data_dir / f"greeting_{io_manager.date_str}.wav"

    try:
        logging.info("Initializing Coqui TTS with XTTS-v2 model")

        # Initialize TTS with GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Using device: {device}")

        if device == "cuda":
            gpu_name = torch.cuda.get_device_name(0)
            logging.info(f"GPU detected: {gpu_name}")

        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        logging.debug(f"Speaker options: {tts.speakers}")
        speaker = random.choice(tts.speakers)
        logging.info(f"Selected random speaker: {speaker}")

        logging.info(f"Synthesizing greeting to {output_path}")
        start_time = time.time()

        # Synthesize with voice cloning (pass all clips as list)
        tts.tts_to_file(
            text=text,
            speaker=speaker,
            language="en",
            file_path=str(output_path)
        )

        elapsed = time.time() - start_time
        logging.info(f"TTS synthesis complete ({elapsed:.2f}s)")
        return str(output_path)

    except Exception as e:
        logging.exception(f"TTS synthesis failed: {e}")
        return None


def send_to_playback_server(audio_path, album, max_retries=5):
    """
    Send audio file and album song URLs to playback server via HTTP POST with retry logic.

    Args:
        audio_path: Path to WAV file to send
        album: Album dict containing 'songs' list with 'url' keys, or None if no album available
        max_retries: Maximum number of retry attempts (default: 5)

    Returns:
        bool: True if successfully sent, False on failure after all retries
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        logging.error(f"Audio file not found: {audio_path}")
        return False

    # Extract song URLs from album (empty list if album is None or has no songs)
    if album and album.get('songs'):
        song_urls = [song['url'] for song in album['songs']]
        logging.info(f"Preparing to send greeting + {len(song_urls)} song URLs to playback server")
    else:
        song_urls = []
        logging.info("Preparing to send greeting without album data to playback server")

    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                # Exponential backoff: 2^(attempt-1) seconds (2s, 4s, 8s...)
                wait_time = 2 ** (attempt - 1)
                logging.info(f"Retry attempt {attempt}/{max_retries} after {wait_time}s wait")
                time.sleep(wait_time)

            endpoint = f"{SERVER_ADDR}/greeting"

            logging.info(f"Sending audio + song URLs to playback server: {endpoint}")

            with open(audio_path, 'rb') as f:
                # Send audio file and song URLs as multipart form data
                files = {'audio': f}
                data = {'song_urls': '\n'.join(song_urls)}
                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=30
                )

            if response.status_code == 200:
                logging.info("Audio and songs sent successfully to playback server")
                return True
            else:
                logging.error(f"Playback server returned status {response.status_code}: {response.text}")
                # Don't retry on 4xx errors (client errors like 400, 404)
                if 400 <= response.status_code < 500:
                    logging.error("Client error - not retrying")
                    return False
                # Retry on 5xx server errors
            
        except requests.exceptions.Timeout:
            logging.error(f"Connection timeout after 30s (attempt {attempt}/{max_retries})")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error (attempt {attempt}/{max_retries}): {e}")
        except Exception as e:
            logging.exception(f"Unexpected error (attempt {attempt}/{max_retries}): {e}")

    # All retries exhausted
    logging.error(f"Failed to send audio after {max_retries} attempts")
    return False
