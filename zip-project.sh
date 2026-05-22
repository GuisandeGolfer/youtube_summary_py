#!/bin/zsh

# Zip project for transfer to another machine
# Excludes build artifacts, virtual environments, and runtime data

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_NAME="$(basename "$PROJECT_DIR")"
OUTPUT_FILE="${PROJECT_DIR}.zip"

echo "Zipping $PROJECT_NAME..."
echo "Output: $OUTPUT_FILE"

cd "$(dirname "$PROJECT_DIR")"

zip -r "$OUTPUT_FILE" "$PROJECT_NAME" \
  -x "$PROJECT_NAME/.venv/*" \
  -x "$PROJECT_NAME/.git/*" \
  -x "$PROJECT_NAME/__pycache__/*" \
  -x "$PROJECT_NAME/.claude/*" \
  -x "$PROJECT_NAME/data/*" \
  -x "$PROJECT_NAME/downloads/*" \
  -x "$PROJECT_NAME/.DS_Store" \
  -x "$PROJECT_NAME/*/__pycache__/*" \
  -x "$PROJECT_NAME/.env"

echo ""
echo "✓ Created: $OUTPUT_FILE"
echo ""
echo "Note: .env file excluded for security. Remember to:"
echo "  1. Create .env on the new machine"
echo "  2. Add your OPENAI_API_KEY"
echo "  3. Run 'uv sync' to recreate the virtual environment"
