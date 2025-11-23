"""
Core business logic for YouTube video processing.

This package contains modules for:
- YouTube video downloading and metadata extraction
- Audio transcription using Whisper
- Text summarization using Claude
- Database operations
"""

from .youtube import download_video_audio, get_video_info, extract_video_id
from .transcription import transcribe_audio_file
from .summarization import generate_summary
from .database import save_transcription_to_db

__all__ = [
    'download_video_audio',
    'get_video_info',
    'extract_video_id',
    'transcribe_audio_file',
    'generate_summary',
    'save_transcription_to_db',
]
