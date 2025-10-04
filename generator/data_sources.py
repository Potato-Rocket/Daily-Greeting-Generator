"""
Data Sources for Daily Greeting Generator

Fetches data from external APIs:
- Weather data from weather.gov API
- Literary excerpts from Project Gutenberg via Gutendex API
- Music metadata from Navidrome server (Subsonic API)
"""

import requests
from urllib.parse import quote
import base64
import random
import re
import logging
import time


# Weather.gov API configuration
LAT = 0.0
LON = 0.0
USER_AGENT = "DailyGreeting/1.0"

# Navidrome server configuration
NAVIDROME_BASE = "http://192.168.1.134:4533"
NAVIDROME_USER = "username"
NAVIDROME_PASS = "password"
NAVIDROME_CLIENT = "DailyGreeting"

# Literature excerpt parameters
LITERATURE_LENGTH = 600
LITERATURE_PADDING = 2000


def get_weather_data():
    """
    Get weather data from weather.gov API.

    Returns:
        dict: Weather data with 'overnight', 'sunrise', 'today' keys, or None on failure
    """
    try:
        start_time = time.time()
        logging.info("Fetching weather data from weather.gov API")

        # Convert latitude and longitude to NWS grid coordinates
        points_url = f"https://api.weather.gov/points/{LAT},{LON}"
        points_response = requests.get(points_url, headers={"User-Agent": USER_AGENT})
        logging.debug(f"Points API call took {time.time() - start_time:.2f}s")

        if points_response.status_code != 200:
            logging.error(f"Weather.gov points API returned status {points_response.status_code}")
            return None

        points_data = points_response.json()
        forecast_url = points_data["properties"]["forecast"]
        forecast_hourly_url = points_data["properties"]["forecastHourly"]
        logging.debug(f"Forecast URLs: {forecast_url}, {forecast_hourly_url}")

        # Fetch forecast data
        forecast_start = time.time()
        forecast_response = requests.get(forecast_url, headers={"User-Agent": USER_AGENT})
        hourly_response = requests.get(forecast_hourly_url, headers={"User-Agent": USER_AGENT})
        logging.debug(f"Forecast API calls took {time.time() - forecast_start:.2f}s")

        if forecast_response.status_code != 200 or hourly_response.status_code != 200:
            logging.error(f"Weather.gov forecast API error (daily: {forecast_response.status_code}, hourly: {hourly_response.status_code})")
            return None

        forecast_data = forecast_response.json()
        hourly_data = hourly_response.json()

        # Find first daytime hour for sunrise conditions
        sunrise_hour = None
        for hour in hourly_data["properties"]["periods"]:
            if hour['isDaytime']:
                sunrise_hour = hour
                break

        if not sunrise_hour:
            logging.warning("No daytime hours found in forecast data")
            return None

        overnight = forecast_data["properties"]["periods"][0]
        today = forecast_data["properties"]["periods"][1]

        total_time = time.time() - start_time
        logging.debug(f"Total weather API time: {total_time:.2f}s")
        logging.info("Weather data fetched successfully")

        return {
            "overnight": {
                "dayOfWeek": overnight['name'],
                "precipitation": overnight['probabilityOfPrecipitation']['value'],
                "description": overnight['detailedForecast']
            },
            "sunrise": {
                "temperature": sunrise_hour['temperature'],
                "humidity": sunrise_hour['relativeHumidity']['value'],
                "dewpoint": sunrise_hour['dewpoint']['value'],
                "windSpeed": sunrise_hour['windSpeed'],
                "windDirection": sunrise_hour['windDirection'],
                "precipitation": sunrise_hour['probabilityOfPrecipitation']['value'],
                "conditions": sunrise_hour['shortForecast']
            },
            "today": {
                "dayOfWeek": today['name'],
                "precipitation": today['probabilityOfPrecipitation']['value'],
                "description": today['detailedForecast']
            }
        }

    except Exception as e:
        logging.exception(f"Weather fetch error: {e}")
        return None


def get_random_literature(length=LITERATURE_LENGTH, padding=LITERATURE_PADDING):
    """
    Retrieve a random excerpt from an English book using the Gutendex API.

    Uses exponential distribution to select random page, avoiding unreliable ID guessing.

    Args:
        length: Target length of excerpt in characters
        padding: Characters to skip from start/end to avoid headers/footers

    Returns:
        dict: Literature data with 'title', 'author', 'excerpt' keys, or None on failure
    """
    try:
        start_time = time.time()
        # Select random page using exponential distribution (favors lower page numbers)
        random_page = int(random.expovariate(0.05)) + 1
        logging.info(f"Fetching literature from Gutendex (page {random_page})")

        api_url = f"https://gutendex.com/books/?languages=en&page={random_page}"
        response = requests.get(api_url)
        logging.debug(f"Gutendex API call took {time.time() - start_time:.2f}s")

        if response.status_code != 200:
            logging.error(f"Gutendex API returned status {response.status_code}")
            return None

        data = response.json()
        books = data.get('results', [])

        if not books:
            logging.warning(f"No books found on Gutendex page {random_page}")
            return None

        logging.debug(f"Found {len(books)} books on page {random_page}")

        # Select random book and check for plain text format
        book = random.choice(books)
        formats = book.get('formats', {})
        book_id = book['id']
        title = book['title']

        text_url = (formats.get('text/plain; charset=utf-8') or
                    formats.get('text/plain; charset=us-ascii') or
                    formats.get('text/plain'))

        if not text_url:
            logging.warning(f"No plain text format for book '{title}' (ID: {book_id})")
            return None

        logging.info(f"Fetching text for '{title}'")
        logging.debug(f"Book ID {book_id}, URL: {text_url}")

        text_start = time.time()
        text_response = requests.get(text_url, timeout=10)
        logging.debug(f"Book text download took {time.time() - text_start:.2f}s")
        if text_response.status_code != 200:
            logging.error(f"Failed to fetch book text (status {text_response.status_code})")
            return None

        text = text_response.text

        # Extract author metadata
        authors = book.get('authors', [])
        if authors and isinstance(authors[0], dict):
            author = {
                'name': authors[0].get('name', 'Unknown'),
                'birth_year': authors[0].get('birth_year'),
                'death_year': authors[0].get('death_year')
            }
        else:
            author = {
                'name': str(authors[0]) if authors else 'Unknown',
                'birth_year': None,
                'death_year': None
            }

        # Remove Project Gutenberg headers and footers
        start_match = re.search(r'\*\*\* START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*', text)
        if start_match:
            text = text[start_match.end():]

        end_match = re.search(r'\*\*\* END OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*', text)
        if end_match:
            text = text[:end_match.start()]

        if len(text) < padding * 2 + length:
            logging.warning(f"Book text too short after trimming ({len(text)} chars)")
            return None

        # Remove padding from start/end, extract random excerpt
        text = text[padding:-padding]
        start_pos = random.randint(0, len(text) - length)
        excerpt = text[start_pos:start_pos + length].strip()

        # Trim to word boundaries
        first_space = excerpt.find(' ')
        last_space = excerpt.rfind(' ')
        if first_space > 0 and last_space > first_space:
            excerpt = excerpt[first_space + 1:last_space]

        total_time = time.time() - start_time
        logging.debug(f"Total literature fetch time: {total_time:.2f}s")
        logging.info(f"Literature excerpt extracted successfully ({len(excerpt)} chars)")

        return {
            "title": title,
            "author": author,
            "excerpt": excerpt
        }

    except Exception as e:
        logging.exception(f"Literature fetch error: {e}")
        return None


def get_navidrome_albums(count=5):
    """
    Retrieve a list of random albums from a Navidrome server.

    Args:
        count: Number of random albums to fetch

    Returns:
        list: Album dicts with 'id', 'name', 'artist', 'year', 'genres' keys, or None on failure
    """
    try:
        start_time = time.time()
        logging.info(f"Fetching {count} random albums from Navidrome")

        api_url = f"{NAVIDROME_BASE}/rest/getAlbumList2.view?u={NAVIDROME_USER}&p={quote(NAVIDROME_PASS)}&v=1.16.1&c={NAVIDROME_CLIENT}&f=json&type=random&size={count}"
        response = requests.get(api_url)
        logging.debug(f"Navidrome album list API call took {time.time() - start_time:.2f}s")

        if response.status_code != 200:
            logging.error(f"Navidrome API returned status {response.status_code}")
            return None

        data = response.json()['subsonic-response']['albumList2']['album']

        # Extract relevant fields from each album
        albums = []
        for album in data:
            albums.append({
                'id': album['id'],
                'name': album['name'],
                'artist': album['artist'],
                'year': album.get('year', 'Unknown'),
                'genres': [genre['name'] for genre in album.get('genres', [])]
            })

        logging.info(f"Successfully fetched {len(albums)} albums")

        return albums

    except Exception as e:
        logging.exception(f"Navidrome album fetch error: {e}")
        return None


def get_album_details(album_id):
    """
    Retrieve detailed information about a specific album from Navidrome.

    Args:
        album_id: Navidrome album ID

    Returns:
        dict: Album details with 'songs', 'coverart' keys, or None on failure
    """
    try:
        start_time = time.time()
        logging.info(f"Fetching album details (ID: {album_id})")

        api_url = f"{NAVIDROME_BASE}/rest/getAlbum.view?u={NAVIDROME_USER}&p={quote(NAVIDROME_PASS)}&v=1.16.1&c={NAVIDROME_CLIENT}&f=json&id={album_id}"
        response = requests.get(api_url)
        logging.debug(f"Navidrome album details API call took {time.time() - start_time:.2f}s")

        if response.status_code != 200:
            logging.error(f"Navidrome API returned status {response.status_code}")
            return None

        album = response.json()['subsonic-response']['album']
        songs = [song['title'] for song in album['song']]
        logging.debug(f"Album has {len(songs)} tracks")

        # Fetch cover art if available
        coverart_id = album.get('coverArt')
        if not coverart_id:
            logging.warning(f"No cover art ID for album {album_id}")
            coverart = None
        else:
            logging.debug(f"Fetching cover art (ID: {coverart_id})")
            api_url = f"{NAVIDROME_BASE}/rest/getCoverArt.view?u={NAVIDROME_USER}&p={quote(NAVIDROME_PASS)}&v=1.16.1&c={NAVIDROME_CLIENT}&id={coverart_id}"
            art_start = time.time()
            response = requests.get(api_url)
            logging.debug(f"Cover art download took {time.time() - art_start:.2f}s")

            if response.status_code != 200:
                logging.warning(f"Cover art API returned status {response.status_code}")
                coverart = None
            else:
                coverart = base64.b64encode(response.content).decode('utf-8')
                logging.info("Cover art fetched successfully")

        total_time = time.time() - start_time
        logging.debug(f"Total album details fetch time: {total_time:.2f}s")
        logging.info("Album details fetched successfully")

        return {
            'songs': songs,
            'coverart': coverart
        }

    except Exception as e:
        logging.exception(f"Album details fetch error: {e}")
        return None
