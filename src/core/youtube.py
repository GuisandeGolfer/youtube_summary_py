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


# Quality format mappings for yt-dlp
QUALITY_FORMATS = {
    'best': 'bestvideo+bestaudio/best',
    '1080p': 'bestvideo[height<=1080]+bestaudio/best',
    '720p': 'bestvideo[height<=720]+bestaudio/best',
    '480p': 'bestvideo[height<=480]+bestaudio/best',
    '360p': 'bestvideo[height<=360]+bestaudio/best',
    'audio_only': 'bestaudio/best'
}


def download_video_full(url: str, downloads_path: str, quality: str = 'best') -> dict:
    """
    Download complete YouTube video (video + audio merged)

    Args:
        url: YouTube video URL
        downloads_path: Directory to save the video file
        quality: Video quality ('best', '1080p', '720p', '480p', '360p', 'audio_only')

    Returns:
        dict with download info (filepath, title, size, format)
    """
    try:
        # Validate quality parameter
        if quality not in QUALITY_FORMATS:
            logger.warning(f"Invalid quality '{quality}', defaulting to 'best'")
            quality = 'best'

        # Ensure downloads directory exists
        os.makedirs(downloads_path, exist_ok=True)

        # Get video info first to use proper title
        video_info = get_video_info(url)
        title = video_info['title']
        video_id = extract_video_id(url)

        # Sanitize title for filename (remove special characters)
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:100]  # Limit length

        # Create filename with video_id to ensure uniqueness
        base_filename = f"{safe_title}_[{video_id}]"

        # Determine output extension based on quality
        if quality == 'audio_only':
            output_extension = 'mp3'
            output_template = os.path.join(downloads_path, f"{base_filename}.%(ext)s")
        else:
            output_extension = 'mp4'
            output_template = os.path.join(downloads_path, f"{base_filename}.%(ext)s")

        # Build yt-dlp command
        bash_command = [
            "yt-dlp",
            "--no-warnings",
            "-f", QUALITY_FORMATS[quality],
            "--output", output_template,
            url
        ]

        # Add format merging for video downloads
        if quality != 'audio_only':
            bash_command.extend([
                "--merge-output-format", "mp4"
            ])
        else:
            # For audio only, extract and convert to mp3
            bash_command.extend([
                "-x",
                "--audio-format", "mp3"
            ])

        logger.info(f"Downloading video from {url} with quality={quality}")
        logger.info(f"Command: {' '.join(bash_command)}")

        process = subprocess.run(
            bash_command,
            check=True,
            capture_output=True,
            text=True
        )

        # Determine actual output file
        if quality == 'audio_only':
            output_file = os.path.join(downloads_path, f"{base_filename}.mp3")
        else:
            output_file = os.path.join(downloads_path, f"{base_filename}.mp4")

        # Get file size
        file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
        file_size_mb = file_size / (1024 * 1024)  # Convert to MB

        logger.info(f"Video downloaded successfully: {output_file} ({file_size_mb:.2f} MB)")

        return {
            'filepath': output_file,
            'filename': os.path.basename(output_file),
            'title': title,
            'size_bytes': file_size,
            'size_mb': round(file_size_mb, 2),
            'quality': quality,
            'video_id': video_id,
            'format': output_extension
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading video: {e.stderr}")
        raise Exception(f"Failed to download video: {e.stderr}")
    except Exception as e:
        logger.error(f"Error in download_video_full: {str(e)}")
        raise


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
