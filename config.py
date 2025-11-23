"""
Configuration settings for YouTube Video Summarizer.

This module centralizes all path configurations and settings.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "transcriptions.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# Convert to strings for compatibility with existing code
AUDIO_PATH = str(AUDIO_DIR)
DB_PATH_STR = str(DB_PATH)

# Flask settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5001
FLASK_DEBUG = True

# Queue processor settings
QUEUE_MAX_WORKERS = 3  # Number of videos to process in parallel
