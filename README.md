# Daily Greeting Generator

An automated wake-up system that generates daily, personalized morning greeting messages by combining multiple data sources through a multi-stage LLM pipeline. The greeting is then delivered via text-to-speech at sunrise. Built with the aid of Claude Code, albeit with strong human supervision. Later revised and improved manually.

While a simple recitation of the weather conditions as well as the day's obligations might be enough for some, others might prefer to begin their day with a bit more whimsy and unexpectedness.

### Pipeline

1. **Weather** - Fetch from weather.gov API
2. **Literature Validation** - Select random book from Gutendex API, uses LLM to evaluate potential of random excerpt (max 5 attempts)
4. **Album Selection** - Select 1 of 5 random albums based on how it pairs with literature excerpt (using Ollama LLM)
5. **Album Art Analysis** - Get album cover art and generate text description (using LLM)
6. **Synthesis** - Compose morning greeting based on the weather, literature excerpt, and album info (using LLM)
7. **TTS** - Generate audio with random Coqui XTTS-v2 speaker (GPU-accelerated)
8. **Delivery** - Send to Flask playback server with retry logic
9. **Playback** - At dawn, plays a chime, the greeting, another chime, then begins playback of the selected album

### Data Sources

1. **Weather data** from weather.gov API (overnight, sunrise, and daily forecasts)
2. **Literary excerpts** from random books via Gutendex API (Project Gutenberg)
3. **Music metadata** from Navidrome server (selects 1 of 5 random albums, fetches details and describes album art for chosen album)

TODO: Generate and show example

### Modules

This project is divided into three separate modules, each of which can function semi-independently of the other two:

- **Greeting Generator**, the Python script which makes the required API requests, runs the LLM and TTS pipeline, then sends the generated greeting to the playback server. Should be scheduled as an early morning cron job on a machine with GPU resources for TTS acceleration.
- **Greeting Playback**, the Python server which recieves the generated greeting, calculates the next sunrise, and plays the morning wake up call on schedule. Should be running on a machine with audio output.
- **Notifications**, a simple Python script which plays back a chime of a random tune. Should be set up on the same machine as the greeting playback server.

The core of the system lies in the generator script. In future iterations, the greeting playback and notifications modules will likely be replaced with Home Assistant automation.

### Dependencies

- Access to an Ollama server instance with adequate models available.
- Access to a music server implementing the Subsonic API. I highly recommend Navidrome for its simplicity.
- An instance of an mpc compatible music playback server running on the same machine as the greeting playback server and the notifications script.

If any external API requests fail, the system will degrade gracefully and attempt to format the daily greeting prompt without the missing sources.

## Greeting Generator Script

### Setup

**Run pipeline manually:**
```bash
cd greeting-generator && conda activate coqui && python main.py
```

**Test specific stages:**
```bash
cd greeting-generator/tests
conda activate coqui

# Test coverart description only (uses already saved coverart)
python test_album.py $(date +\"%Y-%m-%d\")

# Test album details fetching and coverart description only (uses existing album selection)
python test_album.py $(date +\"%Y-%m-%d\")

# Test synthesis only (using already generated data)
python test_llm.py $(date +\"%Y-%m-%d\")

# Test audio delivery only (uses existing WAV file)
python test_send.py $(date +\"%Y-%m-%d\")

# Test TTS synthesis only (uses existing greeting text)
python test_tts.py $(date +\"%Y-%m-%d\")
```

**Deploy to server:**
```bash
cd greeting-generator && ./deploy.sh user@host-player  # Copies code and environment.yml
```

**Setup (run once after deployment):**
```bash
ssh user@host-server
cd ~/daily-greeting && ./setup.sh  # Creates conda env, installs deps, sets up 2am cron job
```

**Monitor execution:**
```bash
ssh user@host-server
cd daily-greeting

# View today's log
tail -f data/$(date +%Y-%m-%d)/log_$(date +%Y-%m-%d).txt

# View today's pipeline trace (LLM prompts/responses)
less data/$(date +%Y-%m-%d)/pipeline_$(date +%Y-%m-%d).txt

# Listen to today's final generated greeting
aplay data/$(date +%Y-%m-%d)/greeting_$(date +%Y-%m-%d).wav
```

### Configuration

Copy from `config.ini.example` to `config.ini` (`setup.sh` does this automatically) and customize:

**Weather**
- `lat`, `lon` - Coordinates to get weather forecasts for
- `user_agent` - Custom user agent string (can be anything, an email serves well)

**Ollama**
- `base_url` - Ollama server URL
- `model` - Text model (e.g., `mistral:7b`)
- `image_model` - Vision model (e.g., `llava:7b`)

**Navidrome**
- `base_url` - Navidrome server URL
- `username`, `password` - User login
- `client_name` - Something to identify this client (i.e.)

**Literature**
- `length` - Excerpt length in characters
- `padding` - Additional buffer to avoid front/endmatter

**Playback**
- `server_url` - Playback server endpoint (e.g., `http://192.168.1.36:7000`)

## Greeting Playback Server

### Setup

**Deploy to playback server:**
```bash
cd greeting-playback && ./deploy.sh user@host-player
```

**Setup (run once after deployment):**
```bash
ssh user@host-player
cd daily-greeting && ./setup.sh  # Creates venv, installs deps, configures systemd + cron with verification
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

**Test audio manually:**
```bash
aplay -Dplug:default /home/oscar/greeting-playback/data/greeting.wav
```

### Configuration

Copy from `config.ini.example` and customize:

**Server**
- `port` - Flask API port (default: 7000)

**Location**
- `lat`, `lon` - Coordinates for sunrise calculation

**Playback**
- `offset_minutes` - Minutes offset from sunrise (can be negative to play before sunrise)

## Notifications

**Deploy notification system:**
```bash
cd notifications && ./deploy.sh user@host-player # Deploys wind chimes and playback script to FitPC3
```

**Test chime playback:**
```bash
ssh user@host-player
python /home/oscar/notifications/play_chime.py
```
