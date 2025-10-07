#!/usr/bin/env python3
import random
import subprocess
from pathlib import Path

# Directory containing your chime sounds
CHIME_DIR = Path(__file__).parent / "resources/38888__iainmccurdy__wind-chimes"

# Check whether the directory exists
if not CHIME_DIR.exists():
    print(f"Directory {CHIME_DIR} does not exist")
    exit(1)

# Get all audio files (adjust extensions as needed)
chimes = list(CHIME_DIR.glob("*.wav"))  # or *.mp3, *.ogg, etc.

if not chimes:
    print(f"No audio files found in {CHIME_DIR}")
    exit(1)

# Select and play a random chime
selected = random.choice(chimes)
print(f"Playing: {selected.name}")
subprocess.run(["aplay", "-d", "10", str(selected)])
