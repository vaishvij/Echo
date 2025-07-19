import os
import json
import requests

DESCRIPTION_FOLDER = "person_description"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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

    Use warm, comforting, emotionally intelligent replies. Never say you're an AI or a chatbot.
    """
    return prompt

def query_llm(system_prompt, user_input, history=[]):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization" : f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type" : "application/json"
    }

    messages = [{"role":"system", "content":system_prompt}]
    messages += history
    messages.append({"role":"user", "content":user_input})

    payload = {
        "model" : "moonshotai/kimi-k2:free",
        "messages" : messages,
        "temperature" : 0.7,
        "max-tokens" : 512
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"[ERROR] LLM call failed : {str(e)}"