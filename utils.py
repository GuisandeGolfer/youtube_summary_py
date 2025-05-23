# install with "pyyam"
from typing import Dict
import json
import os, glob

with open("prompt.json") as file:

    context = {
        'transcript': "INSERTED TEXT",
        'url': "INSERTED URL",
    }

    data = json.load(file)

    print(f"yaml data: {data}")

    formatted = data["normal"]["content"].format(**context)


def split_transcription(transcription: str, max_tokens: int) -> list:
# split transcription into max chunk sizes
    words = transcription.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(current_chunk) + len(word) + 1 > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
        current_chunk.append(word)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


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


def delete_files_with_name(base_path: str, filename: str):
    # Construct the pattern to match files with the exact name and any extension
    pattern = os.path.join(base_path, f"{filename}*.mp3")
    
    # Use glob to find all files matching the pattern
    files_to_delete = glob.glob(pattern)
    print(files_to_delete)
    
    # Delete each file found
    for file_path in files_to_delete:
        os.remove(file_path)
        print(f"Deleted: {file_path}")
