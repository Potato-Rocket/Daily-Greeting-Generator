# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daily Greeting is an automated wake-up system that generates personalized morning messages by combining multiple data sources through a multi-stage LLM pipeline, then delivers them via text-to-speech at sunrise.

### Goal
Create urgent, whimsical wake-up messages that stimulate consciousness through creative synthesis of environmental and cultural data.

### Data Sources
1. **Weather data** from weather.gov API (overnight, sunrise, and daily forecasts)
2. **Literary excerpts** from random books via Gutendex API (Project Gutenberg)
3. **Music metadata** from Navidrome server (5 random albums → curated selection)

### LLM Pipeline
1. **Music curation**: Select 1 album from 5 based on pairing with literature excerpt
2. **Synthesis layer**: Extract themes, metaphors, mood, and sensory anchors from weather + literature + music (no wake-up context)
3. **Composition layer**: Transform synthesis output into urgent wake-up message

### Delivery Architecture
- **Generation server** (home server, i7/GTX1650): Runs at 2am daily, generates greeting, renders via Coqui TTS
- **Playback server** (FitPC3 music server): Flask endpoint receives audio, calculates sunrise time
- **Sunrise playback**: Script checks every 5 minutes if within sunrise window (with configurable offset), plays audio through room speakers

## Commands

Run the script:
```bash
python daily_greeting.py
```

## Configuration

The script uses hardcoded configuration at the top of `daily_greeting.py`:

- **Location**: `LAT = 42.2688, LON = -71.8088` - coordinates for weather.gov API
- **Ollama server**: `OLLAMA_BASE = "http://192.168.1.134:11434"` - local Ollama instance
- **Text model**: `MODEL = "llama3.2:3b"` - currently active model (mistral:7b is commented out)
- **Vision model**: `IMAGE_MODEL = "gemma3:4b"` - for album cover art analysis
- **Navidrome server**: `NAVIDROME_BASE = "http://192.168.1.134:4533"` - local Navidrome instance
- **Navidrome credentials**: `NAVIDROME_USER`, `NAVIDROME_PASS`, `NAVIDROME_CLIENT` - authentication for Subsonic API

Update these constants to change location, AI model, or music server.

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

**`get_navidrome_albums(count=5)`** (lines 229-269)
- Calls Navidrome/Subsonic API to fetch random albums
- Uses URL encoding for password authentication
- Returns list of dicts with album ID, name, artist, year, and genres array

**`get_album_details(album_id)`** (lines 272-315)
- Fetches detailed album information including track list and cover art
- Downloads cover art as base64-encoded string
- Returns dict with songs array and coverart (or None if unavailable)

**`send_ollama_request(prompt, keep_alive=5)`** (lines 318-343)
- Sends non-streaming request to local Ollama text model
- `keep_alive` parameter controls model unloading (default 5s, set to 0 to unload immediately)
- Returns generated text response

**`send_ollama_image_request(prompt, image_base64, keep_alive=0)`** (lines 346-373)
- Sends prompt with base64-encoded image to vision model
- Defaults to immediate model unloading to free VRAM
- Returns generated text description

**`format_weather(weather_data)`** (lines 376-389)
- Formats weather dict into human-readable string
- Returns single string with overnight, sunrise, and today forecasts

**`format_literature(literature_data)`** (lines 392-401)
- Formats literature dict into human-readable string
- Includes title, author with birth/death years, and excerpt

**`format_albums(album_data)`** (lines 404-412)
- Formats album list into numbered, human-readable string
- Includes album name, artist, year, and genres for each entry

## Development Roadmap

### Phase 1: Core Pipeline
- [x] Implement Navidrome API integration (authentication + fetch 5 random albums)
- [ ] Create music curation prompt (select 1 album based on literature pairing)
- [ ] Design synthesis layer prompt (extract themes/metaphors/mood from all sources)
- [ ] Design composition layer prompt (convert synthesis to urgent wake-up message)

### Phase 2: Audio Delivery
- [ ] Integrate Coqui TTS container for audio rendering
- [ ] Build Flask endpoint on FitPC3 to receive audio files

### Phase 3: Playback Automation
- [ ] Create sunrise calculation script with configurable offset
- [ ] Write 5-minute interval checker script for playback at sunrise
- [ ] Set up 2am daily cron job for greeting generation pipeline
