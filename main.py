import os
import subprocess
import time
import logging
from typing import Tuple
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import argparse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants
DEST_PATH = os.path.abspath("/Users/diegoguisande/Desktop/PARA/Projects_1/youtube_summary_py")
AUDIO_PATH = os.path.join(DEST_PATH, "audio")
TRANSCRIPTION_PATH = os.path.join(DEST_PATH, "transcriptions")
OBSIDIAN_BASE_PATH = "/Users/diegoguisande/Library/Mobile Documents/iCloud~md~obsidian/Documents/Second Brain/PARA"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YouTube Video Summarizer")
    parser.add_argument("--url", help="YouTube video URL", required=True)
    parser.add_argument("--filename", help="Output filename (without extension)", required=True)
    parser.add_argument("--dest", type=int, choices=[1, 2, 3, 4], help="Destination folder (1: Projects, 2: Areas, 3: Resources, 4: Archives)", required=True)
    parser.add_argument("--keep", help="if you want to keep the audio and raw transcription")
    return parser.parse_args()


def download_video_audio(url: str, filename: str) -> str:
    os.makedirs(AUDIO_PATH, exist_ok=True)
    output_path = os.path.join(AUDIO_PATH, f"{filename}.mp3")

    if os.path.exists(output_path):
        raise FileExistsError(f"File {output_path} already exists")

    bash_command = f"yt-dlp --progress -x --audio-format mp3 --output {output_path} {url}"

    with tqdm(total=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
        pbar.set_description("Downloading video")
        process = subprocess.Popen(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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


def transcribe_mp3_file(filename: str) -> Tuple[OpenAI, str]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    audio_file_path = os.path.join(AUDIO_PATH, f"{filename}.mp3")

    with open(audio_file_path, "rb") as audio_file, tqdm(total=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
        pbar.set_description("Transcribing audio")
        # TODO: add a spinning ASCII wheel instead of using tqdm
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        pbar.update(100)

    os.makedirs(TRANSCRIPTION_PATH, exist_ok=True)
    with open(os.path.join(TRANSCRIPTION_PATH, f"{filename}.txt"), 'w') as file:
        file.write(transcription.text)

    return client, transcription.text


def ask_gpt_for_summary(client: OpenAI, transcript: str, url: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. You are helping me summarize and write actionable insights from transcriptions of youtube videos."},
            {"role": "user", "content": f"Hello! Can you help me summarize and write a detailed, yet concise document from this transcript? \n {transcript}, also at the bottom of the summary can you put this url: {url} underneath a h2 md heading like this ![](<insert-url-here>) "}
        ]
    )
    return completion.choices[0].message.content


def save_file_to_obsidian(location: int, transcript: str, filename: str) -> None:
    folder_names = {1: "Projects", 2: "Areas", 3: "Resources", 4: "Archives"}
    folder_name = folder_names.get(location, "Archives")  # Default to Archives if invalid input
    obsidian_path = os.path.join(OBSIDIAN_BASE_PATH, folder_name)

    os.makedirs(obsidian_path, exist_ok=True)
    with open(os.path.join(obsidian_path, f"{filename}.md"), "w") as ai_file:
        ai_file.write(transcript)

    logging.info(f"File saved to Obsidian inside of {obsidian_path}")

    logging.info(f"deleting audio and raw transcription of {filename}")

    os.remove(f"{AUDIO_PATH}/{filename}.mp3")
    os.remove(f"{TRANSCRIPTION_PATH}/{filename}.txt")


def main():
    args = parse_arguments()

    try:
        file_name = download_video_audio(args.url, args.filename)
        client, transcription = transcribe_mp3_file(file_name)
        summary = ask_gpt_for_summary(client, transcription, args.url)
        save_file_to_obsidian(args.dest, summary, file_name)
        logging.info("Process completed successfully")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
