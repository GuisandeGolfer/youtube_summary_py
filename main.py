import os
import random
import subprocess
import time
import logging
import json
from save_transcript_to_db import NewFileHandler
from typing import Tuple, Dict
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
from utils import split_transcription
import argparse
import ffmpeg

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

'''
TODO: make these constants relative to where the script is running, or if these
    are not defined when main() runs
    make run a prompt method run that will fill in these values,
    and then save their response in the yml file.

    maybe try sqlite as a persistent data store?
'''


# Constants
DEST_PATH = os.path.abspath(
    "/Users/diegoguisande/Desktop/PARA/Projects_1/youtube_summary_py")
AUDIO_PATH = os.path.join(DEST_PATH, "audio")
TRANSCRIPTION_PATH = os.path.join(DEST_PATH, "transcriptions")
OBSIDIAN_BASE_PATH = "/Users/diegoguisande/Desktop/obsidian/"


def format_json(prompt_file: Dict[str, Dict[str, str]], transcript: str, url: str):
    data_formatting = { 'transcript': transcript, 'url': url }

    try:
        content = prompt_file["normal"]["content"].format(**data_formatting)
    except KeyError:
        raise KeyError("key error with prompt_file")

    return {'role': "user", 'content': content}


def load_prompt_info(transcript: str, url: str):
    with open("prompt.json", "r") as file:
        data = json.load(file)

    return format_json(data, transcript, url) 


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YouTube Video Summarizer")
    parser.add_argument("--url", help="YouTube video URL", required=True)
    parser.add_argument(
        "--filename", help="Output filename (without extension)", required=True)
    parser.add_argument("--dest", type=int, choices=[
                        1, 2, 3, 4], help="Destination folder (1: Projects, 2: Areas, 3: Resources, 4: Archives)", required=True)
    #parser.add_argument("--type", help="The type of summary you are asking OpenAI", required=True)
    parser.add_argument(
        "--keep", help="if you want to keep the audio and raw transcription")
    return parser.parse_args()


def download_video_audio(url: str, filename: str) -> str:
    os.makedirs(AUDIO_PATH, exist_ok=True)
    output_path = os.path.join(AUDIO_PATH, f"{filename}.mp3")

    if os.path.exists(output_path):
        # raise FileExistsError(f"File {output_path} already exists")
        print(
            f"File {output_path} already exists\nCreating duplicate with different name")
        # Generates a random number between 1 and 100
        random_num = random.randint(1, 100)
        output_path = os.path.join(AUDIO_PATH, f"{filename}-{random_num}.mp3")

    bash_command = f"yt-dlp --progress -x --audio-format mp3 --output {output_path} {url}"

    with tqdm(total=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
        pbar.set_description("Downloading video")
        process = subprocess.Popen(
            bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            output = process.stdout.readline().decode()
            if process.poll() is not None and output == '':
                break
            if output:
                logging.info(output.strip())
                pbar.update(10)  # Simulate progress update
            time.sleep(0.5)
        pbar.update(100 - pbar.n)  # Ensure the bar completes

    return filename


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

def transcribe_audio_segments(client: OpenAI, segments: list) -> str:
    full_transcription = []

    for segment in segments:
        audio_file_path = os.path.join(AUDIO_PATH, segment)
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
            )
            full_transcription.append(transcription.text)

    return " ".join(full_transcription)

def transcribe_mp3_file(filename: str) -> Tuple[OpenAI, str]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    segments = split_audio_file(filename)
    full_transcription = transcribe_audio_segments(client, segments)

    os.makedirs(TRANSCRIPTION_PATH, exist_ok=True)
    with open(os.path.join(TRANSCRIPTION_PATH, f"{filename}.txt"), 'w') as file:
        file.write(full_transcription)

    return client, full_transcription


def ask_gpt_for_summary(client: OpenAI, transcript: str, url: str) -> str:
    max_tokens = 2048  # Adjust based on the model's token limit
    chunks = split_transcription(transcript, max_tokens)
    summaries = []

    for chunk in chunks:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                load_prompt_info(chunk, url),
                load_prompt_info(chunk, url),
            ]
        )
        summaries.append(completion.choices[0].message.content)

    # Combine all summaries into a final summary
    final_summary = "\n".join(summaries)
    print(final_summary)
    return final_summary


def save_file_to_obsidian(location: int, transcript: str, filename: str) -> None:
    folder_names = {1: "Projects", 2: "Areas", 3: "Resources", 4: "Archives"}
    # Default to Archives if invalid input
    folder_name = folder_names.get(location, "Archives")
    obsidian_path = os.path.join(OBSIDIAN_BASE_PATH, folder_name)

    os.makedirs(obsidian_path, exist_ok=True)
    with open(os.path.join(obsidian_path, f"{filename}.md"), "w") as ai_file:
        ai_file.write(transcript)

    logging.info(f"File saved to Obsidian inside of {obsidian_path}")

    logging.info(f"deleting audio of {filename}")

    os.remove(f"{AUDIO_PATH}/{filename}.mp3")
    # os.remove(f"{TRANSCRIPTION_PATH}/{filename}.txt")

def main():
    args = parse_arguments()

    try:
        file_name = download_video_audio(args.url, args.filename)
        client, transcription = transcribe_mp3_file(file_name)
        summary = ask_gpt_for_summary(client, transcription, args.url)
        save_file_to_obsidian(args.dest, summary, file_name)

        logging.info("Process completed successfully")
        logging.info("Saving video transcription data to sqlite database")

        file_handler = NewFileHandler("./transcriptions.db", transcription, args.url)

        file_handler.insert_transcription_into_db()


    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
