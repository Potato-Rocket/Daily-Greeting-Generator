"""
I/O Management for Daily Greeting Generator

Handles all file operations including:
- Dated directory structure in ./tmp/{YYYY-MM-DD}/
- Pipeline output logging (prompts and responses)
- Timestamped execution logs
- Incremental data saving (JSON)
- Greeting text output
- Album cover art saving
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from .llm import MODEL, IMAGE_MODEL

# Default output directory
BASE_DIR = "./tmp"


class IOManager:
    """Manages all file I/O for pipeline execution."""

    def __init__(self, base_dir=BASE_DIR):
        """
        Initialize IOManager with dated subdirectory.

        Args:
            base_dir: Base directory for all outputs (default: BASE_DIR constant)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

        # Create dated subdirectory
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.run_dir = self.base_dir / self.date_str
        self.run_dir.mkdir(exist_ok=True)

        # Pipeline output file handle
        self.pipeline_file = None

    def init_pipeline_file(self):
        """Initialize pipeline output file for prompts and responses."""
        pipeline_path = self.run_dir / f"pipeline_{self.date_str}.txt"
        self.pipeline_file = open(pipeline_path, 'w', encoding='utf-8')
        logging.info(f"Pipeline output will be saved to {pipeline_path}")

        self.write_to_pipeline(f"""Morning greeting generation pipeline for {self.date_str}.
Ollama textual model: {MODEL}
Ollama multimodal vision model: {IMAGE_MODEL}""")

        return pipeline_path

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
        data_path = self.run_dir / f"data_{self.date_str}.json"

        # Load existing data if file exists
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        # Update with new fields
        data.update(kwargs)
        print(json.dumps(kwargs, indent=2))

        # Write back to file
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_data_file(self, date_str=None):
        """
        Load previously saved data_{date}.json file.

        Args:
            date_str: Date string (YYYY-MM-DD) to load. If None, uses current date.

        Returns:
            dict: Loaded pipeline data with 'weather', 'literature', 'album' keys, or None on failure
        """
        if date_str is None:
            date_str = self.date_str

        data_path = self.base_dir / date_str / f"data_{date_str}.json"

        if not data_path.exists():
            logging.error(f"Data file not found: {data_path}")
            return None

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"Loaded data from {data_path}")
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

        greeting_path = self.run_dir / f"greeting_{self.date_str}.txt"
        with open(greeting_path, 'w', encoding='utf-8') as f:
            f.write(greeting_text)
        logging.info(f"Saved greeting to {greeting_path}")

    def save_coverart(self, image_data):
        """
        Save album cover art as JPEG.

        Args:
            image_data: Raw bytes of JPEG image
        """
        coverart_path = self.run_dir / f"coverart_{self.date_str}.jpg"
        with open(coverart_path, "wb") as f:
            f.write(image_data)
        logging.info(f"Saved cover art to {coverart_path}")

    def close(self):
        """Close the pipeline file handle."""
        if self.pipeline_file:
            self.pipeline_file.close()
            self.pipeline_file = None

    def __enter__(self):
        """Context manager entry - initialize pipeline file."""
        self.init_pipeline_file()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close pipeline file."""
        self.close()
        return False  # Don't suppress exceptions


def setup_logging(io_manager, logging_level=logging.INFO):
    """
    Configure logging with timestamped file output and console output.

    Args:
        io_manager: IOManager instance for determining log file path
    """
    log_path = io_manager.run_dir / f"log_{io_manager.date_str}.txt"

    logging.basicConfig(
        level=logging_level,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

    logging.info(f"Logging to {log_path}")
