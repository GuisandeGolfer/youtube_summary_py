# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Video Summarizer is a Flask web application that downloads YouTube videos, transcribes them using OpenAI Whisper, and generates AI summaries using OpenAI GPT. It features a queue system for batch processing multiple videos in parallel.

## Development Commands

### Environment Setup
```bash
# Install dependencies (uses uv for fast dependency management)
uv sync

# Run the Flask web server
uv run python app.py

# Alternative: activate venv and run directly
source .venv/bin/activate
python app.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_database.py

# Run specific test
pytest tests/test_database.py::TestSaveTranscriptionToDB::test_save_new_video_with_summary -v

# Run tests matching a pattern
pytest -k summary

# Stop at first failure
pytest -x

# Run with coverage
pytest --cov=. --cov-report=html
```

### CLI Tools
```bash
# Query and retrieve transcriptions interactively (requires fzf)
scripts/transcript_viewer.py

# Get summary directly
scripts/transcript_viewer.py --summary

# Copy result to clipboard
scripts/transcript_viewer.py --clipboard

# Database migration utility
scripts/migrate_database.py
```

## Architecture

### Core Processing Pipeline

The application follows a multi-stage pipeline for video processing:

1. **Download** (`src/core/youtube.py`): Uses yt-dlp to download audio from YouTube videos
2. **Split** (embedded in transcription): Long audio files are automatically split into ~23-minute segments using ffmpeg
3. **Transcribe** (`src/core/transcription.py`): Each segment is transcribed using OpenAI Whisper API
4. **Summarize** (`src/core/summarization.py`): Full transcription is summarized using OpenAI GPT
5. **Store** (`src/core/database.py`): Metadata, transcription, and summary saved to SQLite
6. **Cleanup**: Audio segments are automatically deleted after processing

### Queue System

The queue system (`src/queue/`) enables batch processing of multiple videos:

- **VideoQueue** (`manager.py`): Thread-safe queue data structure that tracks video processing status (PENDING → DOWNLOADING → TRANSCRIBING → SUMMARIZING → COMPLETED/FAILED)
- **QueueProcessor** (`processor.py`): Parallel processor using ThreadPoolExecutor (default: 3 workers) to process multiple videos concurrently
- **ActionType enum**: Videos can be queued for either PROCESS (transcribe + summarize) or DOWNLOAD (download only)

The queue is managed via Flask API routes in `app.py` (`/queue/add`, `/queue/start`, `/queue/list`, `/queue/remove`, `/queue/clear`).

### Configuration

All paths and settings are centralized in `config.py`:
- `AUDIO_PATH`: Temporary audio storage (`data/audio/`)
- `DOWNLOADS_PATH`: Video downloads (`downloads/`)
- `DB_PATH`: SQLite database (`data/transcriptions.db`)
- `QUEUE_MAX_WORKERS`: Parallel processing limit (default: 3)
- `FLASK_PORT`: Default 5001

### Flask Routes

**Single Video Processing:**
- `POST /process`: Download, transcribe, and summarize a single video
- `POST /download`: Download video without processing

**Queue Management:**
- `POST /queue/add`: Add video to processing queue
- `POST /queue/start`: Begin parallel queue processing (runs in background thread)
- `GET /queue/list`: Get current queue state and stats
- `DELETE /queue/remove/<item_id>`: Remove pending item from queue
- `POST /queue/clear`: Clear all pending items

### Database Schema

SQLite database (`data/transcriptions.db`) with `videos` table:
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT,
    video_length INTEGER,
    channel TEXT,
    transcription TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Prompt Templates

Summarization prompts are defined in `prompt.json` with three variants:
- `normal`: Concise summary with URL embedded
- `detailed`: Summary with examples and context from transcript
- `latin`: Summary translated to Latin (experimental)

## Important Implementation Details

### Audio Segmentation
Long videos are automatically split into segments to stay within OpenAI Whisper's file size limits. The splitting logic is in `src/core/transcription.py` and uses ffmpeg. Audio segments are stored temporarily in `data/audio/` and deleted after successful transcription.

### Parallel Processing
The queue processor uses ThreadPoolExecutor to process multiple videos simultaneously. The number of concurrent workers is configurable via `QUEUE_MAX_WORKERS` in `config.py`. Each worker processes one video through the entire pipeline (download → transcribe → summarize → save).

### Error Handling
Queue items track their status and error messages. If a video fails processing, its status is set to FAILED and the error message is stored in the `error` field for debugging.

### Testing Strategy
The test suite uses pytest with mocking for external API calls (OpenAI, yt-dlp). Tests are organized by module and marked with categories (unit, integration, slow, api). See `pytest.ini` for configuration.

## Dependencies

- **yt-dlp**: YouTube video downloading
- **ffmpeg**: Audio processing and segmentation (must be installed separately)
- **OpenAI API**: Whisper (transcription) and GPT (summarization)
- **Flask**: Web server
- **fzf**: Required for CLI transcript viewer tool (install via `brew install fzf`)

## Environment Variables

Required in `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

## Common Development Patterns

### Adding a New Processing Step
1. Create function in appropriate `src/core/` module
2. Update `src/core/__init__.py` to export the function
3. Integrate into the pipeline in `app.py` (single processing) and `src/queue/processor.py` (queue processing)
4. Add corresponding tests in `tests/`

### Modifying Queue Behavior
The queue system is split into data structures (`manager.py`) and processing logic (`processor.py`). Status updates are handled by setting `item.status`, `item.progress`, and `item.current_step` on QueueItem objects. The queue tracks processing state with `is_processing` and `active_workers` flags.

### Database Schema Changes
Use `scripts/migrate_database.py` for migrations. The transcript viewer tool (`scripts/transcript_viewer.py`) is designed to handle missing columns gracefully by checking the schema dynamically.
