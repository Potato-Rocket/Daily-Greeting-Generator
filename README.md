# Daily Greeting Generator

An automated wake-up system that generates daily, personalized morning greeting messages by combining multiple data sources through a multi-stage LLM pipeline. The greeting is rendered to audio via Piper TTS and served through a Flask web app with a built-in viewer. Built with the aid of Claude Code, albeit with strong human supervision. Later revised and improved manually.

While a simple recitation of the weather conditions as well as the day's obligations might be enough for some, others might prefer to begin their day with a bit more whimsy and unexpectedness.

### Pipeline

1. **Weather** — Fetch from weather.gov API
2. **Literature Validation** — Select random book from Gutendex API, use LLM to evaluate potential of random excerpt (max 5 attempts)
3. **Album Selection** — Select 1 of 5 random albums based on how it pairs with literature excerpt (using Ollama LLM)
4. **Album Art Analysis** — Get album cover art and generate text description (using LLM vision model)
5. **Synthesis** — Compose morning greeting based on the weather, literature excerpt, and album info (using LLM)
6. **TTS** — Generate audio with Piper TTS (random voice selection)

### Data Sources

1. **Weather data** from weather.gov API (overnight, sunrise, and daily forecasts)
2. **Literary excerpts** from random books via Gutendex API (Project Gutenberg)
3. **Music metadata** from Navidrome server (selects 1 of 5 random albums, fetches details and describes album art for chosen album)

### Web UI

The Flask app includes a viewer at `/view/<date>` for browsing past greetings. It shows the greeting text, album cover art, audio player, and collapsible pipeline/execution logs, with a sidebar for navigating between dates.

### Dependencies

- Access to an Ollama server instance with text and vision models available
- Access to a music server implementing the Subsonic API (e.g. Navidrome)

If any external API requests fail, the system will degrade gracefully and attempt to format the daily greeting prompt without the missing sources.

## Setup

### Docker (recommended)

```bash
cp config.yaml.example config.yaml   # Edit with your settings
docker compose up --build
```

The container exposes port 5000. Config is mounted at `/config/`, output data at `/data/`, and Piper voice models at `/models/` (a default voice is bundled during the image build).

### Local development

```bash
pip install -r requirements.txt
cp config.yaml.example config.yaml   # Edit with your settings
python cli.py                        # Run pipeline once (loads .env)
python main.py                       # Start Flask server on port 5000
```

### Release

```bash
./release.sh    # Builds, tags, and pushes the Docker image
```

## Configuration

Copy `config.yaml.example` to `config.yaml` and customize:

**weather** — `lat`, `lon` (coordinates for forecasts), `user_agent` (identifier for weather.gov requests)

**ollama** — `host` (server URL), `text_model` (e.g. `mistral:7b`), `multimodal_model` (e.g. `llava:7b`)

**navidrome** — `base_url`, `username`, `password`, `client_name`

**greeting** — `min_length`, `q1_length`, `mean_length` (log-normal word count distribution parameters for greeting generation)

**literature** — `length` (excerpt length in characters), `padding` (buffer to avoid front/endmatter)

**piper** — `voice` (`random` or specific voice name), `length_scale`, `noise_scale`, `noise_w_scale`

## API

The Flask server (`main.py`) exposes a JSON API alongside the web viewer.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dates` | List available dates (newest first) |
| `POST` | `/api/generate` | Trigger a pipeline run. Returns `409` if one is already in progress |
| `GET` | `/api/greeting?date=<date>&fallback=<mode>` | Greeting data as JSON. Fallback mode: `first`, `last`, `random`, or `fail` (default) |
| `GET` | `/api/audio/<date>` | WAV audio file |
| `GET` | `/api/coverart/<date>` | Album cover art JPEG |

The web viewer is at `/view/<date>` (or `/` to redirect to the most recent date). It shows dates with partial data (e.g. failed runs) alongside complete ones, with missing content noted inline.

## Monitoring

```bash
# View today's log
tail -f data/$(date +%Y-%m-%d)/log_$(date +%Y-%m-%d).txt

# View today's pipeline trace (LLM prompts/responses)
less data/$(date +%Y-%m-%d)/pipeline_$(date +%Y-%m-%d).txt
```

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
