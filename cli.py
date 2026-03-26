"""CLI entry point for local development. Loads .env then runs the pipeline."""

from dotenv import load_dotenv
load_dotenv()

from generator.generator import run_pipeline
run_pipeline()
