import ffmpeg
import os

DEST_PATH = os.path.abspath(
    "/Users/diegoguisande/Desktop/PARA/Projects_1/youtube_summary_py")
AUDIO_PATH = os.path.join(DEST_PATH, "audio")
TRANSCRIPTION_PATH = os.path.join(DEST_PATH, "transcriptions")
OBSIDIAN_BASE_PATH = "/Users/diegoguisande/Desktop/obsidian/"

def split_audio_file(filename: str, segment_duration: int = 1400) -> list:
    audio_file_path = os.path.join(AUDIO_PATH, f"{filename}.mp3")
    segments = []

    # Get the total duration of the audio file
    probe = ffmpeg.probe(audio_file_path)
    total_duration = float(probe['format']['duration'])

    # Calculate the number of segments
    num_segments = int(total_duration // segment_duration) + 1

    for i in range(num_segments):
        start_time = i * segment_duration
        segment_filename = f"{filename}_part{i}.mp3"
        segment_path = os.path.join(AUDIO_PATH, segment_filename)

        # Use ffmpeg to extract the segment
        ffmpeg.input(audio_file_path, ss=start_time, t=segment_duration).output(segment_path).run()

        segments.append(segment_filename)

    return segments


