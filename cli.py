"""CLI entry point for local development. Loads .env then runs the pipeline."""

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from generator.generator import run_pipeline
run_pipeline()
