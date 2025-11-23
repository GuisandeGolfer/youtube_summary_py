import os
import logging
import subprocess
import json

logger = logging.getLogger(__name__)


def split_audio_file(audio_path: str, filename: str, segment_duration: int = 1400) -> list:
    """
    Split audio file into smaller segments for transcription

    Args:
        audio_path: Directory containing the audio file
        filename: Name of the audio file (without extension)
        segment_duration: Duration of each segment in seconds (default: ~23 minutes)

    Returns:
        List of segment filenames
    """
    audio_file_path = os.path.join(audio_path, f"{filename}.wav")
    segments = []

    try:
        # Get the total duration of the audio file using ffprobe
        probe_command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            audio_file_path
        ]

        probe_result = subprocess.run(
            probe_command,
            capture_output=True,
            text=True,
            check=True
        )

        probe_data = json.loads(probe_result.stdout)
        total_duration = float(probe_data['format']['duration'])

        # Calculate the number of segments
        num_segments = int(total_duration // segment_duration) + 1

        logger.info(f"Splitting audio into {num_segments} segments")

        for i in range(num_segments):
            start_time = i * segment_duration
            segment_filename = f"{filename}_part{i}.wav"
            segment_path = os.path.join(audio_path, segment_filename)

            # Use ffmpeg to extract the segment (16-bit WAV at 16kHz for whisper.cpp)
            ffmpeg_command = [
                'ffmpeg',
                '-i', audio_file_path,
                '-ss', str(start_time),
                '-t', str(segment_duration),
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',      # Mono audio
                '-c:a', 'pcm_s16le',  # 16-bit PCM
                '-y',  # Overwrite output files
                segment_path
            ]

            subprocess.run(
                ffmpeg_command,
                check=True,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )

            segments.append(segment_filename)
            logger.info(f"Created segment: {segment_filename}")

        return segments

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ffmpeg/ffprobe: {str(e)}")
        raise Exception("ffmpeg or ffprobe command failed. Make sure ffmpeg is installed (brew install ffmpeg)")
    except Exception as e:
        logger.error(f"Error splitting audio file: {str(e)}")
        raise


def transcribe_audio_segments(audio_path: str, segments: list, model_path: str) -> str:
    """
    Transcribe audio segments using whisper.cpp

    Args:
        audio_path: Directory containing audio segments
        segments: List of segment filenames
        model_path: Path to whisper.cpp model file

    Returns:
        Complete transcription text
    """
    WHISPER_CLI = "/Users/diegoguisande/Desktop/PARA/Resources_3/whisper.cpp/build/bin/whisper-cli"
    LIB_PATHS = ":".join([
        "/Users/diegoguisande/Desktop/PARA/Resources_3/whisper.cpp/build/src",
        "/Users/diegoguisande/Desktop/PARA/Resources_3/whisper.cpp/build/ggml/src",
        "/Users/diegoguisande/Desktop/PARA/Resources_3/whisper.cpp/build/ggml/src/ggml-blas",
        "/Users/diegoguisande/Desktop/PARA/Resources_3/whisper.cpp/build/ggml/src/ggml-metal"
    ])

    full_transcription = []

    for i, segment in enumerate(segments, 1):
        logger.info(f"Transcribing segment {i}/{len(segments)}: {segment}")

        audio_file_path = os.path.join(audio_path, segment)

        try:
            # Set up environment with library paths
            env = os.environ.copy()
            env["DYLD_LIBRARY_PATH"] = LIB_PATHS

            # Run whisper-cli
            result = subprocess.run(
                [
                    WHISPER_CLI,
                    "-m", model_path,
                    "-f", audio_file_path,
                    "-nt",           # No timestamps in output
                    "-l", "en",      # Language (English)
                    "-t", "4"        # Number of threads
                ],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )

            # whisper-cli outputs to stdout
            transcription_text = result.stdout.strip()
            full_transcription.append(transcription_text)

        except subprocess.CalledProcessError as e:
            logger.error(f"Error transcribing segment {segment}: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error transcribing segment {segment}: {str(e)}")
            raise

    return " ".join(full_transcription)


def cleanup_audio_files(audio_path: str, filename: str):
    """
    Delete audio files after transcription

    Args:
        audio_path: Directory containing audio files
        filename: Base filename to clean up
    """
    try:
        # Find all files matching the filename pattern
        import glob
        pattern = os.path.join(audio_path, f"{filename}*.wav")
        files_to_delete = glob.glob(pattern)

        for file_path in files_to_delete:
            os.remove(file_path)
            logger.info(f"Deleted: {file_path}")

    except Exception as e:
        logger.warning(f"Error cleaning up audio files: {str(e)}")


def transcribe_audio_file(filename: str, audio_path: str) -> str:
    """
    Main function to transcribe an audio file using whisper.cpp

    Args:
        filename: Name of the audio file (without extension)
        audio_path: Directory containing the audio file

    Returns:
        Complete transcription text
    """
    try:
        # Path to whisper.cpp model (ggml-base.en.bin)
        model_path = "/Users/diegoguisande/Desktop/PARA/Resources_3/whisper.cpp/models/ggml-base.en.bin"

        if not os.path.exists(model_path):
            raise ValueError(f"Whisper model not found at {model_path}")

        # Split audio file into segments
        segments = split_audio_file(audio_path, filename)

        # Transcribe all segments using whisper.cpp
        full_transcription = transcribe_audio_segments(audio_path, segments, model_path)

        # Clean up audio files after transcription
        cleanup_audio_files(audio_path, filename)

        logger.info("Transcription completed successfully")
        return full_transcription

    except Exception as e:
        logger.error(f"Error in transcribe_audio_file: {str(e)}")
        raise
