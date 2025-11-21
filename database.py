import sqlite3
import logging
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def create_videos_table(cursor):
    """
    Create videos table if it doesn't exist

    Args:
        cursor: SQLite cursor object
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            video_length INTEGER,
            channel TEXT,
            transcription TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Videos table ensured to exist")


def extract_video_info(video_url: str) -> dict:
    """
    Extract video information using yt-dlp

    Args:
        video_url: YouTube video URL

    Returns:
        Dictionary containing video information
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(video_url, download=False)

        return {
            'title': video_info.get('title', 'Unknown Title'),
            'url': video_info.get('webpage_url', video_url),
            'video_length': video_info.get('duration', 0),
            'channel': video_info.get('uploader', 'Unknown Channel')
        }

    except Exception as e:
        logger.error(f"Error extracting video info: {str(e)}")
        # Return default values if extraction fails
        return {
            'title': 'Unknown Title',
            'url': video_url,
            'video_length': 0,
            'channel': 'Unknown Channel'
        }


def save_transcription_to_db(db_path: str, transcription: str, video_url: str, summary: str = None):
    """
    Save video transcription and summary to SQLite database

    Args:
        db_path: Path to SQLite database file
        transcription: Video transcription text
        video_url: YouTube video URL
        summary: Video summary text (optional)
    """
    conn = None

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        create_videos_table(cursor)

        # Extract video information
        logger.info(f"Extracting video information for: {video_url}")
        video_info = extract_video_info(video_url)

        # Check if video already exists in database
        cursor.execute(
            "SELECT id FROM videos WHERE url = ?",
            (video_info['url'],)
        )
        existing = cursor.fetchone()

        if existing:
            logger.warning(f"Video already exists in database: {video_info['title']}")
            # Update existing record
            cursor.execute("""
                UPDATE videos
                SET transcription = ?,
                    summary = ?,
                    title = ?,
                    video_length = ?,
                    channel = ?
                WHERE url = ?
            """, (
                transcription,
                summary,
                video_info['title'],
                video_info['video_length'],
                video_info['channel'],
                video_info['url']
            ))
            logger.info(f"Updated existing record for: {video_info['title']}")
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO videos (title, url, video_length, channel, transcription, summary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                video_info['title'],
                video_info['url'],
                video_info['video_length'],
                video_info['channel'],
                transcription,
                summary
            ))
            logger.info(f"Inserted new record for: {video_info['title']}")

        conn.commit()
        logger.info("Transcription saved to database successfully")

    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise Exception(f"Failed to save to database: {str(e)}")

    except Exception as e:
        logger.error(f"Error saving transcription to database: {str(e)}")
        raise

    finally:
        if conn:
            conn.close()


def get_all_transcriptions(db_path: str) -> list:
    """
    Retrieve all transcriptions from database

    Args:
        db_path: Path to SQLite database file

    Returns:
        List of dictionaries containing video data
    """
    conn = None

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, url, video_length, channel, summary, created_at
            FROM videos
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Error retrieving transcriptions: {str(e)}")
        return []

    finally:
        if conn:
            conn.close()
