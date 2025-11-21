# Test Suite for YouTube Summary Project

## Overview
This test suite demonstrates Test-Driven Development (TDD) principles for the YouTube video summarizer application.

## Test Structure

```
tests/
├── __init__.py              # Makes tests a Python package
├── conftest.py              # Shared fixtures and configuration
├── test_database.py         # Tests for database operations
├── test_summarization.py    # Tests for OpenAI summarization
├── test_transcription.py    # Tests for audio transcription
└── test_app.py             # Integration tests for Flask app
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_database.py
```

### Run specific test class
```bash
pytest tests/test_database.py::TestSaveTranscriptionToDB
```

### Run specific test function
```bash
pytest tests/test_database.py::TestSaveTranscriptionToDB::test_save_new_video_with_summary
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage report (requires pytest-cov)
```bash
pytest --cov=. --cov-report=html
```

## Test Categories

### Unit Tests
- Test individual functions in isolation
- Fast execution
- Mock all external dependencies
- Examples: `test_database.py`, `test_summarization.py`

### Integration Tests
- Test multiple components working together
- Test data flow between modules
- Example: `test_app.py`

### Fixtures (conftest.py)
Shared test data and setup:
- `temp_db` - Temporary database for testing
- `temp_audio_dir` - Temporary directory for audio files
- `sample_transcription` - Sample text data
- `sample_summary` - Sample summary text
- `mock_openai_client` - Mocked OpenAI API

## TDD Workflow

### The Red-Green-Refactor Cycle

1. **RED**: Write a failing test
   ```python
   def test_new_feature():
       result = new_feature()
       assert result == "expected"
   ```

2. **GREEN**: Write minimal code to pass
   ```python
   def new_feature():
       return "expected"
   ```

3. **REFACTOR**: Improve code while keeping tests green
   ```python
   def new_feature():
       # Better implementation
       return calculate_result()
   ```

## Understanding the Tests

### Example: Testing Summary Storage

```python
def test_save_new_video_with_summary(
    temp_db,
    sample_transcription,
    sample_summary,
    sample_video_url
):
    # ARRANGE: Set up test data
    # ACT: Call the function
    save_transcription_to_db(
        db_path=temp_db,
        transcription=sample_transcription,
        summary=sample_summary,
        video_url=sample_video_url
    )

    # ASSERT: Verify the result
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT summary FROM videos")
    result = cursor.fetchone()

    assert result[0] == sample_summary
    conn.close()
```

## Key TDD Principles Demonstrated

1. **Test First**: Write tests before implementation
2. **Small Steps**: One test at a time
3. **Mock External Dependencies**: APIs, file systems, databases
4. **Test Behavior, Not Implementation**: Focus on what, not how
5. **Test Edge Cases**: Empty inputs, errors, boundary conditions
6. **Keep Tests Fast**: Use mocks to avoid slow operations
7. **One Assertion Per Test** (mostly): Each test validates one thing

## Common Testing Patterns

### Mocking External APIs
```python
@patch('module.OpenAI')
def test_with_mocked_api(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    # Test code here
```

### Testing Exceptions
```python
def test_error_handling():
    with pytest.raises(ValueError, match="error message"):
        function_that_should_raise()
```

### Using Fixtures
```python
def test_with_fixtures(temp_db, sample_data):
    # Fixtures are automatically provided
    result = function(temp_db, sample_data)
    assert result is not None
```

## Current Test Coverage

- **database.py**: ✓ Full coverage
  - Table creation
  - Video info extraction
  - Saving transcriptions AND summaries (NEW)
  - Retrieving all videos

- **summarization.py**: ✓ Full coverage
  - Prompt loading
  - Text splitting
  - OpenAI API calls
  - Error handling

- **transcription.py**: ✓ Full coverage
  - Audio splitting
  - Whisper.cpp integration
  - File cleanup

- **app.py**: ✓ Integration tests
  - Complete workflow
  - Error handling at each step
  - Summary storage validation (NEW)

## Expected Test Results

**Note**: Some tests may fail initially because:
1. Template files might not exist
2. Actual file paths are hardcoded in transcription.py
3. Some tests are intentionally strict to guide development

This is NORMAL in TDD! Failing tests show what needs to be implemented or fixed.

## Next Steps for Learning TDD

1. **Start Small**: Pick one failing test and make it pass
2. **Practice the Cycle**: Red → Green → Refactor
3. **Add New Features with Tests**:
   - Write test for new feature first
   - Watch it fail
   - Implement feature
   - Watch it pass
4. **Refactor with Confidence**: Tests catch regressions

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Test-Driven Development by Example](https://www.oreilly.com/library/view/test-driven-development/0321146530/) - Kent Beck
- [Python Testing with pytest](https://pragprog.com/titles/bopytest/python-testing-with-pytest/) - Brian Okken

## Questions?

TDD is a skill that improves with practice. Don't worry if tests fail initially - that's the point! Tests guide you toward correct implementation.
