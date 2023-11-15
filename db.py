from pathlib import Path
import json
import os

def save(db_file, database):
    with open(db_file, "w") as f:
        json.dump(database, f, indent=4)

def load(db_file):
    database_file = Path(__file__).parent / db_file
    if os.path.exists(database_file):
        with open(database_file, "r") as f:
            return json.load(f)
    else:
        return {
            "conversations": {}
        }