import os
import subprocess
import logging
import random
import json
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def get_video_info(url: str) -> dict:
    """
    Extract video metadata without downloading the video.

    Args:
        url: YouTube video URL

    Returns:
        dict with video info (title, duration, etc.)
    """
    try:
        bash_command = [
            "yt-dlp",
            "--dump-json",
            "--no-warnings",
            "--no-playlist",
            url
        ]

        logger.info(f"Fetching video info for {url}")
        process = subprocess.run(
            bash_command,
            check=True,
            capture_output=True,
            text=True
        )

        video_info = json.loads(process.stdout)

        return {
            'title': video_info.get('title', 'Unknown Title'),
            'duration': video_info.get('duration', 0),
            'uploader': video_info.get('uploader', 'Unknown'),
            'view_count': video_info.get('view_count', 0),
            'upload_date': video_info.get('upload_date', ''),
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error fetching video info: {e.stderr}")
        raise Exception(f"Failed to fetch video info: {e.stderr}")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing video info JSON: {str(e)}")
        raise Exception(f"Failed to parse video info")
    except Exception as e:
        logger.error(f"Error in get_video_info: {str(e)}")
        raise


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    parsed_url = urlparse(url)

    if 'youtube.com' in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [None])[0]
    elif 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.lstrip('/')

    raise ValueError("Invalid YouTube URL")


def download_video_audio(url: str, audio_path: str) -> str:
    """
    Download audio from a YouTube video

    Args:
        url: YouTube video URL
        audio_path: Directory to save the audio file

    Returns:
        Filename (without extension) of the downloaded audio
    """
    try:
        # Extract video ID to use as filename
        video_id = extract_video_id(url)
        filename = f"video_{video_id}"

        # Ensure audio directory exists
        os.makedirs(audio_path, exist_ok=True)

        output_path = os.path.join(audio_path, f"{filename}.wav")

        # Check if file already exists
        if os.path.exists(output_path):
            logger.info(f"File {output_path} already exists, creating duplicate with random suffix")
            random_suffix = random.randint(1, 10000)
            filename = f"video_{video_id}_{random_suffix}"
            output_path = os.path.join(audio_path, f"{filename}.wav")

        # Download using yt-dlp (16-bit WAV at 16kHz for whisper.cpp)
        bash_command = [
            "yt-dlp",
            "--no-warnings",
            "-x",
            "--audio-format", "wav",
            "--postprocessor-args", "ffmpeg:-ar 16000 -ac 1",  # 16kHz mono
            "--output", output_path,
            url
        ]

        logger.info(f"Downloading audio from {url}")
        process = subprocess.run(
            bash_command,
            check=True,
            capture_output=True,
            text=True
        )

        logger.info(f"Audio downloaded successfully: {filename}")
        return filename

    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading video: {e.stderr}")
        raise Exception(f"Failed to download video: {e.stderr}")
    except Exception as e:
        logger.error(f"Error in download_video_audio: {str(e)}")
        raise
