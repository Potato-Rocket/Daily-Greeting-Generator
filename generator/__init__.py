"""
Daily Greeting Generator

This package handles the generation of personalized wake-up messages.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("daily-greeting")
except PackageNotFoundError:
    __version__ = "unknown"
