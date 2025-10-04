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

The pipeline uses a multi-stage approach with validation and filtering:

#### Stage 1: Literature Validation (max 5 attempts)
- Fetch random literature excerpt
- Evaluate suitability for themes, tone, imagery, metaphor, or sensory details
- Prompt format: `REASONING` + `VERDICT: YES/NO`
- Continue until suitable excerpt found or max attempts reached

#### Stage 2: Album Selection (from 5 random albums)
- Fetch 5 random albums from Navidrome
- Select 1 album that pairs best with literature (by contrast or complement)
- Prompt format: `REASONING` (2-3 sentences considering options) + `VERDICT: 1-5`
- Parse verdict with regex fallback to random selection on failure

#### Stage 3: Album Art Analysis (if available)
- Fetch album details (tracklist + cover art)
- Check if cover art is Navidrome default (blue vinyl with "Navidrome" text)
  - Prompt format: `DESCRIPTION` + `REASONING` + `VERDICT: YES/NO`
- If not default, analyze cover art with vision model
  - Generate 3-5 bullet points describing colors, composition, style
  - Store analysis text (discard base64 image)

#### Stage 4: Synthesis Layer
- Extract abstract patterns from all inputs (weather + literature + album)
- **Critical**: No wake-up context at this stage, only raw materials
- Prompt format outputs:
  - `THEMES`: 3-5 abstract concepts (vastness, transition, isolation, harmony)
  - `MOOD`: 2-4 mood descriptors
  - `SENSORY ANCHORS`: 3-5 concrete sensory details (colors, textures, temperatures, sounds)
  - `SYMBOLIC ELEMENTS`: 2-4 symbols/images/metaphors for reinterpretation

#### Stage 5: Composition Layer (TODO)
- Transform synthesis output into urgent wake-up message
- Add wake-up context only at this final stage

### Delivery Architecture
- **Generation server** (home server, i7/GTX1650): Runs at 2am daily, generates greeting, renders via Coqui TTS
- **Playback server** (FitPC3 music server): Flask endpoint receives audio, calculates sunrise time
- **Sunrise playback**: Script checks every 5 minutes if within sunrise window (with configurable offset), plays audio through room speakers

## Commands

Run the pipeline:
```bash
python run_pipeline.py
```

Legacy script (deprecated, for reference only):
```bash
python daily_greeting.py  # DO NOT USE - see generator/ module instead
```

## Configuration

Configuration is defined in module constants:

**Weather** (`generator/data_sources.py`):
- `LAT`, `LON` - Coordinates for weather.gov API (currently: Worcester, MA area)
- `USER_AGENT` - Custom user agent string for weather.gov

**Ollama** (`generator/llm.py`):
- `OLLAMA_BASE` - Ollama server URL (default: `http://192.168.1.134:11434`)
- `MODEL` - Text model (currently: `mistral:7b`)
- `IMAGE_MODEL` - Vision model (currently: `gemma3:4b`)

**Navidrome** (`generator/data_sources.py`):
- `NAVIDROME_BASE`, `NAVIDROME_USER`, `NAVIDROME_PASS`, `NAVIDROME_CLIENT` - Subsonic API credentials

## Architecture

### Module Structure

```
├── run_pipeline.py           # Main entry point
├── daily_greeting.py          # DEPRECATED - legacy reference code
└── generator/
    ├── __init__.py
    ├── data_sources.py        # External API calls (weather, literature, music)
    ├── formatters.py          # Data formatting for LLM consumption
    ├── llm.py                 # Ollama API interface
    ├── pipeline.py            # Multi-stage pipeline logic
    └── io_manager.py          # File I/O and logging setup
```

### Main Pipeline Flow (`run_pipeline.py`)

1. **Initialize** - Create IOManager, setup logging
2. **Stage 1: Weather** - Fetch from weather.gov API
3. **Stage 2: Literature** - Validate random excerpt (max 5 attempts)
4. **Stage 3: Album Selection** - Choose 1 from 5 random albums
5. **Stage 4: Album Art** - Analyze cover art with vision model
6. **Stage 5: Synthesis** - Extract themes/mood/sensory elements
7. **Stage 6: Composition** - Transform to wake-up message (TODO)

### Key Modules

**`generator/data_sources.py`** - External API Integration
- `get_weather_data()` - Two-step weather.gov API (lat/lon → forecast)
- `get_random_literature(length, padding)` - Gutendex with exponential page distribution
- `get_navidrome_albums(count)` - Fetch random albums from music server
- `get_album_details(album_id)` - Get tracklist and cover art

**`generator/formatters.py`** - LLM-Ready Text Formatting
- `format_weather(weather_data)` - Weather narrative for prompts
- `format_literature(literature_data)` - Title, author, excerpt
- `format_albums(album_data)` - Numbered list of album options
- `format_album(album_data)` - Single album with full details

**`generator/llm.py`** - Ollama Interface
- `send_ollama_request(prompt)` - Text generation
- `send_ollama_image_request(prompt, image_base64)` - Vision model

**`generator/pipeline.py`** - Multi-Stage Pipeline Logic
- `validate_literature(io_manager, max_attempts)` - Retry logic for suitable excerpts
- `select_album(io_manager, formatted_lit)` - LLM-based album selection with regex parsing
- `analyze_album_art(io_manager, album)` - Default check + vision analysis
- `synthesize_materials(...)` - Extract abstract themes/mood
- `compose_greeting(...)` - Final composition (TODO)

**`generator/io_manager.py`** - File Operations
- Context manager for pipeline file lifecycle
- Dated directory structure: `./tmp/{YYYY-MM-DD}/`
- Files: `pipeline_{date}.txt`, `log_{date}.txt`, `data_{date}.json`, `greeting_{date}.txt`
- `print_section(title, content)` - Formatted headers for pipeline trace

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

## Coding Standards

**Last Updated**: October 4, 2025

These standards ensure consistency across the codebase. Follow them for all new code and when refactoring existing code.

### 1. Logging Levels

**Purpose**: Create narrative at different zoom levels for debugging and monitoring.

| Level | Usage | Examples |
|-------|-------|----------|
| `DEBUG` | Raw data dumps, iteration counters, detailed progress | JSON payloads, "Attempt 3/5", URL values |
| `INFO` | Major milestones, stage transitions, successful completions | "Stage 1: Weather data", "Album details fetched successfully" |
| `WARNING` | Non-critical issues, fallbacks, retries | "Using random fallback", "No cover art available" |
| `ERROR` | Critical failures requiring attention | "Navidrome API returned status 500", "Pipeline aborted" |
| `EXCEPTION` | All exceptions with stack traces | Use `logging.exception()` in except blocks |

**Style Rules**:
- Start INFO messages with context: "Fetching weather data...", not "Fetching..."
- Use sentence case, no trailing periods except for multi-sentence messages
- Include relevant IDs/counts in messages: `f"Fetching album details (ID: {album_id})"`
- Log completion: Pair start/end INFO messages for long operations

**Examples**:
```python
logging.info("Fetching weather data from weather.gov API")  # Start
logging.debug(f"Forecast URLs: {forecast_url}, {hourly_url}")  # Details
logging.info("Weather data fetched successfully")  # Complete

logging.warning("No cover art available, skipping analysis")  # Fallback
logging.error(f"Ollama API returned status {response.status_code}")  # Failure
```

### 2. Output Mechanisms

Two separate output streams with distinct purposes:

**Execution Log** (`log_{date}.txt`):
- Configured by `setup_logging()` in `io_manager.py`
- Uses Python `logging` module
- Timestamped entries: `[HH:MM:SS] LEVEL: message`
- Purpose: Track execution progress, debugging, monitoring

**Pipeline Trace** (`pipeline_{date}.txt`):
- Managed by `io_manager.print_section()`
- Captures LLM prompts and responses
- Formatted with section headers (50-char separator lines)
- Purpose: Inspect LLM interactions, prompt engineering, reproducibility

**Console**: Shows both simultaneously (execution log + pipeline sections)

**DO NOT** use `logging` for LLM prompts/responses. **DO NOT** use `print_section()` for status updates.

### 3. Docstring Format

**Standard**: Google-style with Args/Returns sections

```python
def function_name(param1, param2=default):
    """
    Brief one-line summary ending with period.

    Optional extended description explaining context, approach, or rationale.
    Can span multiple paragraphs if needed.

    Args:
        param1: Description of param1
        param2: Description of param2 with default behavior

    Returns:
        type: Description of return value, or None on failure
    """
```

**Requirements**:
- All functions must have docstrings
- Include `Args:` section if function takes parameters
- Include `Returns:` section for all functions (even if returns None)
- One blank line between sections
- Return type format: `type: description` (e.g., `dict: Weather data with 'overnight', 'sunrise', 'today' keys`)

**Bad Examples**:
```python
# Missing Returns section
def get_weather():
    """Get weather data."""

# Inline Args (don't do this)
def get_weather():
    """
    Get weather data.
    Returns dict with weather or None.
    """
```

### 4. Inline Comments

**Philosophy**: Document WHY, not WHAT. Explain reasoning, not mechanics.

**Good**:
```python
# Select random page using exponential distribution (favors lower page numbers)
random_page = int(random.expovariate(0.05)) + 1

# Convert latitude and longitude to NWS grid coordinates
points_url = f"https://api.weather.gov/points/{LAT},{LON}"
```

**Bad** (redundant, self-evident):
```python
# Increment the counter
counter += 1

# Call the API
response = requests.get(url)
```

**Rules**:
- Place comments **before** the code block they describe
- Use sentence fragments (no trailing period unless multi-sentence)
- Group related operations under single comment
- No comments for self-explanatory code
- Use comments for non-obvious algorithms, workarounds, or design decisions

### 5. Pipeline Section Headers

**Format**: `{STAGE} - {TYPE}` where TYPE is `PROMPT` or `RESPONSE`

**Standard Headers**:
- `LITERATURE VALIDATION - PROMPT` / `LITERATURE VALIDATION - RESPONSE`
- `ALBUM SELECTION - PROMPT` / `ALBUM SELECTION - RESPONSE`
- `ALBUM ART - DEFAULT CHECK PROMPT` / `ALBUM ART - DEFAULT CHECK RESPONSE`
- `ALBUM ART - ANALYSIS PROMPT` / `ALBUM ART - ANALYSIS RESPONSE`
- `SYNTHESIS - PROMPT` / `SYNTHESIS - RESPONSE`
- `COMPOSITION - PROMPT` / `COMPOSITION - RESPONSE` (future)

**Usage**:
```python
io_manager.print_section("SYNTHESIS - PROMPT", synthesis_prompt)
synthesis = send_ollama_request(synthesis_prompt)
io_manager.print_section("SYNTHESIS - RESPONSE", synthesis)
```

**Benefits**: Scannable, grepable, consistent hierarchy

### 6. Error Handling

**Pattern**: Try/except with `logging.exception()` for all external API calls

```python
def get_weather_data():
    """..."""
    try:
        logging.info("Fetching weather data from weather.gov API")
        # API calls here
        logging.info("Weather data fetched successfully")
        return data
    except Exception as e:
        logging.exception(f"Weather fetch error: {e}")
        return None
```

**Rules**:
- Always catch exceptions in data source functions
- Use `logging.exception()` to capture stack traces
- Return `None` on failure (caller handles None checking)
- Log specific error context in exception message
- Never silently swallow exceptions

### 7. File Organization

**Imports**: Standard library → Third-party → Local modules
```python
import json
import logging
from pathlib import Path
from datetime import datetime

import requests

from .llm import MODEL, IMAGE_MODEL
```

**Constants**: Module-level, UPPER_SNAKE_CASE, grouped by purpose
```python
# Weather.gov API configuration
LAT = 42.2688
LON = -71.8088
USER_AGENT = "DailyGreetingYggdrasil/1.0"

# Navidrome server configuration
NAVIDROME_BASE = "http://192.168.1.134:4533"
```

**Functions**: Logical order (data fetching → formatting → pipeline stages)
