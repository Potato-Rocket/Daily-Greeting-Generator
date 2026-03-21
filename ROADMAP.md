# Daily Greeting v2 Roadmap

Each phase ends with something that runs end-to-end.

## Phase 1 — Containerized Generator
Minimum to get off conda and into Docker, keeping everything else the same.
- ~~Swap Coqui for Piper in `tts.py`~~
- ~~Write Dockerfile (`python:3-slim`, bundled Piper voice)~~
- ~~Verify: `docker build && docker run` generates and delivers a greeting~~

## Phase 2 — Flask API
Replace cron-triggered script with persistent service.
- ~~Move pipeline orchestration from `main.py` → `generator/orchestrator.py`~~
- `main.py` becomes Flask server:
  - ~~`POST /generate` — blocking, deduplicated (lock + check)~~
  - `GET /greeting?fallback=fail|last|random` — returns metadata JSON
  - `GET /audio/<date>` — returns WAV
- `cli.py` for local testing, calls same orchestrator
- Update Dockerfile to `EXPOSE` port

## Phase 3 — Publish & Deploy
Replace `deploy.sh` + `scp` with container registry.
- Push to Docker Hub or ghcr.io
- `docker-compose.yml` with env file, config mount, model volume
- `docker pull && docker compose up` on target machine

## Phase 4 — Home Assistant Integration
HA orchestrates scheduling and playback, replacing playback server.
- HA automation: call `/generate` at 2am
  - Should ping ntfy
- At sunrise: call `/greeting?fallback=last`, play audio via media player, queue album
- Retire `check_sunrise.sh` and Flask playback receiver

## Phase 5 — Config Split
Separate infrastructure/secrets from behavioral tuning.
- Env vars: URLs, credentials, coordinates
- Mounted `config.ini`: model names, excerpt length, album count
- Update `config.py` to layer: defaults → config.ini → env vars
- Create `.env.example`, update `config.ini.example`

## Phase 6 — Pipeline improvements
- Switch to using generic OpenAPI with library
- Improve templating, integration with thinking models
- Tweak prompt engineering

## Phase 7 — DataSource Refactor
Standardize source interface for extensibility.
- Base class: `fetch()`, `data`, `format_for_prompt()`, `context_blurb()`
- Migrate weather, literature, album to source classes
- Synthesis loops over active sources
- Each source reads its own `[section]` from config
- Replace raw requests with more reliable library API wrappers where applicable
