# Daily Greeting Generator

An automated wake-up system that generates personalized morning messages by combining multiple data sources through a multi-stage LLM pipeline, then delivers them via text-to-speech at sunrise. Built with the aid of Claude Code, albeit with strong human supervision. Later revised and improved manually.

### Structure

This project is divided into three separate modules, each of which can function independently of the other two:

- **Greeting Generator**, the Python script which makes the required API requests, runs the LLM and TTS pipeline, then sends the generated greeting to the playback server. Should be scheduled as an early morning cron job on a machine with GPU resources for TTS acceleration.
- **Greeting Playback**, the Python server which recieves the generated greeting, calculates the next sunrise, and plays the morning wake up call on schedule. Should be running on a machine with audio output.
- **Notifications**, a simple Python script which plays back a chime of a random tune. Should be set up on the same machine as the greeting playback server.

The core of the system lies in the generator script. In future iterations, the greeting playback and notifications modules will likely be replaced with Home Assistant automation.

### Dependencies

- Access to an Ollama server instance with visual and text-only models available.
- Access to a music server implementing the Subsonic API. I highly recommend Navidrome for its simplicity.
- An instance of an mpc compatible music playback server running on the same machine as the greeting playback server and the notifications script.

## Greeting Generator

### Data Sources
1. **Weather data** from weather.gov API (overnight, sunrise, and daily forecasts)
2. **Literary excerpts** from random books via Gutendex API (Project Gutenberg)
3. **Music metadata** from Navidrome server (selects 1 of 5 random albums, fetches details for chosen album)

### Generation Pipeline

1. **Weather** - Fetch from weather.gov API
2. **Literature Validation** - Get random excerpt (max 5 attempts, evaluate "interesting material")
4. **Album Selection** - Choose 1 from 5 random albums (pairs with literature or standalone)
5. **Album Art Analysis** - Check for default cover, analyze custom art with vision model
6. **Synthesis** - Compose greeting with structured REASONING + GREETING output
7. **TTS** - Generate audio with random Coqui XTTS-v2 speaker (GPU-accelerated)
8. **Delivery** - Send to playback server with retry logic
9. **Playback** - Wind chime → greeting → wind chime at sunrise

### Setup

**Run pipeline manually:**
```bash
cd greeting-generator && conda activate coqui && python main.py
```

**Test specific stages:**
```bash
cd greeting-generator
conda activate coqui
# Test synthesis only (uses existing data)
python tests/test_llm.py

# Test TTS synthesis only (uses existing greeting text)
python tests/test_tts.py

# Test audio delivery only (uses existing WAV file)
python tests/test_send.py
```

**Deploy to server:**
```bash
cd greeting-generator && ./deploy.sh  # Copies code and environment.yml, excludes __pycache__
```

**Setup (run once after deployment):**
```bash
cd greeting-generator && ./setup.sh  # Creates conda env, installs deps, sets up 2am cron job
```

**Monitor execution:**
```bash
cd greeting-generator
# View today's log
tail -f data/$(date +%Y-%m-%d)/log_$(date +%Y-%m-%d).txt

# View today's pipeline trace (LLM prompts/responses)
less data/$(date +%Y-%m-%d)/pipeline_$(date +%Y-%m-%d).txt
```
### Configuration

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

**[playback]**
- `server_url` - Playback server endpoint (e.g., `http://192.168.1.36:7000`)


## Greeting Playback

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

## Notifications

**Deploy notification system:**
```bash
cd notifications && ./deploy.sh  # Deploys wind chimes and playback script to FitPC3
```

**Test chime playback:**
```bash
# On FitPC3
python3 /home/oscar/notifications/play_chime.py
```

### Configuration

Copy from `config.ini.example` and customize:

**[server]**
- `port` - Flask API port (default: 7000)

**[location]**
- `lat`, `lon` - Coordinates for sunrise calculation

**[playback]**
- `offset_minutes` - Minutes offset from sunrise (can be negative to play before sunrise)
