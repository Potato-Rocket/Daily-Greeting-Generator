FROM python:3-slim
WORKDIR /usr/src/app

# Default config file in config directory
COPY config.yaml.example /config/config.yaml

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies (cached layer — only reruns when pyproject.toml or lockfile changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# App files
COPY main.py ./
COPY generator/ ./generator/
COPY static/ ./static/
COPY templates/ ./templates/

# Bundle default model for Piper TTS
RUN uv run python -m piper.download_voices --download-dir /models/ en_US-lessac-high

EXPOSE 5000

CMD ["uv", "run", "main.py"]
