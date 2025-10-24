"""
Data Formatters for Daily Greeting Generator

Transforms raw API data into human-readable strings for LLM consumption.
"""

import logging


def format_weather(weather_data):
    """
    Format weather data into human-readable string.

    Args:
        weather_data: Dict with 'overnight', 'sunrise', 'today' keys, or None if weather unavailable

    Returns:
        str: Formatted weather description with overnight, sunrise, and today forecasts
    """
    if not weather_data:
        logging.warning("No weather data provided for formatting")
        return "WEATHER DATA: Not available"

    overnight = f"Overnight: {weather_data['overnight']['description']} {weather_data['overnight']['precipitation']}% chance of precipitation."

    sunrise = f"Sunrise (NOW): {weather_data['sunrise']['temperature']}°F, {weather_data['sunrise']['conditions']}, {weather_data['sunrise']['humidity']}% humidity, dewpoint {weather_data['sunrise']['dewpoint']:.2f}°C, wind {weather_data['sunrise']['windSpeed']} from {weather_data['sunrise']['windDirection']}, {weather_data['sunrise']['precipitation']}% chance of precipitation."

    today = f"Today ({weather_data['today']['dayOfWeek']}): {weather_data['today']['description']} {weather_data['today']['precipitation']}% chance of precipitation."

    return "WEATHER DATA:\n" + overnight + "\n" + sunrise + "\n" + today


def format_literature(literature_data):
    """
    Format literature data into a human-readable string.

    Args:
        literature_data: Dict with 'title', 'author', 'excerpt' keys, or None if literature unavailable

    Returns:
        str: Formatted literature excerpt with title and author info
    """
    if not literature_data:
        logging.warning("No literature data provided for formatting")
        return "LITERATURE EXCERPT: Not available"

    author_info = literature_data['author']['name']
    if literature_data['author']['birth_year'] and literature_data['author']['death_year']:
        author_info += f" ({literature_data['author']['birth_year']}-{literature_data['author']['death_year']})"

    return f'LITERATURE EXCERPT: "{literature_data["title"]}" by {author_info}:\n\n{literature_data["excerpt"]}'


def format_albums(album_data):
    """
    Format album list into a human-readable numbered string.

    Args:
        album_data: List of album dicts with 'name', 'artist', 'year', 'genres' keys

    Returns:
        str: Formatted numbered list of albums with metadata
    """
    album_lines = []
    for index, album in enumerate(album_data):
        genres = ', '.join(album['genres']) if album['genres'] else 'Unknown genre'
        album_lines.append(f"[{index + 1}] \"{album['name']}\" by {album['artist']} ({album['year']}) - Genres: {genres}")

    return "ALBUMS:\n" + "\n".join(album_lines)


def format_album(album_data):
    """
    Format detailed album data into a human-readable string.

    Args:
        album_data: Dict with 'name', 'artist', 'year', 'genres', 'songs', 'coverart' keys

    Returns:
        str: Formatted album details with full tracklist and optional cover art description
    """
    if not album_data:
        logging.warning("No album data provided for formatting.")
        return "No album data available."

    genres = ', '.join(album_data['genres']) if album_data['genres'] else 'Unknown genre'

    song_lines = []
    for index, song in enumerate(album_data['songs']):
        song_lines.append(f"{index + 1}. {song['title']}")

    string = f"""SELECTED ALBUM: \"{album_data['name']}\" by {album_data['artist']} ({album_data['year']})
Genres: {genres}
Tracklist:
{"\n".join(song_lines)}"""

    if album_data['coverart']:
        string += f"\nCover art description:\n{album_data['coverart']}"

    return string
