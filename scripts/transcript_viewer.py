#!/usr/bin/env python3
"""
YouTube Transcript & Summary Retriever

A CLI tool to browse and retrieve transcriptions and summaries from your
local transcriptions.db database using fzf for interactive selection.

Usage:
    transcript                          # Interactive mode, output to stdout
    transcript --summary                # Skip type selection, get summary
    transcript --full                   # Skip type selection, get transcription
    transcript --clipboard              # Copy result to clipboard
    transcript --summary --clipboard    # Get summary and copy to clipboard

Dependencies:
    - fzf (install via: brew install fzf)
    - Python 3.8+
    - SQLite3 (built-in)

Author: Your friendly AI assistant
"""

import sys
import os
import sqlite3
import subprocess
import argparse
import re
import textwrap
from datetime import datetime
from typing import Optional, Tuple, List, Dict


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def get_db_path() -> str:
    """
    Get the path to transcriptions.db in the data directory.

    Returns:
        str: Absolute path to transcriptions.db
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level to project root
    return os.path.join(project_root, "data", "transcriptions.db")


def get_table_columns(db_path: str) -> List[str]:
    """
    Get list of columns that exist in the videos table.

    This function checks the actual database schema to handle
    databases that might not have all expected columns (like summary or created_at).

    Args:
        db_path: Path to database

    Returns:
        List of column names
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(videos)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    return columns


def fetch_all_videos() -> List[Dict]:
    """
    Query the database and fetch all videos with their metadata.

    This function dynamically builds the query based on what columns
    actually exist in the database, making it compatible with older
    database schemas that might be missing summary or created_at columns.

    Returns:
        List of dictionaries containing video data:
        - id: Video ID
        - title: Video title
        - url: YouTube URL
        - channel: Channel name
        - video_length: Duration in seconds
        - created_at: Timestamp when added (if column exists, else None)
        - has_summary: Boolean indicating if summary exists (if column exists, else 0)
        - has_transcription: Boolean indicating if transcription exists

    Raises:
        Exception: If database doesn't exist or query fails
    """
    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        print("Have you processed any videos yet?", file=sys.stderr)
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()

        # Check what columns actually exist in the database
        columns = get_table_columns(db_path)
        has_summary_col = 'summary' in columns
        has_created_at_col = 'created_at' in columns

        # Build query dynamically based on available columns
        select_fields = [
            "id",
            "title",
            "url",
            "channel",
            "video_length",
        ]

        # Add created_at if it exists
        if has_created_at_col:
            select_fields.append("created_at")

        # Add has_summary check if column exists
        if has_summary_col:
            select_fields.append(
                "CASE WHEN summary IS NOT NULL AND summary != '' THEN 1 ELSE 0 END as has_summary"
            )

        # Always check transcription
        select_fields.append(
            "CASE WHEN transcription IS NOT NULL AND transcription != '' THEN 1 ELSE 0 END as has_transcription"
        )

        # Order by created_at if it exists, otherwise by id (descending = newest first)
        order_by = "created_at DESC" if has_created_at_col else "id DESC"

        query = f"""
            SELECT {', '.join(select_fields)}
            FROM videos
            ORDER BY {order_by}
        """

        cursor.execute(query)
        videos = [dict(row) for row in cursor.fetchall()]

        # Add default values for missing columns so the rest of the code doesn't break
        for video in videos:
            if 'created_at' not in video:
                video['created_at'] = None
            if 'has_summary' not in video:
                video['has_summary'] = 0

        conn.close()

        if not videos:
            print("No videos found in database.", file=sys.stderr)
            print("Process some videos first using the main app!", file=sys.stderr)
            sys.exit(1)

        return videos

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_video_content(video_id: int, content_type: str) -> str:
    """
    Fetch the summary or transcription for a specific video.

    Args:
        video_id: The database ID of the video
        content_type: Either 'summary' or 'transcription'

    Returns:
        str: The requested content

    Raises:
        Exception: If content doesn't exist or query fails
    """
    db_path = get_db_path()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the requested column actually exists
        columns = get_table_columns(db_path)

        if content_type not in columns:
            print(f"Error: Database doesn't have '{content_type}' column.", file=sys.stderr)
            print(f"Your database needs to be updated to support summaries.", file=sys.stderr)
            print(f"Process a video with the main app to update the schema.", file=sys.stderr)
            conn.close()
            sys.exit(1)

        cursor.execute(f"SELECT {content_type} FROM videos WHERE id = ?", (video_id,))
        result = cursor.fetchone()
        conn.close()

        if not result or not result[0]:
            print(f"Error: No {content_type} found for this video.", file=sys.stderr)
            sys.exit(1)

        return result[0]

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# FORMATTING FUNCTIONS
# ============================================================================

def format_duration(seconds: int) -> str:
    """
    Convert seconds to human-readable duration (HH:MM:SS or MM:SS).

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration string
    """
    if not seconds:
        return "??:??"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_date(timestamp: str) -> str:
    """
    Convert SQLite timestamp to readable date format.

    Args:
        timestamp: SQLite timestamp string or None

    Returns:
        str: Formatted date (e.g., "Jan 15, 2025") or "No date" if None
    """
    if not timestamp:
        return "No date"
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%b %d, %Y")
    except:
        return "Unknown"


def format_video_for_fzf(video: Dict) -> str:
    """
    Format a video entry for display in fzf.

    Format: [ID] [Duration] Title | Channel | Date [S/T indicators]
    Where S = has summary, T = has transcription

    Args:
        video: Dictionary containing video metadata

    Returns:
        str: Formatted string for fzf display
    """
    # Format duration
    duration = format_duration(video['video_length'])

    # Format date (might be None if column doesn't exist)
    date = format_date(video.get('created_at'))

    # Content indicators
    indicators = []
    if video.get('has_summary'):
        indicators.append('S')
    if video.get('has_transcription'):
        indicators.append('T')
    indicator_str = ''.join(indicators) if indicators else '-'

    # Truncate title and channel for display
    title = video['title'][:60] + '...' if len(video['title']) > 60 else video['title']
    channel = video['channel'][:25] + '...' if len(video['channel']) > 25 else video['channel']

    # Format: [ID] [Duration] Title | Channel | Date [Indicators]
    return f"[{video['id']:3d}] [{duration}] {title:60s} | {channel:25s} | {date} [{indicator_str}]"


# ============================================================================
# FZF INTERACTION FUNCTIONS
# ============================================================================

def check_fzf_installed() -> bool:
    """
    Check if fzf is installed and available.

    Returns:
        bool: True if fzf is installed, False otherwise
    """
    try:
        subprocess.run(['fzf', '--version'],
                      capture_output=True,
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def select_video_with_fzf(videos: List[Dict]) -> Optional[int]:
    """
    Display videos in fzf for interactive selection.

    Args:
        videos: List of video dictionaries

    Returns:
        int: Selected video ID, or None if cancelled
    """
    # Format videos for display
    formatted_lines = [format_video_for_fzf(video) for video in videos]
    fzf_input = '\n'.join(formatted_lines)

    # Simple fzf command without preview
    fzf_command = [
        'fzf',
        '--height=40%',                     # Use 40% of terminal height
        '--reverse',                        # Results top to bottom
        '--border',                         # Show border
        '--header=Select a video (ESC to cancel) | [S]=Summary [T]=Transcription',
        '--prompt=Videos > ',
    ]

    try:
        result = subprocess.run(
            fzf_command,
            input=fzf_input,
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            # User cancelled (ESC or Ctrl-C)
            return None

        # Extract video ID from selected line [ID]
        selected_line = result.stdout.strip()
        video_id = int(selected_line.split('[')[1].split(']')[0])

        return video_id

    except Exception as e:
        print(f"Error during selection: {e}", file=sys.stderr)
        sys.exit(1)


def select_content_type_with_fzf(video_id: int) -> str:
    """
    Use fzf to let user choose between summary and transcription.

    Checks what content types are available for the selected video
    and lets the user choose. If only one type is available, returns it automatically.

    Args:
        video_id: The selected video ID (for validation)

    Returns:
        str: Either 'summary' or 'transcription'
    """
    # Check what's available for this video
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check what columns exist in the database
    columns = get_table_columns(db_path)
    has_summary_col = 'summary' in columns

    # Query based on available columns
    if has_summary_col:
        cursor.execute(
            "SELECT summary, transcription FROM videos WHERE id = ?",
            (video_id,)
        )
        result = cursor.fetchone()
        has_summary = result[0] is not None and result[0] != ''
        has_transcription = result[1] is not None and result[1] != ''
    else:
        # No summary column, only check transcription
        cursor.execute(
            "SELECT transcription FROM videos WHERE id = ?",
            (video_id,)
        )
        result = cursor.fetchone()
        has_summary = False
        has_transcription = result[0] is not None and result[0] != ''

    conn.close()

    # Build options list based on what's available
    options = []
    if has_summary:
        options.append("summary         - Get AI-generated summary (shorter)")
    if has_transcription:
        options.append("transcription   - Get full transcription (complete)")

    if not options:
        print("Error: This video has no content available.", file=sys.stderr)
        sys.exit(1)

    # If only one option available, return it automatically
    if len(options) == 1:
        if options[0].startswith('summary'):
            return 'summary'
        else:
            return 'transcription'

    # Multiple options - let user choose with fzf
    fzf_input = '\n'.join(options)

    fzf_command = [
        'fzf',
        '--height=40%',
        '--reverse',
        '--border',
        '--header=What do you want to retrieve?',
        '--prompt=Type > ',
    ]

    try:
        result = subprocess.run(
            fzf_command,
            input=fzf_input,
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            # User cancelled
            sys.exit(0)

        # Extract type from selection
        selected = result.stdout.strip()
        if selected.startswith('summary'):
            return 'summary'
        else:
            return 'transcription'

    except Exception as e:
        print(f"Error during selection: {e}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def format_text_with_linebreaks(text: str) -> str:
    """
    Format text with logical line breaks for better readability.

    Splits on sentence boundaries (. ! ?) and wraps long sentences
    at word boundaries if they exceed 100 characters.

    Args:
        text: Raw text (transcription or summary)

    Returns:
        str: Formatted text with newlines
    """
    # Split on sentence endings while preserving the punctuation
    # Matches: period/question/exclamation followed by space(s)
    sentences = re.split(r'([.!?])\s+', text)

    formatted = []
    i = 0
    while i < len(sentences):
        # Reconstruct sentence with its punctuation
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]
            i += 2
        else:
            sentence = sentences[i]
            i += 1

        sentence = sentence.strip()
        if not sentence:
            continue

        # If sentence is longer than 100 chars, wrap it at word boundaries
        if len(sentence) > 100:
            wrapped = textwrap.fill(sentence, width=100, break_long_words=False)
            formatted.append(wrapped)
        else:
            formatted.append(sentence)

    return '\n'.join(formatted)


def output_to_stdout(content: str) -> None:
    """
    Print content to stdout (can be piped).

    Formats text with line breaks for better readability with head/tail/less.

    Args:
        content: The text to output
    """
    formatted = format_text_with_linebreaks(content)
    print(formatted)


def output_to_clipboard(content: str) -> None:
    """
    Copy content to system clipboard using pbcopy (macOS).

    For Linux, you might use xclip or xsel instead.

    Args:
        content: The text to copy to clipboard
    """
    formatted = format_text_with_linebreaks(content)

    try:
        subprocess.run(
            ['pbcopy'],
            input=formatted,
            text=True,
            check=True
        )
        print("✓ Copied to clipboard!", file=sys.stderr)

    except FileNotFoundError:
        print("Error: pbcopy not found. Are you on macOS?", file=sys.stderr)
        print("For Linux, install xclip: sudo apt install xclip", file=sys.stderr)
        print("\nContent output to stdout instead:", file=sys.stderr)
        print(content)
    except Exception as e:
        print(f"Error copying to clipboard: {e}", file=sys.stderr)
        print("\nContent output to stdout instead:", file=sys.stderr)
        print(content)


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """
    Main entry point for the transcript CLI tool.

    Workflow:
    1. Parse command line arguments
    2. Check dependencies (fzf)
    3. Fetch videos from database
    4. Let user select video with fzf
    5. Determine content type (from flag or user choice)
    6. Fetch content from database
    7. Output to stdout or clipboard
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Retrieve transcriptions and summaries from your YouTube video database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  transcript                          # Interactive mode
  transcript --summary                # Get summary (still select video)
  transcript --full                   # Get full transcription
  transcript --clipboard              # Copy to clipboard
  transcript --summary --clipboard    # Get summary and copy to clipboard
  transcript | pbcopy                 # Pipe to clipboard yourself
        """
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Get summary (skip content type selection)'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Get full transcription (skip content type selection)'
    )

    parser.add_argument(
        '--clipboard',
        action='store_true',
        help='Copy result to clipboard instead of stdout'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.summary and args.full:
        print("Error: Cannot use both --summary and --full", file=sys.stderr)
        sys.exit(1)

    # Check if fzf is installed
    if not check_fzf_installed():
        print("Error: fzf is not installed.", file=sys.stderr)
        print("Install it with: brew install fzf", file=sys.stderr)
        sys.exit(1)

    # Fetch all videos from database
    videos = fetch_all_videos()

    # Let user select a video with fzf
    video_id = select_video_with_fzf(videos)

    if video_id is None:
        print("Cancelled.", file=sys.stderr)
        sys.exit(0)

    # Determine content type
    if args.summary:
        content_type = 'summary'
    elif args.full:
        content_type = 'transcription'
    else:
        # Ask user with fzf
        content_type = select_content_type_with_fzf(video_id)

    # Fetch the content
    content = fetch_video_content(video_id, content_type)

    # Output the content
    if args.clipboard:
        output_to_clipboard(content)
    else:
        output_to_stdout(content)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(0)
