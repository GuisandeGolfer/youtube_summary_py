"""
Integration tests for app.py module

TDD INSIGHT: Integration tests verify that all components work together.
These tests are "higher level" and test real user workflows.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    """
    Fixture that creates a test client for the Flask app.

    TDD Principle: Use Flask's test client to test endpoints without
    running a real server.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestIndexRoute:
    """Test suite for the index route"""

    def test_index_route_returns_html(self, client):
        """
        Test that index route returns the HTML page.

        TDD Principle: Test basic functionality first.
        """
        response = client.get('/')

        assert response.status_code == 200
        # Note: This might fail if template doesn't exist, which is okay for TDD
        # In real TDD, you'd create the template to make this pass


class TestProcessVideoRoute:
    """Test suite for the /process endpoint"""

    @patch('app.save_transcription_to_db')
    @patch('app.generate_summary')
    @patch('app.transcribe_audio_file')
    @patch('app.download_video_audio')
    def test_process_video_success(
        self,
        mock_download,
        mock_transcribe,
        mock_summary,
        mock_save_db,
        client,
        sample_video_url,
        sample_transcription,
        sample_summary
    ):
        """
        Test successful video processing workflow.

        TDD Principle: Integration test - verify the complete flow works.
        This is the MOST IMPORTANT test - it validates the user's main use case.
        """
        # Setup mocks
        mock_download.return_value = "test_audio"
        mock_transcribe.return_value = sample_transcription
        mock_summary.return_value = sample_summary

        # Execute
        response = client.post('/process', json={'url': sample_video_url})

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['summary'] == sample_summary
        assert 'Transcription saved to database' in data['message']

        # Verify all steps were called
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_summary.assert_called_once_with(sample_transcription, sample_video_url)
        mock_save_db.assert_called_once()

        # NEW: Verify summary was passed to database
        call_args = mock_save_db.call_args
        assert call_args[1]['summary'] == sample_summary

    def test_process_video_no_url(self, client):
        """
        Test error handling when no URL is provided.

        TDD Principle: Test error conditions - invalid input.
        """
        response = client.post('/process', json={})

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'No URL provided' in data['error']

    def test_process_video_invalid_json(self, client):
        """
        Test error handling with invalid JSON.

        TDD Principle: Test malformed requests.
        """
        response = client.post('/process', data='not json', content_type='application/json')

        # Should either return 400 or 500 depending on how Flask handles it
        assert response.status_code in [400, 500]

    @patch('app.download_video_audio')
    def test_process_video_download_error(
        self,
        mock_download,
        client,
        sample_video_url
    ):
        """
        Test error handling when video download fails.

        TDD Principle: Test failure at each step of the workflow.
        """
        # Setup mock to raise error
        mock_download.side_effect = Exception("Download failed")

        # Execute
        response = client.post('/process', json={'url': sample_video_url})

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert 'Download failed' in data['error']

    @patch('app.transcribe_audio_file')
    @patch('app.download_video_audio')
    def test_process_video_transcription_error(
        self,
        mock_download,
        mock_transcribe,
        client,
        sample_video_url
    ):
        """
        Test error handling when transcription fails.

        TDD Principle: Test failure at different stages.
        """
        mock_download.return_value = "test_audio"
        mock_transcribe.side_effect = Exception("Transcription failed")

        # Execute
        response = client.post('/process', json={'url': sample_video_url})

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('app.generate_summary')
    @patch('app.transcribe_audio_file')
    @patch('app.download_video_audio')
    def test_process_video_summarization_error(
        self,
        mock_download,
        mock_transcribe,
        mock_summary,
        client,
        sample_video_url,
        sample_transcription
    ):
        """
        Test error handling when summarization fails.

        TDD Principle: Test all possible failure points.
        """
        mock_download.return_value = "test_audio"
        mock_transcribe.return_value = sample_transcription
        mock_summary.side_effect = Exception("API error")

        # Execute
        response = client.post('/process', json={'url': sample_video_url})

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('app.save_transcription_to_db')
    @patch('app.generate_summary')
    @patch('app.transcribe_audio_file')
    @patch('app.download_video_audio')
    def test_process_video_database_error(
        self,
        mock_download,
        mock_transcribe,
        mock_summary,
        mock_save_db,
        client,
        sample_video_url,
        sample_transcription,
        sample_summary
    ):
        """
        Test error handling when database save fails.

        TDD Principle: Test that errors in final steps are caught.
        """
        mock_download.return_value = "test_audio"
        mock_transcribe.return_value = sample_transcription
        mock_summary.return_value = sample_summary
        mock_save_db.side_effect = Exception("Database error")

        # Execute
        response = client.post('/process', json={'url': sample_video_url})

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('app.save_transcription_to_db')
    @patch('app.generate_summary')
    @patch('app.transcribe_audio_file')
    @patch('app.download_video_audio')
    def test_process_video_saves_summary_to_database(
        self,
        mock_download,
        mock_transcribe,
        mock_summary,
        mock_save_db,
        client,
        sample_video_url,
        sample_transcription,
        sample_summary
    ):
        """
        Test that summary is correctly passed to database.

        TDD Principle: This test specifically validates our NEW feature -
        that summaries are saved alongside transcriptions.
        """
        mock_download.return_value = "test_audio"
        mock_transcribe.return_value = sample_transcription
        mock_summary.return_value = sample_summary

        # Execute
        response = client.post('/process', json={'url': sample_video_url})

        # Assert success
        assert response.status_code == 200

        # Verify save_transcription_to_db was called with summary
        mock_save_db.assert_called_once()
        call_kwargs = mock_save_db.call_args[1]

        assert 'transcription' in call_kwargs
        assert call_kwargs['transcription'] == sample_transcription
        assert 'summary' in call_kwargs
        assert call_kwargs['summary'] == sample_summary
        assert 'video_url' in call_kwargs
        assert call_kwargs['video_url'] == sample_video_url


class TestEndToEndWorkflow:
    """
    End-to-end integration tests

    TDD INSIGHT: These tests verify the complete user journey.
    In a real TDD workflow, you'd write these FIRST to define
    what success looks like, then implement features to make them pass.
    """

    @patch('app.save_transcription_to_db')
    @patch('app.generate_summary')
    @patch('app.transcribe_audio_file')
    @patch('app.download_video_audio')
    def test_complete_workflow_with_summary_storage(
        self,
        mock_download,
        mock_transcribe,
        mock_summary,
        mock_save_db,
        client
    ):
        """
        Test the complete workflow: download -> transcribe -> summarize -> save.

        This is a key TDD test - it defines the ENTIRE feature requirement.
        """
        # Setup mocks
        test_url = "https://www.youtube.com/watch?v=test"
        test_filename = "test_audio_file"
        test_transcription = "This is a test transcription of the video content."
        test_summary = "Summary: Test video about testing."

        mock_download.return_value = test_filename
        mock_transcribe.return_value = test_transcription
        mock_summary.return_value = test_summary

        # Execute complete workflow
        response = client.post('/process', json={'url': test_url})

        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['summary'] == test_summary

        # Verify the workflow steps executed in order
        assert mock_download.call_count == 1
        assert mock_transcribe.call_count == 1
        assert mock_summary.call_count == 1
        assert mock_save_db.call_count == 1

        # Verify data flows correctly through the pipeline
        mock_download.assert_called_with(test_url, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'audio'))
        mock_transcribe.assert_called_with(test_filename, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'audio'))
        mock_summary.assert_called_with(test_transcription, test_url)

        # Most importantly: Verify summary is saved to database
        save_db_call = mock_save_db.call_args[1]
        assert save_db_call['transcription'] == test_transcription
        assert save_db_call['summary'] == test_summary
        assert save_db_call['video_url'] == test_url


"""
TDD LEARNING NOTES:
===================

What you've seen here:
1. Unit tests - Test individual functions in isolation
2. Integration tests - Test that components work together
3. End-to-end tests - Test complete user workflows

TDD Best Practices demonstrated:
- Mock external dependencies (APIs, databases, file systems)
- Test happy paths AND error conditions
- Test edge cases (empty input, missing files, etc.)
- Use descriptive test names that explain what's being tested
- Arrange-Act-Assert pattern in each test
- One assertion per test (mostly)

How to use TDD in your workflow:
1. Write a failing test for new functionality
2. Run the test - watch it fail (RED)
3. Write minimal code to make it pass (GREEN)
4. Refactor while keeping tests green (REFACTOR)
5. Repeat

Benefits you'll see:
- Fewer bugs reach production
- Easier refactoring (tests catch regressions)
- Better code design (testable code is usually better code)
- Living documentation (tests show how to use your code)

Remember: Not all tests need to pass initially! The goal is to
have a comprehensive test suite that guides development.
"""
