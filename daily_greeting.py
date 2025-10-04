import requests
import json
import random
import re
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Details for weather.gov API call
LAT = 42.2688
LON = -71.8088
USER_AGENT = "DailyGreetingYggdrasil/1.0"

# Details for Ollama API call
OLLAMA_BASE = "http://192.168.1.134:11434"
# MODEL = "mistral:7b"
MODEL = "llama3.2:3b"


def get_weather_data():
    """
    Get weather data from weather.gov API.
    Returns dict with relevant raw data, or None on failure.
    """
    try:
        # Step 1: Convert latitude and longitude to NWS grid coordinates
        # This is required to get the correct forecast URLs for the location
        logging.info(f"Fetching forecast url for coordinates: {LAT}, {LON}")
        points_url = f"https://api.weather.gov/points/{LAT},{LON}"
        points_response = requests.get(points_url, headers={"User-Agent": USER_AGENT})

        # Check if the API call was successful
        if points_response.status_code != 200:
            logging.error(f"Points API error: {points_response.status_code}")
            return None

        # Parse the response to get grid and forecast URLs
        points_data = points_response.json()

        # Step 2: Extract forecast URLs from the points API response
        # These URLs provide daily and hourly forecast data for the location
        forecast_url = points_data["properties"]["forecast"]
        forecast_hourly_url = points_data["properties"]["forecastHourly"]
        logging.debug(f"Forecast URL: {forecast_url}")
        logging.debug(f"Hourly Forecast URL: {forecast_hourly_url}")

        # Step 3: Request the actual forecast data from the URLs
        logging.info(f"Fetching forecast data...")
        forecast_response = requests.get(forecast_url, headers={"User-Agent": USER_AGENT})
        hourly_response = requests.get(forecast_hourly_url, headers={"User-Agent": USER_AGENT})

        # Check if both forecast API calls were successful
        if forecast_response.status_code != 200 or hourly_response.status_code != 200:
            logging.error("Forecast API error")
            return None

        # Parse the JSON responses for daily and hourly forecasts
        forecast_data = forecast_response.json()
        hourly_data = hourly_response.json()

        # Step 4: Find the first daytime hour in the hourly forecast
        # This is used to represent the sunrise conditions
        sunrise_hour = None
        for hour in hourly_data["properties"]["periods"]:
            if hour['isDaytime']:
                sunrise_hour = hour
                break
        logging.debug(f"Sunrise hour: {json.dumps(sunrise_hour, indent=2)}")

        # Step 5: Extract the overnight and today forecast periods
        # These are typically the first two periods in the daily forecast
        overnight = forecast_data["properties"]["periods"][0]
        today = forecast_data["properties"]["periods"][1]
        logging.debug(f"Overnight forecast: {json.dumps(overnight, indent=2)}")
        logging.debug(f"Today forecast: {json.dumps(today, indent=2)}")

        # Step 6: Build and return a dictionary with relevant weather data
        # Includes overnight, sunrise, and today summaries
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
        # Catch any errors and log a message for debugging
        logging.exception(f"Weather fetch error: {e}")
        return None


def get_random_literature(length=1000, padding=2000):
    """
    Retrieve a random excerpt from an English book using the Gutendex API.
    This method avoids unreliable random ID guessing by selecting a random page of results.
    """
    try:
        # Step 1: Select a random page using an exponential distribution
        # This favors lower page numbers but allows for higher ones occasionally
        random_page = int(random.expovariate(0.05)) + 1

        # Step 2: Query Gutendex for English books on the selected page
        logging.info(f"Fetching books from Gutendex page {random_page}...")
        api_url = f"https://gutendex.com/books/?languages=en&page={random_page}"
        response = requests.get(api_url)

        # Step 3: Check for successful API response
        if response.status_code != 200:
            logging.error(f"Gutendex API error: {response.status_code}")
            return None

        # Step 4: Parse the book list from the API response
        data = response.json()
        books = data.get('results', [])
        logging.info(f"Found {len(books)} books on page {random_page}.")
        # logging.debug(f"Books data: {json.dumps(books, indent=2)}") --- IGNORE ---

        # Step 5: If no books found, abort
        if not books:
            return None

        # Step 6: Pick a random book from the page
        book = random.choice(books)
        # Step 7: Get available text formats for the book
        formats = book.get('formats', {})
        book_id = book['id']

        # Step 8: Look for a plain text format URL
        text_url = (formats.get('text/plain; charset=utf-8') or 
                    formats.get('text/plain; charset=us-ascii') or
                    formats.get('text/plain'))
        
        # Step 9: If no plain text format is available, abort
        if not text_url:
            logging.warning(f"No plain text format available for book ID: {book_id}")
            return None
        
        logging.debug(f"Selected book ID {book_id} with text URL: {text_url}")

        # Step 10: Fetch the book's plain text content
        logging.info(f"Fetching book content of book...")
        text_response = requests.get(text_url, timeout=10)
        if text_response.status_code != 200:
            logging.error(f"Failed to fetch text from {text_url}")
            return None

        text = text_response.text

        # Step 11: Extract book metadata
        title = book['title']
        authors = book.get('authors', []) # Handle author data safely
        if authors and isinstance(authors[0], dict):
            author = {
                'name': authors[0].get('name', 'Unknown'),
                'birth_year': authors[0].get('birth_year'),
                'death_year': authors[0].get('death_year')
            }
        else:
            # Fallback if author is malformed
            author = {
                'name': str(authors[0]) if authors else 'Unknown',
                'birth_year': None,
                'death_year': None
            }

        # Step 12: Remove Project Gutenberg header if present
        debugging_info = f"Trimming text for excerpt..."
        start_match = re.search(r'\*\*\* START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*', text)
        if start_match:
            text = text[start_match.end():]

        # Step 13: Remove Project Gutenberg footer if present
        end_match = re.search(r'\*\*\* END OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*', text)
        if end_match:
            text = text[:end_match.start()]

        # Step 14: Ensure text is long enough for padding and excerpt
        if len(text) < padding * 2 + length:
            logging.warning(f"Book text too short after trimming: {len(text)} characters")
            return None
        
        # Step 15: Remove padding from start and end to avoid headers/footers
        text = text[padding:-padding]

        # Step 16: Select a random excerpt of the desired length
        start_pos = random.randint(0, len(text) - length)
        excerpt = text[start_pos:start_pos + length].strip()

        # Step 17: Trim excerpt to nearest spaces to avoid partial words
        first_space = excerpt.find(' ')
        last_space = excerpt.rfind(' ')

        if first_space > 0 and last_space > first_space:
            excerpt = excerpt[first_space + 1:last_space]

        # Step 18: Return the excerpt along with book metadata
        return {
            "title": title,
            "author": author,
            "excerpt": excerpt
        }

    except Exception as e:
        # Catch any errors and log a message for debugging
        logging.exception(f"Literature error: {e}")
        return None


def send_ollama_request(prompt):
    """
    Send a prompt to the Ollama API and return the response text.
    Returns the response string, or None on failure.
    """
    # prepare payload for Ollama API
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    # send request to Ollama API
    logging.info(f"Sending request to Ollama model {MODEL}...")
    response = requests.post(OLLAMA_BASE + "/api/generate", json=payload)
    # check for successful response
    if response.status_code != 200:
        logging.error(f"Ollama API error: {response.status_code}")
        return None
    
    return response.json()['response']


def format_weather(weather_data):
    """
    Format weather data into human-readable strings.
    Returns dict with overnight, sunrise, and today formatted strings.
    """
    overnight = f"Overnight: {weather_data['overnight']['description']} {weather_data['overnight']['precipitation']}% chance of precipitation."

    sunrise = f"Sunrise (NOW): {weather_data['sunrise']['temperature']}°F, {weather_data['sunrise']['conditions']}, {weather_data['sunrise']['humidity']}% humidity, dewpoint {weather_data['sunrise']['dewpoint']:.2f}°C, wind {weather_data['sunrise']['windSpeed']} from {weather_data['sunrise']['windDirection']}, {weather_data['sunrise']['precipitation']}% chance of precipitation."

    today = f"Today ({weather_data['today']['dayOfWeek']}): {weather_data['today']['description']} {weather_data['today']['precipitation']}% chance of precipitation."

    return {
        'overnight': overnight,
        'sunrise': sunrise,
        'today': today
    }


def format_literature(literature_data):
    """
    Format literature data into a human-readable string.
    Returns formatted string with title, author info, and excerpt.
    """
    author_info = literature_data['author']['name']
    if literature_data['author']['birth_year'] and literature_data['author']['death_year']:
        author_info += f" ({literature_data['author']['birth_year']}-{literature_data['author']['death_year']})"

    return f'Literature excerpt: "{literature_data["title"]}" by {author_info}:\n{literature_data["excerpt"]}'

