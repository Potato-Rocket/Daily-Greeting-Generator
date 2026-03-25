"""
Daily Greeting Generator

This package handles the generation of personalized wake-up messages by:
1. Fetching data from weather, literature, and music APIs
2. Running multi-stage LLM pipeline to synthesize creative content
3. Generating text-to-speech audio for sunrise playback

Runs on: Home server (i7/GTX1650) at 2am daily
"""

__version__ = "0.1.0"
