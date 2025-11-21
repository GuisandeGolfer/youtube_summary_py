# YouTube Video Summarizer - Web Application

A simple web application to summarize YouTube videos and save transcriptions to a SQLite database.

## Features

- Single-page web interface
- Download and transcribe YouTube videos
- Generate AI-powered summaries using OpenAI GPT
- Save transcriptions to SQLite database for later vectorization
- Clean, organized code split across logical modules

## Project Structure

```
.
├── app.py                  # Flask web server and routes
├── youtube.py             # YouTube video downloading functions
├── transcription.py       # Audio transcription using OpenAI Whisper
├── summarization.py       # Summary generation using GPT
├── database.py            # SQLite database operations
├── templates/
│   └── index.html        # Web interface
├── prompt.json            # Prompt templates for summarization
├── .env                   # Environment variables (API keys)
└── transcriptions.db      # SQLite database (auto-created)
```

## Setup

### 1. Install uv

Install [uv](https://github.com/astral-sh/uv) if you haven't already:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

### 2. Install Dependencies

Make sure you have ffmpeg installed:

```bash
# Install ffmpeg (macOS)
brew install ffmpeg
```

Then sync the project dependencies with uv:

```bash
uv sync
```

This will create a virtual environment and install all dependencies automatically.

### 3. Set Up Environment Variables

Create a `.env` file in the project root with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

### 4. Run the Application

```bash
uv run python app.py
```

The server will start on `http://localhost:5000`

Alternatively, activate the virtual environment and run directly:

```bash
source .venv/bin/activate
python app.py
```

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Enter a YouTube URL in the input field
3. Click "Process Video"
4. Wait for the process to complete (this may take a few minutes depending on video length)
5. View the summary on the page
6. The transcription is automatically saved to `transcriptions.db`

## Database Schema

The SQLite database contains a `videos` table with the following structure:

```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT,
    video_length INTEGER,
    channel TEXT,
    transcription TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## How It Works

1. **Download** - The YouTube video's audio is downloaded using yt-dlp
2. **Split** - Long audio files are split into ~23-minute segments using ffmpeg
3. **Transcribe** - Each segment is transcribed using OpenAI's Whisper API
4. **Summarize** - The full transcription is summarized using GPT-3.5-turbo
5. **Save** - The transcription and video metadata are saved to SQLite
6. **Display** - The summary is shown on the webpage
7. **Cleanup** - Audio files are automatically deleted after processing

## Quick Reference

```bash
# Install dependencies
uv sync

# Run the app
uv run python app.py

# Add a new dependency
uv add package-name

# Update dependencies
uv lock --upgrade
```

## Notes

- Audio files are automatically cleaned up after transcription
- If a video already exists in the database, it will be updated
- Large videos may take several minutes to process
- You need a valid OpenAI API key with access to Whisper and GPT models
- This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable dependency management
- The `requirements.txt` file is kept for compatibility but `pyproject.toml` is the source of truth
