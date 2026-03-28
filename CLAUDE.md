# Daily Greeting Generator

Flask API that runs a multi-stage LLM pipeline — fetches weather, literature, and music data, synthesizes a personalized wake-up greeting via Ollama, then renders it to audio with Piper TTS.

## Architecture

| Module | Role |
|---|---|
| `main.py` | Flask server (`/generate`, `/greeting`, `/audio/<date>`) |
| `generator/generator.py` | Pipeline runner — orchestrates stages in sequence |
| `generator/pipeline.py` | LLM stages: literature validation, album selection, art analysis, synthesis |
| `generator/data_sources.py` | External API fetchers (weather.gov, Gutendex, Navidrome) |
| `generator/llm.py` | Ollama interface (text + vision) |
| `generator/tts.py` | Piper TTS synthesis with voice fallback |
| `generator/io_manager.py` | File I/O, path computation, logging setup |
| `generator/config.py` | YAML config singleton with typed dataclasses |
| `generator/templates/` | Jinja2 prompt templates (partials prefixed with `_`) |

## Key Patterns

- **Config singleton**: `Config.instance()` returns typed dataclasses loaded from `config.yaml`. Env vars (`GREETING_BASE_DIR`, `GREETING_CONFIG_DIR`) set paths; YAML controls behavior. Re-loaded each generation via `Config.load()`.
- **Path/IO split**: `PathManager` is pure path computation (no side effects). `IOManager` handles file writes and is used as a context manager.
- **Graceful degradation**: Each pipeline stage handles missing data and continues — weather, literature, or music can fail independently without aborting the pipeline.
- **LLM response parsing**: `VERDICT` keyword pattern matching (e.g. `VERDICT: YES`, `VERDICT: 3`).
- **Logging**: Module-level `logging` calls throughout (not per-class loggers). Format: `[HH:MM:SS] LEVEL: message`.

## Data Layout

```
data/{YYYY-MM-DD}/
  data_{date}.json      # Pipeline output (all stages)
  greeting_{date}.txt   # Final text
  greeting_{date}.wav   # Audio
  book_{date}.txt       # Full book text
  coverart_{date}.jpg   # Album art
  log_{date}.txt        # Execution log
  pipeline_{date}.txt   # LLM prompts and responses
```

## Running

- **Docker**: `docker compose up` (see `compose.yml`). Config mounted at `/config/`, data at `/data/`, models at `/models/`.
- **Local**: `python cli.py` (loads `.env` via python-dotenv).
- **Release**: `release.sh` builds, tags, and pushes the Docker image.

## Style Conventions

- `pathlib.Path` throughout, never `os.path`
- Enums for categorical values (`Temperature`, `Mode`)
- f-string logging
- Module docstrings describe purpose; function docstrings use Args/Returns format
- `requests` with module-level `TIMEOUT = 30` for all HTTP calls
