import os
import subprocess
import time
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import requests  # for simulating network request progress

load_dotenv()

dest_path = os.path.abspath("/Users/diegoguisande/Desktop/PARA/Projects_1/youtube_summary_py")


def pick_dest_folder() -> int:
    para_folder: str = input(
        "\n Where do you want to put the file? (Projects (1), Areas (2), Resources (3), Archives (4))\n"
    )
    para_choice = int(para_folder)
    if type(para_choice) is not int:
        raise Exception("\n don't add .mp3, just the filename")
    else:
        return para_choice


def recieve_filename() -> str:
    filename: str = input("what do you want the summary/audio to be named?... (don't put extension)\n")
    if ".mp3" not in filename:
        return filename
    else:
        raise Exception("\n don't add .mp3, just the filename")


def recieve_video_url() -> str:
    print("hello! Welcome to the Youtube-Summary-Tool")
    video: str = input("Please enter a video url... \n")
    if "https://youtu.be" in video or "youtube" in video:
        return video
    else:
        raise Exception("not a url \n needs .com or www")


def download_video_audio(url: str, filename: str) -> str:
    current_pth = os.getcwd()
    if os.path.exists(f'{current_pth}/{filename}.mp3'):
        raise Exception("\n There is a file with the same name in audio/")
    print(f"url is {url}")
    bash_command = f"yt-dlp --progress -x --audio-format mp3 --output {filename}.mp3 {url}"
    print(bash_command)
    os.chdir("/Users/diegoguisande/Desktop/PARA/Projects_1/youtube_summary_py/audio")

    # Execute the bash command and capture the output
    with tqdm(total=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
        pbar.set_description("Downloading video")
        process = subprocess.Popen(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            output = process.stdout.readline().decode()
            if process.poll() is not None and output == '':
                break
            if output:
                print(output.strip())
                pbar.update(10)  # Simulate progress update, adjust as necessary
            time.sleep(0.5)  # Simulate delay
        pbar.update(100 - pbar.n)  # Ensure the bar completes
    return filename


def transcribe_mp3_file(filename: str, dest_path=dest_path) -> tuple[OpenAI, str]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    audio_file = open(f"{dest_path}/audio/{filename}.mp3", "rb")

    with tqdm(total=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
        pbar.set_description("Transcribing audio")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        pbar.update(100)  # Complete the progress bar

    with open(f"{dest_path}/transcriptions/{filename}.txt", 'w') as file:
        file.write(transcription.text)

    audio_file.close()
    return client, transcription.text


def ask_gpt_for_summary(client, transcript: str, url: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. You are helping me summarize and write actionable insights from transcriptions of youtube videos."},
            {"role": "user", "content": f"Hello! Can you help me summarize and write a detailed, yet concise document from this transcript? \n {transcript}, also at the bottom of the summary can you put this url: {url} underneath a h2 md heading like this ![](<insert-url-here>) "}
        ]
    )
    return completion.choices[0].message.content


def save_file_to_obsidian(location: int, transcript: str, filename: str) -> None:
    local_obsidian_path = "/Users/diegoguisande/Library/Mobile Documents/iCloud~md~obsidian/Documents/Second Brain/PARA"
    print(f"obsidian path: {local_obsidian_path}")
    if location == 1:
        local_obsidian_path = local_obsidian_path + "/Projects"
    elif location == 2:
        local_obsidian_path = local_obsidian_path + "/Areas"
    elif location == 3:
        local_obsidian_path = local_obsidian_path + "/Resources"
    else:
        local_obsidian_path = local_obsidian_path + "/Archives"
    summary_text = str(transcript)
    with open(f"{local_obsidian_path}/{filename}.md", "w") as ai_file:
        ai_file.write(summary_text)
    print(f"file saved to Obsidian!! inside of {local_obsidian_path}")


def main():
    url = recieve_video_url()
    filename = recieve_filename()
    obsidian_dest = pick_dest_folder()
    file_name = download_video_audio(url, filename)
    client, transcription = transcribe_mp3_file(file_name)
    summary = ask_gpt_for_summary(client, transcription, url)
    save_file_to_obsidian(obsidian_dest, summary, file_name)


if __name__ == "__main__":
    main()
