FROM python:3-slim
WORKDIR /usr/src/app

# Default config file in config directory
COPY config.yaml.example /config/config.yaml

# Python files
COPY requirements.txt main.py ./
COPY generator/ ./generator/
COPY static/ ./static/
COPY templates/ ./templates/

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Bundle default model for Piper TTS
RUN python -m piper.download_voices --download-dir /models/ en_US-lessac-high

EXPOSE 5000

CMD [ "python", "main.py" ]
