"""
Tests for summarization.py module

TDD INSIGHT: Summarization involves external API calls (OpenAI).
In TDD, we mock these to:
1. Make tests fast (no network calls)
2. Make tests reliable (don't depend on API availability)
3. Make tests free (no API charges during testing)
"""
import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from summarization import (
    load_prompt_template,
    format_prompt,
    split_transcription,
    generate_summary
)


class TestLoadPromptTemplate:
    """Test suite for load_prompt_template function"""

    @patch('builtins.open', new_callable=mock_open, read_data='{"normal": {"role": "user", "content": "Test prompt"}}')
    @patch('os.path.join')
    def test_load_prompt_template_success(self, mock_join, mock_file):
        """
        Test successful loading of prompt template.

        TDD Principle: Mock file I/O to test without actual files.
        """
        mock_join.return_value = 'prompt.json'

        result = load_prompt_template()

        assert 'normal' in result
        assert result['normal']['role'] == 'user'
        assert result['normal']['content'] == 'Test prompt'

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('os.path.join')
    def test_load_prompt_template_file_not_found(self, mock_join, mock_file):
        """
        Test that default prompt is returned when file not found.

        TDD Principle: Test fallback behavior for error conditions.
        """
        mock_join.return_value = 'prompt.json'

        result = load_prompt_template()

        # Should return default prompt
        assert 'normal' in result
        assert 'transcript' in result['normal']['content']
        assert 'url' in result['normal']['content']


class TestFormatPrompt:
    """Test suite for format_prompt function"""

    def test_format_prompt_success(self, sample_transcription, sample_video_url):
        """
        Test successful prompt formatting with transcript and URL.

        TDD Principle: Test data transformation functions thoroughly.
        """
        template = {
            'normal': {
                'role': 'user',
                'content': 'Summarize: {transcript}\nURL: {url}'
            }
        }

        result = format_prompt(template, sample_transcription, sample_video_url)

        assert result['role'] == 'user'
        assert sample_transcription in result['content']
        assert sample_video_url in result['content']

    def test_format_prompt_with_special_characters(self):
        """
        Test prompt formatting with special characters.

        TDD Principle: Test edge cases like special characters.
        """
        template = {
            'normal': {
                'role': 'user',
                'content': 'Transcript: {transcript}'
            }
        }
        transcript = "Test with 'quotes' and \"double quotes\" and {braces}"
        url = "https://example.com"

        result = format_prompt(template, transcript, url)

        assert transcript in result['content']


class TestSplitTranscription:
    """Test suite for split_transcription function"""

    def test_split_short_transcription(self):
        """
        Test that short transcriptions are not split.

        TDD Principle: Test boundary conditions - what's the minimum case?
        """
        short_text = "This is a short transcription."

        result = split_transcription(short_text, max_tokens=2048)

        assert len(result) == 1
        assert result[0] == short_text

    def test_split_long_transcription(self):
        """
        Test that long transcriptions are split into multiple chunks.

        TDD Principle: Test the primary use case for the function.
        """
        # Create a long transcription (roughly 3000 tokens worth)
        long_text = " ".join(["word"] * 12000)  # ~12000 characters = ~3000 tokens

        result = split_transcription(long_text, max_tokens=2048)

        # Should be split into at least 2 chunks
        assert len(result) >= 2
        # Each chunk should be non-empty
        for chunk in result:
            assert len(chunk) > 0

    def test_split_transcription_preserves_content(self):
        """
        Test that splitting doesn't lose any words.

        TDD Principle: Test data integrity - nothing should be lost.
        """
        original = " ".join([f"word{i}" for i in range(100)])

        result = split_transcription(original, max_tokens=50)

        # Rejoin all chunks
        rejoined = " ".join(result)

        # All words should be preserved
        assert rejoined == original

    def test_split_empty_transcription(self):
        """
        Test splitting empty transcription.

        TDD Principle: Test edge case - empty input.
        """
        result = split_transcription("", max_tokens=2048)

        assert len(result) == 1
        assert result[0] == ""


class TestGenerateSummary:
    """Test suite for generate_summary function"""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('summarization.OpenAI')
    @patch('summarization.load_prompt_template')
    def test_generate_summary_single_chunk(
        self,
        mock_load_prompt,
        mock_openai,
        sample_transcription,
        sample_video_url
    ):
        """
        Test generating summary for short transcription (single chunk).

        TDD Principle: Mock external APIs completely for isolated testing.
        """
        # Setup mocks
        mock_load_prompt.return_value = {
            'normal': {
                'role': 'user',
                'content': 'Summarize: {transcript}'
            }
        }

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="Test summary"))
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        # Execute
        result = generate_summary(sample_transcription, sample_video_url)

        # Assert
        assert result == "Test summary"
        assert mock_client.chat.completions.create.call_count == 1

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('summarization.OpenAI')
    @patch('summarization.load_prompt_template')
    @patch('summarization.split_transcription')
    def test_generate_summary_multiple_chunks(
        self,
        mock_split,
        mock_load_prompt,
        mock_openai,
        sample_video_url
    ):
        """
        Test generating summary for long transcription (multiple chunks).

        TDD Principle: Test complex scenarios - multiple API calls.
        """
        # Setup mocks
        long_transcription = "word " * 150000  # Very long text
        mock_split.return_value = ["chunk1", "chunk2", "chunk3"]

        mock_load_prompt.return_value = {
            'normal': {
                'role': 'user',
                'content': 'Summarize: {transcript}'
            }
        }

        # Mock multiple API responses
        mock_completion1 = MagicMock()
        mock_completion1.choices = [MagicMock(message=MagicMock(content="Summary 1"))]

        mock_completion2 = MagicMock()
        mock_completion2.choices = [MagicMock(message=MagicMock(content="Summary 2"))]

        mock_completion3 = MagicMock()
        mock_completion3.choices = [MagicMock(message=MagicMock(content="Summary 3"))]

        mock_final = MagicMock()
        mock_final.choices = [MagicMock(message=MagicMock(content="Final combined summary"))]

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            mock_completion1,
            mock_completion2,
            mock_completion3,
            mock_final
        ]
        mock_openai.return_value = mock_client

        # Execute
        result = generate_summary(long_transcription, sample_video_url)

        # Assert
        assert result == "Final combined summary"
        # Should call API 4 times (3 chunks + 1 final combination)
        assert mock_client.chat.completions.create.call_count == 4

    @patch.dict(os.environ, {}, clear=True)
    def test_generate_summary_no_api_key(self, sample_transcription, sample_video_url):
        """
        Test that missing API key raises error.

        TDD Principle: Test error conditions - missing configuration.
        """
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            generate_summary(sample_transcription, sample_video_url)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('summarization.OpenAI')
    @patch('summarization.load_prompt_template')
    def test_generate_summary_api_error(
        self,
        mock_load_prompt,
        mock_openai,
        sample_transcription,
        sample_video_url
    ):
        """
        Test that API errors are propagated.

        TDD Principle: Test error handling - what if the API fails?
        """
        mock_load_prompt.return_value = {
            'normal': {
                'role': 'user',
                'content': 'Summarize: {transcript}'
            }
        }

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        # Execute and expect error
        with pytest.raises(Exception, match="API Error"):
            generate_summary(sample_transcription, sample_video_url)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('summarization.OpenAI')
    @patch('summarization.load_prompt_template')
    def test_generate_summary_uses_correct_model(
        self,
        mock_load_prompt,
        mock_openai,
        sample_transcription,
        sample_video_url
    ):
        """
        Test that the correct OpenAI model is used.

        TDD Principle: Test configuration - are we using the right settings?
        """
        mock_load_prompt.return_value = {
            'normal': {
                'role': 'user',
                'content': 'Summarize: {transcript}'
            }
        }

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Summary"))]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        # Execute
        generate_summary(sample_transcription, sample_video_url)

        # Verify correct model was used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4o-mini'
