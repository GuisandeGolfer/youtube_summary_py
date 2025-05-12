# install with "pyyam"
import json

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
