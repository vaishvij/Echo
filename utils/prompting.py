import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DESCRIPTION_FOLDER = "person_description"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key = GROQ_API_KEY)

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

    Use warm, comforting, emotionally intelligent replies. Never say you're an AI or a chatbot. Keep responses to 1-2 sentences only when speaking in voice mode.
    """
    return prompt

def query_llm(system_prompt, user_input, history=None):
    if history is None:
        history = []

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=512
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[ERROR] LLM call failed: {str(e)}"
    
def query_llm_stream(system_prompt, user_input, history=None):
    #Yields response sentence by sentence for streaming TTS pipeline
    if history is None:
        history = []
    
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_input})

    try:
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=512,
            stream=True
        )

        buffer = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            buffer += delta
            # Yield complete sentences as they form (includes Hindi danda)
            while any(p in buffer for p in [".", "!", "?", "।"]):
                for punct in [".", "!", "?", "।"]:
                    idx = buffer.find(punct)
                    if idx != -1:
                        yield buffer[:idx + 1].strip()
                        buffer = buffer[idx + 1:]
                        break
        if buffer.strip():
            yield buffer.strip()
    except Exception as e:
        yield f"[ERROR] Streaming failed: {str(e)}"