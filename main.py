import os
import subprocess
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


dest_path = os.path.abspath(".")
# change the choices to accept:
# 1, 2, 3, 4 instead of asking them to type out the dest.


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
    filename: str = input("what do you want the audio to be named?... \n")

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
    # Example bash command to execute
    bash_command = f"yt-dlp -x --audio-format mp3 --output {filename}.mp3 {url}"

    print(bash_command)

    os.chdir("audio/")

    # Execute the bash command and capture the output
    output = subprocess.check_output(bash_command, shell=True)

    print(output.decode())

    return filename


def transcribe_mp3_file(filename: str, dest_path=dest_path) -> tuple[OpenAI, str]:

    client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
            )

    audio_file = open(f"{dest_path}/audio/{filename}.mp3", "rb")

    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )

    with open(f"{dest_path}/transcriptions/{filename}.txt", 'w') as file:
        file.write(transcription.text)

    audio_file.close()

    return client, transcription.text


def ask_gpt_for_summary(client, transcript: str) -> str:

    completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You are helping me summarize and write actionable insights from transcriptions of youtube videos."},
                {"role": "user", "content": f"Hello! Can you help me summarize and write a detailed, yet concise document from this transcript? \n {transcript}"}
                ]
            )

    return completion.choices[0].message.content


def save_file_to_obsidian(location: int, transcript: str, filename: str) -> None:
    # local_obsidian_path = os.path.abspath("../../../..")
    # TODO: instead of doing this bullshit below: just write out the full path name

    cmd_obsidian = subprocess.Popen(["which", "obsidian"], stdout=subprocess.PIPE)

    cmd_cut = subprocess.Popen(["cut", "-d", "'/'", "-f2-"], stdin=cmd_obsidian.stdout, stdout=subprocess.PIPE)

    cmd_obsidian.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.

    cmd_cut = cmd_cut.communicate()[0]

    print(cmd_cut.decode())

    # output = subprocess.check_output(command, shell=True)

    local_obsidian_path = cmd_cut.decode()

    # need to  fix this horrible reference
    print(local_obsidian_path)

    if location == 1:
        local_obsidian_path = local_obsidian_path + "/Projects"
    elif location == 2:
        local_obsidian_path = local_obsidian_path + "/Areas"
    elif location == 3:
        local_obsidian_path = local_obsidian_path + "/Resources"
    else:
        local_obsidian_path = local_obsidian_path + "/Archives"

    summary_text = str(transcript)

    # need to check if a file name or file already exists

    with open(f"{local_obsidian_path}/{filename}.md", "w") as ai_file:
        ai_file.write(summary_text)

    print(f"file saved to Obsidian!! inside of {local_obsidian_path}")


def main():
    url = recieve_video_url()
    filename = recieve_filename()

    obsidian_dest = pick_dest_folder()

    file_name = download_video_audio(url, filename)

    client, transcription = transcribe_mp3_file(file_name)

    summary = ask_gpt_for_summary(client, transcription)

    save_file_to_obsidian(obsidian_dest, summary, file_name)


if __name__ == "__main__":
    main()
