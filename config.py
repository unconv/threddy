from pathlib import Path
import openai
import json
import os

def save(settings_file, settings):
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=4)

def load(settings_file):
    settings_file = Path(__file__).parent / settings_file
    if os.path.exists(settings_file):
        with open(settings_file, "r") as f:
            settings = json.load(f)
    else:
        settings = {}

    if "assistant_id" not in settings:
        print("INFO: Creating an assistant")
        assistant = openai.beta.assistants.create(
            model="gpt-3.5-turbo-1106",
            name="Threddy 2",
            tools=[
                {"type": "retrieval"},
            ]
        )
        settings["assistant_id"] = assistant.id
        save(settings_file, settings)

    return settings
