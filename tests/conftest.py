"""
Pytest configuration and shared fixtures for test suite

Fixtures provide reusable test data and setup/teardown logic.
This is a key TDD concept - making tests easy to write and maintain.
"""
import os
import tempfile
import pytest
import sqlite3
from unittest.mock import MagicMock, patch


@pytest.fixture
def temp_db():
    """
    Fixture that creates a temporary database for testing.

    In TDD, we isolate tests from real data using fixtures.
    This ensures tests are repeatable and don't affect production data.

    Yields:
        str: Path to temporary database file
    """
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    yield path

    # Cleanup after test
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_audio_dir():
    """
    Fixture that creates a temporary directory for audio files.

    Yields:
        str: Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_transcription():
    """
    Fixture providing sample transcription text for testing.

    Returns:
        str: Sample transcription text
    """
    return "This is a sample video transcription for testing purposes. It contains multiple sentences."


@pytest.fixture
def sample_summary():
    """
    Fixture providing sample summary text for testing.

    Returns:
        str: Sample summary text
    """
    return "This video discusses testing concepts and best practices."


@pytest.fixture
def sample_video_url():
    """
    Fixture providing a sample YouTube URL.

    Returns:
        str: Sample YouTube URL
    """
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def sample_video_info():
    """
    Fixture providing sample video metadata.

    Returns:
        dict: Sample video information
    """
    return {
        'title': 'Test Video Title',
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'video_length': 300,
        'channel': 'Test Channel'
    }


@pytest.fixture
def mock_openai_client():
    """
    Fixture that mocks OpenAI API calls.

    In TDD, we mock external dependencies (APIs, databases, etc.)
    to make tests fast, reliable, and independent.

    Returns:
        MagicMock: Mocked OpenAI client
    """
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content="This is a test summary."))
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion

    return mock_client


@pytest.fixture
def mock_ytdlp():
    """
    Fixture that mocks yt-dlp video extraction.

    Returns:
        dict: Mocked video info
    """
    return {
        'title': 'Test Video',
        'webpage_url': 'https://www.youtube.com/watch?v=test123',
        'duration': 600,
        'uploader': 'Test Channel'
    }
