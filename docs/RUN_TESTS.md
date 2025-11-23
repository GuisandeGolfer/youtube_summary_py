# Quick Test Guide

## First Time Setup

1. **Install test dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify pytest is installed**:
   ```bash
   pytest --version
   ```

## Running Tests

### Run everything
```bash
pytest
```

### Run with more detail
```bash
pytest -v
```

### Run a specific test file
```bash
# Database tests only
pytest tests/test_database.py

# Summarization tests only
pytest tests/test_summarization.py

# Transcription tests only
pytest tests/test_transcription.py

# App integration tests only
pytest tests/test_app.py
```

### Run a specific test
```bash
# Test the new summary storage feature
pytest tests/test_database.py::TestSaveTranscriptionToDB::test_save_new_video_with_summary -v
```

### Run tests matching a pattern
```bash
# Run all tests with "summary" in the name
pytest -k summary

# Run all tests with "error" in the name
pytest -k error
```

## Understanding Test Output

### ✓ Green dot (.) = Test passed
### F = Test failed
### E = Test error
### s = Test skipped

## Expected Results

**IMPORTANT**: Some tests may fail on first run! This is NORMAL in TDD.

Common reasons tests might fail:
- Missing template files (templates/index.html)
- Hardcoded paths in transcription.py
- Missing prompt.json file

**This is OKAY!** The tests show you what needs to be fixed.

## TDD Learning Exercise

Try this workflow:

1. **Pick a failing test**:
   ```bash
   pytest tests/test_database.py -v
   ```

2. **Read the test** to understand what it expects

3. **Fix the code** to make the test pass

4. **Run the test again** to see it pass (GREEN!)

5. **Refactor** if needed while keeping tests green

## Debugging Failed Tests

### See full error details
```bash
pytest -v --tb=long
```

### Stop at first failure
```bash
pytest -x
```

### Run last failed tests only
```bash
pytest --lf
```

## Coverage Report

See which code is tested:
```bash
pytest --cov=. --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

## Pro Tips

1. Run tests frequently while coding
2. Fix failing tests immediately
3. Add tests when you find bugs
4. Keep tests fast by using mocks
5. One test should test one thing

## Need Help?

Read the full test documentation: `tests/README.md`
