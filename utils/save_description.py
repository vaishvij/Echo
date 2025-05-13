import os
import json

DESCRIPTION_FOLDER = "person_description"
os.makedirs(DESCRIPTION_FOLDER, exist_ok=True)

def save_person_description(person_id, data):
    filepath = os.path.join(DESCRIPTION_FOLDER, f"{person_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)