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
import argparse


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
OBSIDIAN_BASE_PATH = "/Users/diegoguisande/Library/Mobile Documents/iCloud~md~obsidian/Documents/Second Brain/PARA"


def format_json(prompt_file: Dict[str, Dict[str, str]], detail_depth: str, transcript: str, url: str):
    data_formatting = { 'transcript': transcript, 'url': url }

    try:
        content = prompt_file[detail_depth]["content"].format(**data_formatting)
    except KeyError:
        raise KeyError("key error with prompt_file")

    return {'role': "user", 'content': content}


def load_prompt_info(detail_depth: str, transcript: str, url: str):
    if detail_depth not in ["normal", "detailed", "latin"]:
        raise ValueError("incorrect prompt data request")

    with open("prompt.json", "r") as file:
        data = json.load(file)

    return format_json(data, detail_depth, transcript, url) 


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YouTube Video Summarizer")
    parser.add_argument("--url", help="YouTube video URL", required=True)
    parser.add_argument(
        "--filename", help="Output filename (without extension)", required=True)
    parser.add_argument("--dest", type=int, choices=[
                        1, 2, 3, 4], help="Destination folder (1: Projects, 2: Areas, 3: Resources, 4: Archives)", required=True)
    parser.add_argument("--type", help="The type of summary you are asking OpenAI", required=True)
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


def transcribe_mp3_file(filename: str) -> Tuple[OpenAI, str]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    audio_file_path = os.path.join(AUDIO_PATH, f"{filename}.mp3")

    # TODO: this is where my script failed last

    with open(audio_file_path, "rb") as audio_file, tqdm(total=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
        pbar.set_description("Transcribing audio")
        # TODO: this is where my script failed last
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

# TODO: use gpt-4 instead of 3.5, missed some details in my last summary
# TODO: have a section inside of yaml that use can give specific details to look for in a certain video.


def ask_gpt_for_summary(client: OpenAI, transcript: str, url: str) -> str:
    # TODO: check load_prompt_info results manually
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
<<<<<<< HEAD
        messages=[  # TODO: move these over to yml files
            {"role": "system", "content": "You are a helpful assistant. You are helping me summarize and write actionable insights from transcriptions of youtube videos."},
            {"role": "user", "content": f"Hello! Can you help me summarize and write a detailed, yet concise document from this transcript? \n {transcript}, also at the bottom of the summary can you put this url: {url} underneath a h2 md heading like this ![](<insert-url-here>) "}
=======
        messages=[
            load_prompt_info("system", transcript, url),
            load_prompt_info("detailed", transcript, url),
>>>>>>> origin/main
        ]
    )
    return completion.choices[0].message.content


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
