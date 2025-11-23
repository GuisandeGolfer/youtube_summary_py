"""
Tests for transcription.py module

TDD INSIGHT: Transcription involves external tools (ffmpeg, whisper.cpp).
These tests demonstrate how to mock system commands and file operations.
"""
import pytest
import os
from unittest.mock import patch, MagicMock, call
from src.core.transcription import (
    split_audio_file,
    transcribe_audio_segments,
    cleanup_audio_files,
    transcribe_audio_file
)


class TestSplitAudioFile:
    """Test suite for split_audio_file function"""

    @patch('subprocess.run')
    def test_split_audio_file_single_segment(self, mock_run, temp_audio_dir):
        """
        Test splitting short audio file (single segment).

        TDD Principle: Mock subprocess calls to avoid actual file processing.
        """
        # Mock ffprobe response (short audio - 1000 seconds)
        mock_probe = MagicMock()
        mock_probe.stdout = '{"format": {"duration": "1000.0"}}'
        mock_probe.returncode = 0

        # Mock ffmpeg responses
        mock_ffmpeg = MagicMock()
        mock_ffmpeg.returncode = 0

        mock_run.side_effect = [mock_probe, mock_ffmpeg]

        # Execute
        segments = split_audio_file(temp_audio_dir, "test_audio", segment_duration=1400)

        # Assert
        assert len(segments) == 1
        assert segments[0] == "test_audio_part0.wav"

    @patch('subprocess.run')
    def test_split_audio_file_multiple_segments(self, mock_run, temp_audio_dir):
        """
        Test splitting long audio file (multiple segments).

        TDD Principle: Test the main use case - splitting long files.
        """
        # Mock ffprobe response (long audio - 3000 seconds)
        mock_probe = MagicMock()
        mock_probe.stdout = '{"format": {"duration": "3000.0"}}'
        mock_probe.returncode = 0

        # Mock ffmpeg responses (one per segment)
        mock_ffmpeg = MagicMock()
        mock_ffmpeg.returncode = 0

        # 3 segments needed for 3000 seconds with 1400s segments
        mock_run.side_effect = [mock_probe] + [mock_ffmpeg] * 3

        # Execute
        segments = split_audio_file(temp_audio_dir, "test_audio", segment_duration=1400)

        # Assert
        assert len(segments) == 3
        assert segments[0] == "test_audio_part0.wav"
        assert segments[1] == "test_audio_part1.wav"
        assert segments[2] == "test_audio_part2.wav"

    @patch('subprocess.run')
    def test_split_audio_file_ffprobe_error(self, mock_run, temp_audio_dir):
        """
        Test error handling when ffprobe fails.

        TDD Principle: Test error conditions in subprocess calls.
        """
        # Mock ffprobe to raise error
        mock_run.side_effect = Exception("ffprobe failed")

        # Execute and expect error
        with pytest.raises(Exception, match="ffprobe failed"):
            split_audio_file(temp_audio_dir, "test_audio")

    @patch('subprocess.run')
    def test_split_audio_file_creates_correct_segments(self, mock_run, temp_audio_dir):
        """
        Test that ffmpeg is called with correct parameters.

        TDD Principle: Verify that external tools are called correctly.
        """
        # Mock ffprobe
        mock_probe = MagicMock()
        mock_probe.stdout = '{"format": {"duration": "2000.0"}}'
        mock_probe.returncode = 0

        mock_ffmpeg = MagicMock()
        mock_ffmpeg.returncode = 0

        mock_run.side_effect = [mock_probe, mock_ffmpeg, mock_ffmpeg]

        # Execute
        split_audio_file(temp_audio_dir, "test_audio", segment_duration=1400)

        # Verify ffmpeg was called with correct audio parameters
        ffmpeg_calls = [call for call in mock_run.call_args_list if 'ffmpeg' in str(call)]
        assert len(ffmpeg_calls) == 2  # 2 segments for 2000s

        # Check that audio format is correct (16kHz, mono, 16-bit PCM)
        for ffmpeg_call in ffmpeg_calls:
            args = ffmpeg_call[0][0]
            assert '-ar' in args and '16000' in args  # 16kHz
            assert '-ac' in args and '1' in args  # Mono
            assert 'pcm_s16le' in args  # 16-bit PCM


class TestTranscribeAudioSegments:
    """Test suite for transcribe_audio_segments function"""

    @patch('subprocess.run')
    def test_transcribe_single_segment(self, mock_run, temp_audio_dir):
        """
        Test transcribing a single audio segment.

        TDD Principle: Mock whisper.cpp CLI calls.
        """
        # Mock whisper-cli output
        mock_result = MagicMock()
        mock_result.stdout = "This is the transcription."
        mock_result.returncode = 0

        mock_run.return_value = mock_result

        # Execute
        segments = ["test_part0.wav"]
        model_path = "/path/to/model.bin"
        result = transcribe_audio_segments(temp_audio_dir, segments, model_path)

        # Assert
        assert result == "This is the transcription."
        assert mock_run.call_count == 1

    @patch('subprocess.run')
    def test_transcribe_multiple_segments(self, mock_run, temp_audio_dir):
        """
        Test transcribing multiple audio segments and joining them.

        TDD Principle: Test data aggregation from multiple operations.
        """
        # Mock whisper-cli outputs
        mock_result1 = MagicMock()
        mock_result1.stdout = "First segment."
        mock_result1.returncode = 0

        mock_result2 = MagicMock()
        mock_result2.stdout = "Second segment."
        mock_result2.returncode = 0

        mock_result3 = MagicMock()
        mock_result3.stdout = "Third segment."
        mock_result3.returncode = 0

        mock_run.side_effect = [mock_result1, mock_result2, mock_result3]

        # Execute
        segments = ["test_part0.wav", "test_part1.wav", "test_part2.wav"]
        model_path = "/path/to/model.bin"
        result = transcribe_audio_segments(temp_audio_dir, segments, model_path)

        # Assert
        assert result == "First segment. Second segment. Third segment."
        assert mock_run.call_count == 3

    @patch('subprocess.run')
    def test_transcribe_segments_error_handling(self, mock_run, temp_audio_dir):
        """
        Test error handling when whisper-cli fails.

        TDD Principle: Test error propagation from external tools.
        """
        # Mock whisper-cli to fail
        mock_run.side_effect = Exception("Whisper CLI failed")

        # Execute and expect error
        segments = ["test_part0.wav"]
        model_path = "/path/to/model.bin"

        with pytest.raises(Exception):
            transcribe_audio_segments(temp_audio_dir, segments, model_path)


class TestCleanupAudioFiles:
    """Test suite for cleanup_audio_files function"""

    @patch('glob.glob')
    @patch('os.remove')
    def test_cleanup_audio_files_success(self, mock_remove, mock_glob, temp_audio_dir):
        """
        Test successful cleanup of audio files.

        TDD Principle: Test file system operations with mocks.
        """
        # Mock glob to return file paths
        mock_glob.return_value = [
            os.path.join(temp_audio_dir, "test_audio.wav"),
            os.path.join(temp_audio_dir, "test_audio_part0.wav"),
            os.path.join(temp_audio_dir, "test_audio_part1.wav")
        ]

        # Execute
        cleanup_audio_files(temp_audio_dir, "test_audio")

        # Assert all files were deleted
        assert mock_remove.call_count == 3

    @patch('glob.glob')
    @patch('os.remove')
    def test_cleanup_no_files(self, mock_remove, mock_glob, temp_audio_dir):
        """
        Test cleanup when no files match pattern.

        TDD Principle: Test edge case - nothing to clean.
        """
        mock_glob.return_value = []

        # Execute (should not error)
        cleanup_audio_files(temp_audio_dir, "test_audio")

        # Assert no files were deleted
        assert mock_remove.call_count == 0

    @patch('glob.glob')
    @patch('os.remove')
    def test_cleanup_handles_errors_gracefully(self, mock_remove, mock_glob, temp_audio_dir):
        """
        Test that cleanup errors are logged but don't crash.

        TDD Principle: Test graceful error handling.
        """
        mock_glob.return_value = [os.path.join(temp_audio_dir, "test.wav")]
        mock_remove.side_effect = OSError("Permission denied")

        # Execute (should not raise exception)
        cleanup_audio_files(temp_audio_dir, "test_audio")

        # Should have attempted to remove
        assert mock_remove.call_count == 1


class TestTranscribeAudioFile:
    """Integration test suite for transcribe_audio_file function"""

    @patch('transcription.cleanup_audio_files')
    @patch('transcription.transcribe_audio_segments')
    @patch('transcription.split_audio_file')
    @patch('os.path.exists')
    def test_transcribe_audio_file_success(
        self,
        mock_exists,
        mock_split,
        mock_transcribe,
        mock_cleanup,
        temp_audio_dir
    ):
        """
        Test complete transcription workflow.

        TDD Principle: Integration test - test the whole flow.
        """
        # Setup mocks
        mock_exists.return_value = True  # Model exists
        mock_split.return_value = ["part0.wav", "part1.wav"]
        mock_transcribe.return_value = "Complete transcription text."

        # Execute
        result = transcribe_audio_file("test_audio", temp_audio_dir)

        # Assert
        assert result == "Complete transcription text."
        assert mock_split.called
        assert mock_transcribe.called
        assert mock_cleanup.called

    @patch('os.path.exists')
    def test_transcribe_audio_file_model_not_found(self, mock_exists, temp_audio_dir):
        """
        Test error when whisper model doesn't exist.

        TDD Principle: Test precondition validation.
        """
        mock_exists.return_value = False  # Model doesn't exist

        # Execute and expect error
        with pytest.raises(ValueError, match="Whisper model not found"):
            transcribe_audio_file("test_audio", temp_audio_dir)

    @patch('transcription.cleanup_audio_files')
    @patch('transcription.transcribe_audio_segments')
    @patch('transcription.split_audio_file')
    @patch('os.path.exists')
    def test_transcribe_audio_file_cleanup_called_on_success(
        self,
        mock_exists,
        mock_split,
        mock_transcribe,
        mock_cleanup,
        temp_audio_dir
    ):
        """
        Test that cleanup is called even after successful transcription.

        TDD Principle: Test resource cleanup.
        """
        mock_exists.return_value = True
        mock_split.return_value = ["part0.wav"]
        mock_transcribe.return_value = "Transcription"

        # Execute
        transcribe_audio_file("test_audio", temp_audio_dir)

        # Assert cleanup was called
        mock_cleanup.assert_called_once_with(temp_audio_dir, "test_audio")
