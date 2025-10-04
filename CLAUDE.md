# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daily Greeting is a Python script that generates personalized morning wake-up messages by combining:
1. **Weather data** from weather.gov API (overnight, sunrise, and daily forecasts)
2. **Literary excerpts** from random books via the Gutendex API (Project Gutenberg)
3. **AI text generation** using a local Ollama instance to create atmospheric wake-up messages

The script fetches weather conditions, pulls a random literature excerpt, and uses an LLM to synthesize these into a creative morning greeting.

## Commands

Run the script:
```bash
python daily_greeting.py
```

## Configuration

The script uses hardcoded configuration at the top of `daily_greeting.py`:

- **Location**: `LAT = 42.2688, LON = -71.8088` - coordinates for weather.gov API
- **Ollama server**: `OLLAMA_BASE = "http://192.168.1.134:11434"` - local Ollama instance
- **Model**: `MODEL = "mistral:7b"` - currently active model (llama3.2:3b is commented out)

Update these constants to change location or AI model.

## Architecture

### Main Flow (bottom of file)
1. Fetch random literature excerpt via `get_random_literature()`
2. Fetch weather data via `get_weather_data()`
3. Create prompt via `create_prompt(weather_data, literature_data)`
4. Generate greeting via `send_ollama_request(prompt)`

### Key Functions

**`get_weather_data()`** (lines 18-102)
- Two-step weather.gov API call: converts lat/lon to grid coordinates, then fetches forecast
- Returns dict with overnight, sunrise (first daytime hour), and today forecasts
- Includes temperature, humidity, dewpoint, wind, precipitation data

**`get_random_literature(length=1000, padding=2000)`** (lines 105-219)
- Uses exponential distribution to select random Gutendex page
- Fetches random book, extracts plain text format
- Strips Project Gutenberg headers/footers using regex
- Returns random excerpt with title and author metadata

**`send_ollama_request(prompt)`** (lines 222-242)
- Sends non-streaming request to local Ollama API
- Returns generated text response

**`create_prompt(weather_data, literature_data)`** (lines 245-277)
- Formats weather and literature into a structured prompt
- Uses lognormal distribution for variable message length (around 140 words)
- Instructs model to create atmospheric, metaphorical wake-up message
