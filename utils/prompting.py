import os
import json
import requests
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

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


# Load Mistral locally
print("[INFO] Loading OpenHermes-2.5-Mistral-7B...")

model_id = "teknium/OpenHermes-2.5-Mistral-7B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")
chat_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)

def query_llm(system_prompt, user_input, history=[]):
    prompt = f"<|system|>\n{system_prompt}\n"

    for turn in history:
        if turn["role"] == "user":
            prompt += f"<|user|>\n{turn['content']}\n"
        elif turn["role"] == "assistant":
            prompt += f"<|assistant|>\n{turn['content']}\n"

    prompt += f"<|user|>\n{user_input}\n<|assistant|>\n"

    output = chat_pipeline(prompt, max_new_tokens=256, do_sample=True, temperature=0.7)[0]["generated_text"]
    reply = output.split("<|assistant|>\n")[-1].strip()

    return reply