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

    print(formatted)
