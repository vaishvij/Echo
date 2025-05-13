import os
import json

DESCRIPTION_FOLDER = "person_description"

def generate_system_prompt(person_id):
    filepath = os.path.join(DESCRIPTION_FOLDER, f"{person_id}.json")

    print(f"[DEBUG] Received person_id: {person_id}")
    print(f"[DEBUG] Full path: {filepath}")
    print(f"[DEBUG] File exists? {os.path.exists(filepath)}")

    if not os.path.exists(filepath):
        print(f"[DEBUG] JSON file not found at: {filepath}")
        return "You are a kind and warm digital companion."
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract components
    relationship = data.get("relationship", "someone close")
    language = data.get("language", "en")
    personality = ", ".join(data.get("personality", []))
    memories = data.get("memories", [])
    phrases = data.get("phrases", [])

     # Build memory lines
    memory_lines = "\n".join([f"• {m}" for m in memories])
    phrase_lines = "\n".join([f'• Say: "{p}"' for p in phrases])

    # Final prompt template
    prompt = f"""
    You are a digital representation of the user's {relationship}.
    You are {personality}.
    Speak in {language}.
    You remember things like:
    {memory_lines}

    Sometimes you say comforting phrases like:
    {phrase_lines}

    Use warm, emotionally intelligent, short replies. Never say you're an AI or a chatbot.
    """
    return prompt