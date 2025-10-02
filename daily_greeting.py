import requests
import json

LAT = 42.2688
LON = -71.8088
WEATHER_GOV_BASE = "https://api.weather.gov"
USER_AGENT = "DailyGreetingYggdrasil/1.0"

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
        points_url = f"{WEATHER_GOV_BASE}/points/{LAT},{LON}"
        points_response = requests.get(points_url, headers={"User-Agent": USER_AGENT})

        # Check if the API call was successful
        if points_response.status_code != 200:
            print(f"Points API error: {points_response.status_code}")
            return None

        # Parse the response to get grid and forecast URLs
        points_data = points_response.json()

        # Step 2: Extract forecast URLs from the points API response
        # These URLs provide daily and hourly forecast data for the location
        forecast_url = points_data["properties"]["forecast"]
        forecast_hourly_url = points_data["properties"]["forecastHourly"]

        # Step 3: Request the actual forecast data from the URLs
        forecast_response = requests.get(forecast_url, headers={"User-Agent": USER_AGENT})
        hourly_response = requests.get(forecast_hourly_url, headers={"User-Agent": USER_AGENT})

        # Check if both forecast API calls were successful
        if forecast_response.status_code != 200 or hourly_response.status_code != 200:
            print(f"Forecast API error")
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

        # Step 5: Extract the overnight and today forecast periods
        # These are typically the first two periods in the daily forecast
        overnight = forecast_data["properties"]["periods"][0]
        today = forecast_data["properties"]["periods"][1]

        # Step 6: Build and return a dictionary with relevant weather data
        # Includes overnight, sunrise, and today summaries
        return {
            "overnight": {
                "dayOfWeek": overnight['name'],
                "temperatureUnit": overnight['temperatureUnit'],
                "precipitation": overnight['probabilityOfPrecipitation'],
                "description": overnight['detailedForecast']
            },
            "sunrise": {
                "temperature": sunrise_hour['temperature'],
                "temperatureUnit": sunrise_hour['temperatureUnit'],
                "humidity": sunrise_hour['relativeHumidity'],
                "dewpoint": sunrise_hour['dewpoint'],
                "windSpeed": sunrise_hour['windSpeed'],
                "windDirection": sunrise_hour['windDirection'],
                "precipitation": sunrise_hour['probabilityOfPrecipitation'],
                "conditions": sunrise_hour['shortForecast']
            },
            "today": {
                "dayOfWeek": today['name'],
                "temperatureUnit": today['temperatureUnit'],
                "precipitation": today['probabilityOfPrecipitation'],
                "description": today['detailedForecast']
            }
        }

    except Exception as e:
        # Catch any errors and print a message for debugging
        print(f"Weather fetch error: {e}")
        return None


def process_weather(data):
    payload = {
        "model": MODEL,
        "prompt": f"It is sunrise right now. Please summarize this weather data:\n{json.dumps(data)}",
        "stream": False
    }

    response = requests.post(OLLAMA_BASE + "/api/generate", json=payload)

    if response.status_code != 200:
            print(f"Ollama API error: {response.status_code}")
            return None
        
    return response.json()['response']


weather = get_weather_data()
print(json.dumps(weather, indent=2))
print(process_weather(weather))