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

import json
import logging
from enum import Enum
from pathlib import Path
from datetime import datetime

from .llm import MODEL, IMAGE_MODEL

BASE_DIR = Path("/")
LOG_LEVEL = logging.INFO


class Fallback(Enum):
    FAIL = "fail"
    FIRST = "first"
    LAST = "last"
    RANDOM = "random"


class IOManager:
    """Manages all file I/O for pipeline execution."""

    def __init__(self, date_str=None):
        """
        Initialize IOManager with dated subdirectory.

        Args:
            date_str: Optional date string (YYYY-MM-DD). If None, uses today's date.
        """
        BASE_DIR.mkdir(exist_ok=True)

        # Create date string
        self.date_str = date_str if date_str else datetime.now().strftime(r"%Y-%m-%d")

        # Directories
        self.data_dir = BASE_DIR / "data" / self.date_str
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.model_dir = BASE_DIR / "models"
        self.model_dir.mkdir(exist_ok=True, parents=True)

        # File paths
        self.data_path     = self.data_dir / f"data_{self.date_str}.json"
        self.audio_path    = self.data_dir / f"greeting_{self.date_str}.wav"
        self.greeting_path = self.data_dir / f"greeting_{self.date_str}.txt"
        self.book_path     = self.data_dir / f"book_{self.date_str}.txt"
        self.coverart_path = self.data_dir / f"coverart_{self.date_str}.jpg"
        self.log_path      = self.data_dir / f"log_{self.date_str}.txt"
        self.pipeline_path = self.data_dir / f"pipeline_{self.date_str}.txt"

        # Pipeline output file handle
        self.pipeline_file = None

    def init_pipeline_file(self):
        """Initialize pipeline output file for prompts and responses."""
        self.pipeline_file = open(self.pipeline_path, 'a', encoding='utf-8')
        logging.info(f"Pipeline output will be saved to {self.pipeline_path}")
        self.write_to_pipeline(f"""Morning greeting generation pipeline for {self.date_str}.
Ollama textual model: {MODEL}
Ollama multimodal vision model: {IMAGE_MODEL}""")

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
        if self.data_path.exists():
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        # Update with new fields
        data.update(kwargs)
        print(json.dumps(kwargs, indent=2))

        # Write back to file
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_data_file(self):
        """
        Load previously saved data_{date}.json file.

        Returns:
            dict: Loaded pipeline data with 'weather', 'literature', 'album' keys, or None on failure
        """
        if not self.data_path.exists():
            logging.error(f"Data file not found: {self.data_path}")
            return None

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"Loaded data from {self.data_path}")
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

        with open(self.greeting_path, 'w', encoding='utf-8') as f:
            f.write(greeting_text)
        logging.info(f"Saved greeting to {self.greeting_path}")

    def save_coverart(self, image_data):
        """
        Save album cover art as JPEG.

        Args:
            image_data: Raw bytes of JPEG image
        """
        with open(self.coverart_path, "wb") as f:
            f.write(image_data)
        logging.info(f"Saved cover art to {self.coverart_path}")

    def save_book(self, text):
        """
        Save the selected book to book_{date}.txt file.

        Args:
            text: Unicode text fetched from prject gutenberg
        """
        with open(self.book_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logging.info(f"Saved book to {self.book_path}")

    def load_book(self):
        """
        Load the previously saved book_{date}.txt file.

        Returns:
            str: the content of the book file
        """
        try:
            with open(self.book_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logging.info(f"Loaded book from {self.book_path}")
            return text
        except Exception as e:
            logging.exception(f"Failed to load book: {e}")
            return None

    def close(self):
        """Close the pipeline file handle."""
        if self.pipeline_file:
            self.pipeline_file.close()
            self.pipeline_file = None

    def setup_logging(self):
        """Configure logging with timestamped file and console output."""
        root_logger = logging.getLogger()
        root_logger.setLevel(LOG_LEVEL)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        fmt = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')

        file_handler = logging.FileHandler(self.log_path, mode='a')
        file_handler.setFormatter(fmt)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        logging.info(f"Logging to {self.log_path}")

    def __enter__(self):
        """Context manager entry - configure logging and initialize pipeline file."""
        self.setup_logging()
        self.init_pipeline_file()
        return self

    def __exit__(self):
        """Context manager exit - close pipeline file."""
        self.close()
        return False
