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

### Pipeline Flow

1. **Weather** - Fetch from weather.gov API
2. **Literature Validation** - Validate random excerpt (max 5 attempts, evaluate "interesting material")
3. **Jabberwocky Word Selection** - Generate 3× candidate words, LLM selects subset based on literature style
4. **Album Selection** - Choose 1 from 5 random albums (pairs with literature or standalone)
5. **Album Art Analysis** - Check for default cover, analyze custom art with vision model
6. **Synthesis** - Compose greeting with structured REASONING + GREETING output
7. **TTS** - Generate audio with random Piper voice model
8. **Delivery** - Send to playback server with retry logic
9. **Playback** - Wind chime → greeting → wind chime at sunrise

### Delivery Architecture
- **Generation server** (home server, i7/GTX1650): Runs at 2am daily via cron, generates greeting, renders via Piper TTS, sends to playback server with retry logic
- **Playback server** (FitPC3 music server): Flask service receives audio on port 7000, calculates sunrise time, stores schedule file
- **Sunrise playback**: Bash script (`check_sunrise.sh`) checks every 5 minutes via cron, plays random chime, then greeting through room speakers using `aplay -Dplug:default` for automatic mono-to-stereo conversion, sets volume to 100% before playback, plays another chime after completion
- **Notification system**: Separate `notifications/` module with wind chime sounds and playback script, shared between greeting system and future notification features

## Commands

### Generator (greeting-generator/)

**Run pipeline manually:**
```bash
cd greeting-generator && ./venv/bin/python main.py
```

**Test specific stages:**
```bash
cd greeting-generator
# Test synthesis only (uses existing data)
./venv/bin/python tests/test_llm.py

# Test TTS synthesis only (uses existing greeting text)
./venv/bin/python tests/test_tts.py

# Test audio delivery only (uses existing WAV file)
./venv/bin/python tests/test_send.py
```

**Deploy to server:**
```bash
cd greeting-generator && ./deploy.sh  # Includes TTS models, excludes __pycache__
```

**Setup (run once after deployment):**
```bash
cd greeting-generator && ./setup.sh  # Creates venv, installs deps, sets up 2am cron job
```

**Monitor execution:**
```bash
cd greeting-generator
# View today's log
tail -f data/$(date +%Y-%m-%d)/log_$(date +%Y-%m-%d).txt

# View today's pipeline trace (LLM prompts/responses)
less data/$(date +%Y-%m-%d)/pipeline_$(date +%Y-%m-%d).txt
```

### Playback (greeting-playback/)

**Deploy to playback server:**
```bash
cd greeting-playback && ./deploy.sh
```

**Setup (run once after deployment):**
```bash
cd greeting-playback && ./setup.sh  # Creates venv, installs deps, configures systemd + cron with verification
```

**Check service status:**
```bash
sudo systemctl status greeting.service
sudo systemctl restart greeting.service  # If needed
```

**Monitor logs:**
```bash
# Flask receiver logs
tail -f /home/oscar/greeting-playback/data/receiver.log

# Sunrise checker logs (appears after first greeting received)
tail -f /home/oscar/greeting-playback/data/checker.log

# Verify cron is running
grep CRON /var/log/auth.log | tail -20
```

**Verify playback setup:**
```bash
# Check sunrise schedule
cat /home/oscar/greeting-playback/data/.playback_schedule
date -d @$(cat /home/oscar/greeting-playback/data/.playback_schedule)

# Test audio manually
aplay -Dplug:default /home/oscar/greeting-playback/data/greeting.wav
```

### Notifications (notifications/)

**Deploy notification system:**
```bash
cd notifications && ./deploy.sh  # Deploys wind chimes and playback script to FitPC3
```

**Test chime playback:**
```bash
# On FitPC3
python3 /home/oscar/notifications/play_chime.py
```

## Configuration

### Generator Configuration (`greeting-generator/config.ini`)

Copy from `config.ini.example` and customize:

**[weather]**
- `lat`, `lon` - Coordinates for weather.gov API
- `user_agent` - Custom user agent string

**[ollama]**
- `base_url` - Ollama server URL
- `model` - Text model (e.g., `mistral:7b`)
- `image_model` - Vision model (e.g., `llama3.2-vision:11b`)

**[navidrome]**
- `base_url`, `username`, `password`, `client_name` - Subsonic API credentials

**[literature]**
- `length` - Excerpt length in characters
- `padding` - Additional buffer for excerpt selection

**[composition]**
- `mean_length`, `q1_length`, `min_length` - Greeting length parameters (lognormal distribution)

**[tts]**
- `length_scale` - Speech speed multiplier (>1 slower, <1 faster)

**[playback]**
- `server_url` - Playback server endpoint (e.g., `http://192.168.1.36:7000/greeting`)

### Playback Configuration (`greeting-playback/config.ini`)

Copy from `config.ini.example` and customize:

**[server]**
- `port` - Flask API port (default: 7000)

**[location]**
- `lat`, `lon` - Coordinates for sunrise calculation

**[playback]**
- `offset_minutes` - Minutes offset from sunrise (can be negative to play before sunrise)

## Architecture

### Project Structure

```
├── greeting-generator/                  # Generation server components
│   ├── main.py                          # Main pipeline entry point
│   ├── config.ini                       # Generator configuration (gitignored)
│   ├── config.ini.example               # Generator config template
│   ├── requirements.txt                 # Python dependencies (requests, piper-tts)
│   ├── setup.sh                         # Generator setup script
│   ├── deploy.sh                        # Deploy generator to server
│   │
│   ├── generator/                       # Core pipeline modules
│   │   ├── __init__.py
│   │   ├── config.py                    # Configuration loading and application
│   │   ├── data_sources.py              # External API calls (weather, literature, music)
│   │   ├── formatters.py                # Data formatting for LLM consumption
│   │   ├── llm.py                       # Ollama API interface with model unloading
│   │   ├── pipeline.py                  # Multi-stage pipeline logic
│   │   ├── io_manager.py                # File I/O and logging setup
│   │   ├── tts.py                       # Piper TTS synthesis + playback delivery
│   │   └── jabberwocky.py               # N-gram Markov chain word generator (experimental)
│   │
│   ├── tests/                           # Test files
│   │   ├── test_llm.py
│   │   ├── test_tts.py
│   │   └── test_send.py
│   │
│   ├── data/                            # Pipeline output (gitignored)
│   │   └── YYYY-MM-DD/                  # Dated run directories
│   │       ├── pipeline_YYYY-MM-DD.txt  # LLM prompts and responses
│   │       ├── log_YYYY-MM-DD.txt       # Execution log
│   │       ├── data_YYYY-MM-DD.json     # Structured data from all stages
│   │       ├── greeting_YYYY-MM-DD.txt  # Final greeting text
│   │       ├── greeting_YYYY-MM-DD.wav  # Synthesized audio
│   │       └── coverart_YYYY-MM-DD.jpg  # Album cover (if analyzed)
│   │
│   └── models/                          # TTS models (gitignored, deployed separately)
│       ├── en_US-ryan-high.onnx
│       ├── en_US-ryan-high.onnx.json
│       ├── en_US-lessac-high.onnx
│       ├── en_US-lessac-high.onnx.json
│       └── [other voice models...]
│
├── greeting-playback/                   # Playback server components (FitPC3)
│   ├── receive_greeting.py              # Flask API for receiving audio
│   ├── check_sunrise.sh                 # Sunrise checker script (cron every 5 min)
│   ├── greeting.service                 # Systemd service template for Flask
│   ├── config.ini                       # Playback config (gitignored)
│   ├── config.ini.example               # Playback config template
│   ├── requirements.txt                 # Python dependencies (flask, astral)
│   ├── setup.sh                         # Playback setup script
│   ├── deploy.sh                        # Deploy playback to server
│   │
│   └── data/                            # Playback data (gitignored)
│       ├── greeting.wav                 # Current greeting audio
│       ├── .playback_schedule           # Sunrise epoch timestamp
│       ├── receiver.log                 # Flask receiver logs
│       └── checker.log                  # Sunrise checker logs
│
├── notifications/                       # Shared notification system
│   ├── play_chime.py                    # Random chime playback script
│   ├── deploy.sh                        # Deploy notifications to FitPC3
│   └── resources/
│       └── 38888__iainmccurdy__wind-chimes/
│           ├── [6 wind chime WAV files]
│           └── _readme_and_license.txt
│
└── CLAUDE.md                            # Project documentation (this file)
```


### Key Modules

**`generator/data_sources.py`** - External API Integration
- `get_weather_data()` - Two-step weather.gov API (lat/lon → forecast)
- `get_random_literature(length, padding)` - Gutendex with exponential page distribution
- `get_navidrome_albums(count)` - Fetch random albums from music server
- `get_album_details(album_id)` - Get tracklist and cover art

**`generator/formatters.py`** - LLM-Ready Text Formatting
- `format_weather(weather_data)` - Weather narrative for prompts
- `format_literature(literature_data)` - Title, author, excerpt
- `format_jabberwocky(words)` - Formatted word list for prompts
- `format_albums(album_data)` - Numbered list of album options
- `format_album(album_data)` - Single album with full details

**`generator/llm.py`** - Ollama Interface
- `send_ollama_request(prompt)` - Text generation
- `send_ollama_image_request(prompt, image_base64)` - Vision model
- `unload_all_models()` - Free GPU memory after pipeline completion

**`generator/pipeline.py`** - Multi-Stage Pipeline Logic
- `validate_literature(io_manager, max_attempts)` - Retry logic for suitable excerpts
- `select_words(io_manager, literature, greeting_length)` - Generate + LLM-select jabberwocky words
- `select_album(io_manager, formatted_lit)` - LLM-based album selection with regex parsing
- `analyze_album_art(io_manager, album)` - Default check + vision analysis
- `calculate_greeting_length()` - Lognormal length distribution
- `synthesize_materials(...)` - Dynamic prompt assembly, structured REASONING + GREETING output

**`generator/io_manager.py`** - File Operations
- Context manager for pipeline file lifecycle
- Dated directory structure: `./data/{YYYY-MM-DD}/`
- Files: `pipeline_{date}.txt`, `log_{date}.txt`, `data_{date}.json`, `greeting_{date}.txt`, `greeting_{date}.wav`
- `print_section(title, content)` - Formatted headers for pipeline trace

**`generator/tts.py`** - TTS Synthesis and Delivery
- `synthesize_greeting(text, io_manager)` - Piper TTS audio generation with random voice selection
- `send_to_playback_server(audio_path, album, max_retries)` - HTTP POST audio + album streaming URLs to playback server with retry logic

**`generator/jabberwocky.py`** - Phonetic Word Generation
- `parse_words(book_path)` - Extract and normalize words from text file
- `build_model(wordlist)` - Create N-gram frequency model (2-character context)
- `length_distribution(wordlist)` - Compute weighted length distribution
- `generate_word(model, distribution)` - Generate single pronounceable nonsense word
- `generate_words(io_manager, count)` - Generate multiple jabberwocky words from literature source

**`generator/config.py`** - Configuration Management
- `load_config(base_dir)` - Load INI configuration file from base directory
- `apply_config(config)` - Apply config overrides to module constants

**`greeting-playback/receive_greeting.py`** - Flask Receiver
- `/greeting` endpoint - Accept WAV file + album URLs, calculate today/tomorrow's sunrise, save schedule
- Saves greeting to `data/greeting.wav` (overwrites previous)
- Saves album streaming URLs to `data/song_urls.txt` if provided
- Calculates sunrise epoch time with offset and saves to `data/.playback_schedule`
- Handles wraparound if sunrise has already passed (schedules for tomorrow)

**`greeting-playback/check_sunrise.sh`** - Sunrise Checker
- Runs every 5 minutes via cron
- Reads sunrise time from `data/.playback_schedule`
- Stops any playing media before playback
- Plays random chime, then greeting with `aplay` if past sunrise time
- Plays another chime after greeting completes
- Queues album in mpc (Music Player Client) if `song_urls.txt` exists
- Updates schedule after playback to prevent replays (adds 24 hours)

**`notifications/play_chime.py`** - Notification System
- Selects random wind chime from collection (6 variations)
- Plays with `aplay` with 10-second duration limit
- Shared between greeting system and future notification features

## Development Roadmap

### Phase 1: Core Pipeline ✅
- [x] Implement Navidrome API integration
- [x] Create album selection logic
- [x] Design synthesis layer prompt
- [x] Design composition layer prompt
- [x] Add TTS synthesis with Piper

### Phase 2: Deployment Infrastructure ✅
- [x] Build Flask endpoint on FitPC3
- [x] Create deployment scripts with venv support
- [x] Add configuration system (INI files)
- [x] Implement audio delivery to playback server

### Phase 3: Automation ✅
- [x] Create sunrise calculation script
- [x] Write 5-minute interval checker
- [x] Set up 2am daily cron job
- [x] Configure systemd service for Flask

### Phase 4: Reliability & Testing ✅
- [x] Add retry logic with exponential backoff for audio delivery
- [x] Fix Flask duplicate logging (use app.logger)
- [x] Add test scripts for isolated component testing
- [x] Improve cron job setup with verification
- [x] Add audio volume control and mono-to-stereo conversion
- [x] Switch to append mode for logs (preserve multi-run history)

### Phase 5: Album Playback ✅
- [x] Implement album streaming URL generation via Subsonic API
- [x] Update Flask endpoint to receive and store song URLs
- [x] Switch from mpv to mpc (Music Player Client) for album playback
- [x] Add explicit Ollama model unloading to free GPU memory after pipeline completion
- [x] Configure audio controls to stop any playing media before greeting playback

### Phase 6: Jabberwocky Integration ✅
- [x] Implement N-gram Markov chain word generator
- [x] Add jabberwocky stage to pipeline (word selection from literature)
- [x] Incorporate generated words into synthesis prompt
- [x] Implement graceful failure modes for Navidrome/Gutenberg

### Phase 7: System Refinement (Future)
- [ ] Fix Ollama GPU utilization (currently not using GTX 1650)
- [ ] Fix media-center timezone (currently UTC, should be America/New_York for 2am local time)
- [ ] Set up general-purpose Navidrome/mpc music endpoint on playback server
- [ ] Fine-tune composition prompts based on greeting quality
- [ ] Improve album selection prompt clarity

### Phase 8: Monitoring & Reliability (Future)
- [ ] Add health monitoring (UptimeRobot, Healthchecks.io, or Telegram bot)
- [ ] Alert on pipeline failures or missed runs
- [ ] Build Raspberry Pi e-ink status dashboard (optional, for fun)

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

**Philosophy**: Graceful degradation for optional data sources, hard failure for critical services.

#### Data Source Layer (`data_sources.py`)

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

#### Pipeline Layer (`pipeline.py`)

**Pattern**: Check for None returns and handle gracefully based on criticality

```python
def select_album(io_manager, literature):
    """..."""
    albums = get_navidrome_albums(count=5)

    # Graceful degradation: proceed without album data
    if not albums:
        logging.warning("Navidrome unavailable, skipping album selection")
        return None

    # Continue with album selection...
```

**Criticality Hierarchy**:

| Service | Criticality | Behavior on Failure |
|---------|-------------|---------------------|
| **Ollama** | Critical | Abort pipeline immediately (no greeting without LLM) |
| **Weather** | Semi-critical | Degrade gracefully if possible, warn loudly |
| **Literature** | Optional | Try multiple times (max 5), continue without if all fail |
| **Navidrome** | Optional | Skip album selection/analysis, generate greeting with available data |

**Implementation Guidelines**:
1. **Critical services (Ollama)**: No explicit None checking needed - let exceptions bubble up to `main.py`
2. **Semi-critical services (Weather)**: Check for None, log error, consider continuing with degraded prompt
3. **Optional services (Literature, Navidrome)**: Check for None, log warning, adapt prompt to exclude missing data
4. **Pipeline stages must validate inputs**: Never assume data source succeeded - always check for None before accessing dict keys

**Example - Optional Service Degradation**:
```python
# Stage 3: Album selection (optional)
logging.info("Stage 3: Album selection")
album = select_album(io_manager, literature)

if not album:
    logging.warning("Album selection unavailable, proceeding without music data")
    album = None

# Stage 5: Synthesis adapts to available data
greeting = synthesize_materials(io_manager, weather, literature, album)
```

**Synthesis Layer Adaptation**:
The synthesis stage should build prompts dynamically based on available data:
- If `literature is None`: Omit literature section from prompt
- If `album is None`: Omit album section from prompt
- If both are None but weather exists: Generate weather-only greeting
- If weather is also None: Log critical error and abort (need at least one data source)

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

## Prompt Engineering

**Last Updated**: October 24, 2025

### Design Principles

**1. Structured Output Formats**
- All prompts end with "Respond in the following format exactly:"
- Forces deliberate reasoning before generation
- Enables reliable parsing without fragile regex

**2. Listener Context Awareness**
- Explicitly state what listener can/cannot perceive
- Example: "The listener can see the weather but has NOT seen the literature or album"
- Prevents awkward out-of-context references

**3. Dynamic Prompt Assembly**
- Build prompts conditionally based on available data sources
- Graceful degradation when Navidrome/Gutenberg unavailable
- Never assume all data sources will succeed

### Stage-Specific Patterns

**Literature Validation**
```
Evaluate whether excerpt is "interesting material from which to source literary
style or elements" (not prescriptive themes/mood/imagery list)

Format: REASONING + VERDICT: YES/NO
```

**Jabberwocky Word Selection**
```
Generate 3× target count using N-gram Markov chain from literature
LLM selects subset (~50% of sqrt(greeting_length)) matching literature style
Instruction: "Avoid nonsense words too close to real words"

Format: List of selected words only, transcribed exactly
Fallback: Random selection if parsing fails
```

**Album Selection**
```
Present 5 options as numbered list
With literature: "pairs best with literature (by contrast or complement)"
Without literature: "most interesting for morning wake-up"

Format: REASONING (2-3 sentences) + VERDICT: [number only]
Parse with regex, fallback to random on failure
```

**Album Art Analysis**
```
Two-step process:
1. Default check: "Does this match Navidrome default (blue vinyl)?"
   Format: DESCRIPTION + REASONING + VERDICT: YES/NO

2. Custom art: "Provide detailed, factual description"
   Changed from "including colors, composition, style" (too suggestive)
   Format: 3-5 bullet points, markdown
```

**Synthesis (Core Greeting Generation)**
```
Dynamic assembly pattern:
1. Base instruction: "Compose a motivating morning wake-up call"
2. Conditional data sections (weather/literature/album if available)
3. Listener context statements (what they can/cannot perceive)
4. Style guidance: "Consider distinctive structural/stylistic elements"
5. Jabberwocky integration: "integrate... as naturally as possible"
6. Constraints: word count bounds, impersonal voice

Format: REASONING (analysis + planning) + GREETING (final output)
```

**Key synthesis changes**:
- Removed "FORGET the details" abstraction instruction (too vague)
- Added explicit reasoning section before greeting generation
- Changed from single-shot to think-then-write structure
- "Avoid references too specific or out of context" (clearer than abstract residue)
- "Weave into unified vision. Avoid scattered fragments." (coherence over mystery)

### Format Instruction Evolution

**Old**: "Respond in this exact format strictly:"
**New**: "Respond in the following format exactly:"

Subtle but clearer phrasing - "following format" is more natural than "exact format"

### Length Control

Lognormal distribution with configurable mean/Q1/min:
- `calculate_greeting_length()` returns target word count
- Bounds: `[target - rand(1,10), target + rand(1,10)]` for natural variation
- Jabberwocky count scales with greeting length: `int(0.5 * sqrt(length))`

### Parsing Strategies

1. **Structured formats**: Extract sections with string splitting
2. **Regex patterns**: `VERDICT:\s*(\d+)` for album selection
3. **Validation**: Check extracted values against valid set
4. **Graceful fallbacks**: Random selection when parsing fails
5. **Logging**: Debug invalid LLM output without failing pipeline
