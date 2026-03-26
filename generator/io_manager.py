"""
I/O Management for Daily Greeting Generator

Handles all file operations including:
- Dated directory structure in ./data/{YYYY-MM-DD}/
- Pipeline output logging (prompts and responses)
- Timestamped execution logs
- Incremental data saving (JSON)
- Saving and loading the selected book text
- Greeting text output
- Album cover art saving
"""

import os
import json
import logging
import random
from enum import Enum
from pathlib import Path
from datetime import datetime

from .config import Config

BASE_DIR   = Path(os.environ.get("GREETING_BASE_DIR", "/"))
DATA_DIR   = BASE_DIR / "data"
MODEL_DIR  = BASE_DIR / "models"
LOG_LEVEL  = logging.INFO
LOG_FMT = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')


def setup_logging(log_path=None):
    """Configure logging to console, and optionally to a file."""
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(LOG_FMT)
    root_logger.addHandler(console_handler)
    if log_path:
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setFormatter(LOG_FMT)
        root_logger.addHandler(file_handler)
        logging.info(f"Logging to {log_path}")


class Mode(Enum):
    FAIL = "fail"
    FIRST = "first"
    LAST = "last"
    RANDOM = "random"


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


class PathManager:
    """Pure path computation for a given date. No side effects."""

    def __init__(self, date_str):
        self.date_str      = date_str

        # Directories
        self.date_dir      = DATA_DIR / date_str

        # File paths
        self.data_path     = self.date_dir / f"data_{date_str}.json"
        self.audio_path    = self.date_dir / f"greeting_{date_str}.wav"
        self.greeting_path = self.date_dir / f"greeting_{date_str}.txt"
        self.book_path     = self.date_dir / f"book_{date_str}.txt"
        self.coverart_path = self.date_dir / f"coverart_{date_str}.jpg"
        self.log_path      = self.date_dir / f"log_{date_str}.txt"
        self.pipeline_path = self.date_dir / f"pipeline_{date_str}.txt"
    
    def is_valid(self):
        return (
            self.data_path.exists() and
            self.audio_path.exists()
        )


def get_paths(date_str, fallback=Mode.FAIL):
    try:
        date_str = Mode(date_str)
    except ValueError:
        pass  # literal date string

    date_strs = [d.name for d in DATA_DIR.glob("20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]")]
    valid_strs = [d for d in date_strs if PathManager(d).is_valid()]
    valid_strs.sort()

    if not valid_strs:
        logging.error("No valid data paths found!")
        return None, "No valid greetings found"

    match date_str:
        case Mode.FIRST:
            logging.info("Fetching first valid date")
            return PathManager(valid_strs[0]), None
        case Mode.LAST:
            logging.info("Fetching last valid date")
            return PathManager(valid_strs[-1]), None
        case Mode.RANDOM:
            logging.info("Fetching random valid date")
            return PathManager(random.choice(valid_strs)), None
        case _:
            if date_str in valid_strs:
                return PathManager(date_str), None
            elif fallback == Mode.FAIL:
                logging.error("Specified date or mode was not valid!")
                return None, f"No greeting found for {date_str}"
            else:
                logging.warning("Specified date was not valid, using fallback")
                return get_paths(fallback)


class IOManager:
    """Manages all file I/O for pipeline execution."""

    def __init__(self, paths=None):
        self.paths = paths or PathManager(_today())

        # Ensure directories exist
        self.paths.date_dir.mkdir(exist_ok=True, parents=True)
        MODEL_DIR.mkdir(exist_ok=True, parents=True)

        self.pipeline_file = None

    def init_pipeline_file(self):
        """Initialize pipeline output file for prompts and responses."""
        self.pipeline_file = open(self.paths.pipeline_path, 'a', encoding='utf-8')
        logging.info(f"Pipeline output will be saved to {self.paths.pipeline_path}")
        self.write_to_pipeline(f"""Morning greeting generation pipeline for {self.paths.date_str}.
Ollama textual model: {Config.instance().ollama.model}
Ollama multimodal vision model: {Config.instance().ollama.image_model}""")

    def write_to_pipeline(self, text):
        """
        Write text to pipeline output file.

        Args:
            text: Text to write
        """
        if self.pipeline_file:
            self.pipeline_file.write(text + "\n")
            self.pipeline_file.flush()

    def print_section(self, title, content=None):
        """
        Print formatted section header and optional content to console and pipeline file.

        Args:
            title: Section title
            content: Optional content to print
        """
        separator = "\n" + "=" * 50
        header = f"{separator}\n{title}{separator}"
        print(header)
        self.write_to_pipeline(header)

        if content:
            print(content)
            self.write_to_pipeline(content)

    def update_data_file(self, **kwargs):
        """
        Update data_{date}.json with new fields as they're generated.

        Args:
            **kwargs: Field name and value pairs to add/update in JSON
        """
        # Load existing data if file exists
        if self.paths.data_path.exists():
            with open(self.paths.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        # Update with new fields
        data.update(kwargs)
        print(json.dumps(kwargs, indent=2))

        # Write back to file
        with open(self.paths.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_data_file(self):
        """
        Load previously saved data_{date}.json file.

        Returns:
            dict: Loaded pipeline data with 'weather', 'literature', 'album' keys, or None on failure
        """
        if not self.paths.data_path.exists():
            logging.error(f"Data file not found: {self.paths.data_path}")
            return None

        try:
            with open(self.paths.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"Loaded data from {self.paths.data_path}")
            return data
        except Exception as e:
            logging.exception(f"Failed to load data file: {e}")
            return None

    def save_greeting(self, greeting_text):
        """
        Save the final greeting to greeting_{date}.txt file.

        Args:
            greeting_text: Plain text greeting (no boilerplate)
        """
        if not greeting_text:
            logging.warning("No greeting text to save.")
            return

        with open(self.paths.greeting_path, 'w', encoding='utf-8') as f:
            f.write(greeting_text)
        logging.info(f"Saved greeting to {self.paths.greeting_path}")

    def save_coverart(self, image_data):
        """
        Save album cover art as JPEG.

        Args:
            image_data: Raw bytes of JPEG image
        """
        with open(self.paths.coverart_path, "wb") as f:
            f.write(image_data)
        logging.info(f"Saved cover art to {self.paths.coverart_path}")

    def save_book(self, text):
        """
        Save the selected book to book_{date}.txt file.

        Args:
            text: Unicode text fetched from prject gutenberg
        """
        with open(self.paths.book_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logging.info(f"Saved book to {self.paths.book_path}")

    def load_book(self):
        """
        Load the previously saved book_{date}.txt file.

        Returns:
            str: the content of the book file
        """
        try:
            with open(self.paths.book_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logging.info(f"Loaded book from {self.paths.book_path}")
            return text
        except Exception as e:
            logging.exception(f"Failed to load book: {e}")
            return None

    def close(self):
        """Close pipeline file and reset logging to console only."""
        if self.pipeline_file:
            self.pipeline_file.close()
            self.pipeline_file = None
        setup_logging()

    def __enter__(self):
        """Context manager entry - configure logging and initialize pipeline file."""
        setup_logging(self.paths.log_path)
        self.init_pipeline_file()
        return self

    def __exit__(self):
        """Context manager exit - close pipeline file."""
        self.close()
        return False
