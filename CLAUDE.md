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

**`format_weather(weather_data)`** (lines 246-261)
- Formats weather dict into human-readable strings
- Returns dict with overnight, sunrise, and today formatted strings

**`format_literature(literature_data)`** (lines 264-273)
- Formats literature dict into human-readable string
- Includes title, author with birth/death years, and excerpt

## Development Roadmap

### Phase 1: Core Pipeline
- [ ] Implement Navidrome API integration (authentication + fetch 5 random albums)
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
