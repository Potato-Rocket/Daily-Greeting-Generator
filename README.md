# Daily Greeting Generator

An automated wake-up system that generates daily, personalized morning greeting messages by combining multiple data sources through a multi-stage LLM pipeline. The greeting is rendered to audio via Piper TTS and served through a Flask web app with a built-in viewer. Built with the aid of Claude Code, albeit with strong human supervision. Later revised and improved manually.

While a simple recitation of the weather conditions as well as the day's obligations might be enough for some, others might prefer to begin their day with a bit more whimsy. This script gathers input data from various sources before feeding it all into the LLM prompt, creating more variation and fun, unexpected results between each day's message.

### Pipeline

1. **Weather** — Fetch from weather.gov API
2. **Literature Validation** — Select random book using the Gutendex API, use LLM to evaluate potential of random excerpt (max 5 attempts)
3. **Album Selection** — Select 1 of 5 random albums based on how it pairs with literature excerpt (using LLM)
4. **Album Art Analysis** — Get cover art for selected album and generate text description (using multimodal LLM model)
5. **Synthesis** — Compose morning greeting based on the weather, literature excerpt, and album info (using LLM)
6. **TTS** — Generate audio with Piper TTS (random voice selection)

### Data Sources

1. **Weather data** from weather.gov API (overnight, sunrise, and daily forecasts)
2. **Literary excerpts** from random books via Gutendex API (Project Gutenberg)
3. **Music metadata** from Navidrome server (selects 1 of 5 random albums, fetches details and describes album art for chosen album)

Suggestions for other data sources are welcome! A future refactor making data sources more modular is planned.

### Web UI

The Flask app includes a viewer for browsing past greetings. It shows the greeting text, album cover art, an audio player for the TTS generation, and collapsible pipeline/execution logs, with a sidebar for navigating between dates.

### Dependencies

- Access to an Ollama server instance with text and vision models available. A future refactor for compatibility with all OpenAI API servers is planned.
- Access to a music server implementing the Subsonic API (e.g. Navidrome)

If any external API requests fail, the system will degrade gracefully and attempt to format the daily greeting prompt without the missing sources.

## Configuration

Configuration is split into two layers:

| Layer | File | What goes here |
|---|---|---|
| Secrets & infrastructure | `.env` | URLs, credentials, coordinates — anything deployment-specific or sensitive |
| Behavioral tuning | `config.yaml` | Model names, excerpt lengths, TTS parameters — project-specific but not secret |

Env vars take precedence over `config.yaml`, which takes precedence over built-in defaults. This means you can run without a `config.yaml` if you set the required env vars, or without a `.env` if you put everything in `config.yaml`.

### Env vars (`.env`)

Copy `.env.example` to `.env` and fill in your values:

| Variable | Description |
|---|---|
| `GREETING_WEATHER_LAT` / `GREETING_WEATHER_LON` | Your location for weather.gov |
| `GREETING_OLLAMA_HOST` | Ollama server URL |
| `GREETING_NAVIDROME_URL` | Navidrome server URL |
| `GREETING_NAVIDROME_USER` / `GREETING_NAVIDROME_PASS` | Navidrome credentials |
| `GREETING_BASE_DIR` | Root for `data/` and `models/` (default: `/`) |
| `GREETING_CONFIG_DIR` | Directory containing `config.yaml` (default: `/config/`) |

### Behavioral config (`config.yaml`)

Copy `config.yaml.example` to `config.yaml` and adjust to taste. This file controls model selection, greeting length targets, literature excerpt size, and Piper TTS parameters. It does not need to contain credentials.

## Setup

### Docker Compose

Docker images are available at [Docker Hub](https://hub.docker.com/repository/docker/potatorocket/daily-greeting/general). After installing [Docker](https://docs.docker.com/engine/install/), copy the following to `compose.yml`:

```yaml
services:
  generator:
    image: docker.io/potatorocket/daily-greeting:latest
    container_name: daily-greeting
    volumes:
      - /path/to/data:/data
      - ./config.yaml:/config/config.yaml
      - greeting-models:/models
    env_file:
      - path: .env
        required: false
    ports:
      - "5000:5000"
    restart: unless-stopped

volumes:
  greeting-models:
```

Then fetch the example files, fill them in, and start the service:

```bash
curl -o config.yaml https://raw.githubusercontent.com/Potato-Rocket/Daily-Greeting-Generator/refs/heads/main/config.yaml.example
curl -o .env https://raw.githubusercontent.com/Potato-Rocket/Daily-Greeting-Generator/refs/heads/main/.env.example
# Edit both files with your values
docker compose up -d
```

Your server will be running at `http://localhost:5000`. After editing either config file, restart to apply changes:

```bash
docker compose restart
```

## API

The Flask server (`main.py`) exposes a JSON API alongside the web viewer. Note that dates must be formatted as `YYYY-MM-DD`. Only one greeting will be stored per day. If a second greeting is requested, the data from a previous greeting will be overwritten, though the pipline and execution logs will be appended to.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dates` | List available dates (newest first) |
| `POST` | `/api/generate` | Trigger a pipeline run. Returns `409` if one is already in progress |
| `GET` | `/api/greeting?date=<date>&fallback=<mode>` | Returns reeting data as JSON. Date: `<date>`, `first`, `last`, `random`. Fallback mode: `first`, `last`, `random`, or `fail` (default) |
| `GET` | `/api/audio/<date>` | WAV audio file |
| `GET` | `/api/coverart/<date>` | Album cover art JPEG |

The web viewer is at `/view/<date>` (or `/` to redirect to the most recent date). It shows dates with partial data (e.g. failed runs) alongside complete ones, with missing content noted inline.

## Monitoring

The most convenient way to see logs are in the web viewer or via:

```bash
docker compose logs
```

If those methods are inoperable, the project's data is stored in plaintext and can be inspected directly. This is notably easier if you have mounted the data directory to a local folder.

## Data Layout

Each run produces a date-stamped directory under `data/`:

```
data/{YYYY-MM-DD}/
  data_{date}.json      # Pipeline output (all stages)
  greeting_{date}.txt   # Final greeting text
  greeting_{date}.wav   # Audio file
  book_{date}.txt       # Full book text
  coverart_{date}.jpg   # Album cover art
  log_{date}.txt        # Execution log
  pipeline_{date}.txt   # LLM prompts and responses
```
