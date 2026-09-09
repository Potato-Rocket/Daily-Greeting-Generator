"""
Test TTS Runner

Loads a previously generated greeting text and synthesizes it with one or more
Piper voices, for comparing voices without re-running the full pipeline.

Usage:
    python tests/test_tts.py [date] [voice ...]

    date   Date to load greeting text from (YYYY-MM-DD). Defaults to the most
           recently generated greeting.
    voice  One or more Piper voice names (.onnx stem) to synthesize with.
           Defaults to every voice model available locally in models/.

Output is written to greeting_{date}_{voice}.wav in that date's data
directory for each voice tested, leaving the canonical greeting_{date}.wav
untouched.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from generator.config import Config
from generator.io_manager import IOManager, setup_logging, get_paths, Mode, MODEL_DIR
from generator.tts import synthesize_greeting


def _local_voices():
    """Return names of Piper voice models available in MODEL_DIR."""
    return sorted(m.stem for m in MODEL_DIR.glob("*.onnx") if m.with_suffix(".onnx.json").exists())


def main():
    """Synthesize a stored greeting with one or more Piper voices."""
    args = sys.argv[1:]

    date_arg = None
    if args and args[0].count("-") == 2 and args[0][:4].isdigit():
        date_arg = args.pop(0)

    voices = args or _local_voices()
    if not voices:
        print(f"Error: No Piper voice models found in {MODEL_DIR}")
        sys.exit(1)

    setup_logging()
    Config.load()

    paths, error = get_paths(date_arg or Mode.LAST)
    if error:
        print(f"Error: {error}")
        sys.exit(1)

    io_manager = IOManager(paths)

    logging.info("=== TTS TEST START ===")
    logging.info(f"Loading greeting from {io_manager.paths.date_str}")

    try:
        if not io_manager.paths.greeting_path.exists():
            logging.error(f"TTS test aborted: Greeting file not found at {io_manager.paths.greeting_path}")
            return

        greeting = io_manager.paths.greeting_path.read_text()
        if not greeting:
            logging.error("TTS test aborted: Greeting file is empty")
            return

        logging.info(f"Loaded greeting ({len(greeting)} chars)")
        logging.info(f"Testing {len(voices)} voice(s): {', '.join(voices)}")

        for voice in voices:
            logging.info(f"--- Synthesizing with voice: {voice} ---")
            Config.instance().piper.voice = voice
            io_manager.paths.audio_path = (
                io_manager.paths.date_dir / f"greeting_{io_manager.paths.date_str}_{voice}.wav"
            )

            if synthesize_greeting(greeting, io_manager):
                logging.info(f"Saved: {io_manager.paths.audio_path}")
            else:
                logging.error(f"Synthesis failed for voice: {voice}")

        logging.info("=== TTS TEST COMPLETE ===")

    except Exception as e:
        logging.exception(f"TTS test error: {e}")
        raise


if __name__ == "__main__":
    main()
