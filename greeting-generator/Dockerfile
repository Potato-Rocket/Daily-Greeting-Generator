FROM python:3-slim
WORKDIR /usr/src/app

# Default config file in config directory
COPY config.ini.example /config/config.ini

# Python files
COPY requirements.txt main.py ./
COPY generator/ ./generator/

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Bundle default model for Piper TTS
RUN python -m piper.download_voices --download-dir /models/ en_US-lessac-high

CMD [ "python", "main.py" ]
