"""
Tests for database.py module

TDD EXAMPLE: In real TDD, you would write these tests FIRST,
then implement the code to make them pass. This ensures you:
1. Think about requirements before coding
2. Write testable code
3. Have confidence your code works as expected
"""
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from database import (
    create_videos_table,
    extract_video_info,
    save_transcription_to_db,
    get_all_transcriptions
)


class TestCreateVideosTable:
    """Test suite for create_videos_table function"""

    def test_table_creation_success(self, temp_db):
        """
        Test that videos table is created successfully.

        TDD Principle: Test the happy path first - what should happen
        when everything works correctly.
        """
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        create_videos_table(cursor)

        # Verify table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='videos'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 'videos'

        conn.close()

    def test_table_has_correct_columns(self, temp_db):
        """
        Test that the videos table has all required columns including summary.

        TDD Principle: Test behavior, not implementation. We care that
        the columns exist, not HOW they were created.
        """
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        create_videos_table(cursor)

        # Get table info
        cursor.execute("PRAGMA table_info(videos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Assert all required columns exist
        assert 'id' in column_names
        assert 'title' in column_names
        assert 'url' in column_names
        assert 'video_length' in column_names
        assert 'channel' in column_names
        assert 'transcription' in column_names
        assert 'summary' in column_names  # NEW: Test our new column
        assert 'created_at' in column_names

        conn.close()

    def test_table_creation_is_idempotent(self, temp_db):
        """
        Test that calling create_videos_table multiple times doesn't error.

        TDD Principle: Test edge cases and error conditions.
        """
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Create table twice
        create_videos_table(cursor)
        create_videos_table(cursor)  # Should not raise an error

        # Verify table still exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
        result = cursor.fetchone()

        assert result is not None
        conn.close()


class TestExtractVideoInfo:
    """Test suite for extract_video_info function"""

    @patch('database.YoutubeDL')
    def test_extract_video_info_success(self, mock_ytdl, sample_video_url):
        """
        Test successful video info extraction.

        TDD Principle: Mock external dependencies (yt-dlp) so tests
        are fast and don't depend on network/YouTube availability.
        """
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'webpage_url': sample_video_url,
            'duration': 300,
            'uploader': 'Test Channel'
        }
        mock_ytdl.return_value = mock_instance

        # Execute
        result = extract_video_info(sample_video_url)

        # Assert
        assert result['title'] == 'Test Video'
        assert result['url'] == sample_video_url
        assert result['video_length'] == 300
        assert result['channel'] == 'Test Channel'

    @patch('database.YoutubeDL')
    def test_extract_video_info_handles_errors(self, mock_ytdl, sample_video_url):
        """
        Test that extract_video_info handles errors gracefully.

        TDD Principle: Test error handling - what happens when things go wrong?
        """
        # Setup mock to raise an exception
        mock_instance = MagicMock()
        mock_instance.__enter__ = MagicMock(side_effect=Exception("Network error"))
        mock_ytdl.return_value = mock_instance

        # Execute
        result = extract_video_info(sample_video_url)

        # Assert default values are returned
        assert result['title'] == 'Unknown Title'
        assert result['url'] == sample_video_url
        assert result['video_length'] == 0
        assert result['channel'] == 'Unknown Channel'


class TestSaveTranscriptionToDB:
    """Test suite for save_transcription_to_db function"""

    @patch('database.extract_video_info')
    def test_save_new_video_with_summary(
        self,
        mock_extract,
        temp_db,
        sample_transcription,
        sample_summary,
        sample_video_url,
        sample_video_info
    ):
        """
        Test saving a new video with transcription AND summary.

        TDD Principle: This is our NEW requirement - test it first!
        """
        # Setup mock
        mock_extract.return_value = sample_video_info

        # Execute
        save_transcription_to_db(
            db_path=temp_db,
            transcription=sample_transcription,
            video_url=sample_video_url,
            summary=sample_summary
        )

        # Verify data was saved
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE url = ?", (sample_video_url,))
        result = cursor.fetchone()

        assert result is not None
        assert result[2] == sample_video_url  # url
        assert result[5] == sample_transcription  # transcription
        assert result[6] == sample_summary  # summary

        conn.close()

    @patch('database.extract_video_info')
    def test_save_video_without_summary(
        self,
        mock_extract,
        temp_db,
        sample_transcription,
        sample_video_url,
        sample_video_info
    ):
        """
        Test that summary is optional (backward compatibility).

        TDD Principle: Test that new features don't break existing functionality.
        """
        mock_extract.return_value = sample_video_info

        # Execute without summary
        save_transcription_to_db(
            db_path=temp_db,
            transcription=sample_transcription,
            video_url=sample_video_url
        )

        # Verify data was saved
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT transcription, summary FROM videos WHERE url = ?", (sample_video_url,))
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == sample_transcription  # transcription exists
        assert result[1] is None  # summary is None

        conn.close()

    @patch('database.extract_video_info')
    def test_update_existing_video_with_summary(
        self,
        mock_extract,
        temp_db,
        sample_transcription,
        sample_summary,
        sample_video_url,
        sample_video_info
    ):
        """
        Test updating an existing video with new summary.

        TDD Principle: Test state changes - inserting vs updating.
        """
        mock_extract.return_value = sample_video_info

        # First insert
        save_transcription_to_db(
            db_path=temp_db,
            transcription="Old transcription",
            video_url=sample_video_url,
            summary="Old summary"
        )

        # Update with new data
        save_transcription_to_db(
            db_path=temp_db,
            transcription=sample_transcription,
            video_url=sample_video_url,
            summary=sample_summary
        )

        # Verify only one record exists with updated data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), transcription, summary FROM videos WHERE url = ?", (sample_video_url,))
        result = cursor.fetchone()

        assert result[0] == 1  # Only one record
        assert result[1] == sample_transcription  # Updated transcription
        assert result[2] == sample_summary  # Updated summary

        conn.close()

    def test_save_to_invalid_db_path_raises_error(
        self,
        sample_transcription,
        sample_video_url
    ):
        """
        Test that invalid database path raises an error.

        TDD Principle: Test error conditions and edge cases.
        """
        with pytest.raises(Exception):
            save_transcription_to_db(
                db_path="/invalid/path/db.db",
                transcription=sample_transcription,
                video_url=sample_video_url
            )


class TestGetAllTranscriptions:
    """Test suite for get_all_transcriptions function"""

    def test_get_all_transcriptions_empty_db(self, temp_db):
        """
        Test retrieving from empty database.

        TDD Principle: Test boundary conditions - what if there's no data?
        """
        # Create empty table
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        create_videos_table(cursor)
        conn.commit()
        conn.close()

        # Execute
        result = get_all_transcriptions(temp_db)

        # Assert
        assert result == []

    @patch('database.extract_video_info')
    def test_get_all_transcriptions_includes_summary(
        self,
        mock_extract,
        temp_db,
        sample_transcription,
        sample_summary,
        sample_video_url,
        sample_video_info
    ):
        """
        Test that get_all_transcriptions includes summary field.

        TDD Principle: Test the complete data flow of new features.
        """
        mock_extract.return_value = sample_video_info

        # Add a video with summary
        save_transcription_to_db(
            db_path=temp_db,
            transcription=sample_transcription,
            video_url=sample_video_url,
            summary=sample_summary
        )

        # Retrieve
        results = get_all_transcriptions(temp_db)

        # Assert
        assert len(results) == 1
        assert 'summary' in results[0]
        assert results[0]['summary'] == sample_summary
        assert results[0]['title'] == sample_video_info['title']
        assert results[0]['channel'] == sample_video_info['channel']

    @patch('database.extract_video_info')
    def test_get_all_transcriptions_ordered_by_date(
        self,
        mock_extract,
        temp_db,
        sample_transcription,
        sample_video_info
    ):
        """
        Test that results are ordered by created_at DESC (newest first).

        TDD Principle: Test expected behavior, not implementation details.
        """
        mock_extract.return_value = sample_video_info

        # Add multiple videos
        save_transcription_to_db(temp_db, sample_transcription, "https://youtube.com/1")
        save_transcription_to_db(temp_db, sample_transcription, "https://youtube.com/2")
        save_transcription_to_db(temp_db, sample_transcription, "https://youtube.com/3")

        # Retrieve
        results = get_all_transcriptions(temp_db)

        # Assert ordered by date (newest first)
        assert len(results) == 3
        assert results[0]['url'] == "https://youtube.com/3"  # Most recent
        assert results[2]['url'] == "https://youtube.com/1"  # Oldest

    def test_get_all_transcriptions_invalid_path_returns_empty(self):
        """
        Test that invalid database path returns empty list gracefully.

        TDD Principle: Graceful degradation - don't crash on errors.
        """
        result = get_all_transcriptions("/invalid/path/db.db")
        assert result == []
