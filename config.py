import os

# Load .env file if present
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

# API Keys - Load from environment
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
PEXELS_API_KEY     = os.getenv("PEXELS_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Voice Settings
VOICE = "en-US-ChristopherNeural"

# Directory Structure
OUTPUT_DIR = "output"
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# --- VIDEO RENDER SETTINGS ---
VIDEO_WIDTH  = 1920
VIDEO_HEIGHT = 720
DEFAULT_PRESET  = "ultrafast"
DEFAULT_BITRATE = "8000k"
FPS = 24

# --- TRANSITION SETTINGS ---
TRANSITIONS_ENABLED_DEFAULT  = True
TRANSITION_DURATION_DEFAULT  = 0.35