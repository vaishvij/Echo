from flask import Flask, request, render_template, send_file, send_from_directory, jsonify, redirect, url_for, session
import os
from utils.audio_processing import process_audio
from utils.audio_processing import clone_voice_from_text
from utils.audio_processing import synthesize_voice
from utils.save_description import save_person_description
from utils.prompting import generate_system_prompt, query_llm
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/index')
def index():
    return render_template("index.html")

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER,exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_audio():
    audio = request.files['audio']
    person_id = request.form['person_id'].strip()
    filename = f"{person_id}.wav"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio.save(filepath)
    
    processed_path = os.path.join(PROCESSED_FOLDER, filename)
    process_audio(filepath,processed_path)

    return f"""
        <h2>Here’s your audio for ({person_id}):</h2>
        <audio controls autoplay>
            <source src="/uploads/{filename}" type="audio/wav">
        </audio>
        <br><br>
        <h2>Enhanced Audio:</h2>
        <audio controls autoplay>
            <source src="/processed/{filename}" type="audio/wav">
        </audio>
        <br><br>
        <form action="/synthesize" method="post">
            <input type="hidden" name="person_id" value="{person_id}">
            <label>Enter text to synthesize in the uploaded voice:</label><br>
            <textarea name="text" rows="3" cols="60" required></textarea><br><br>
            <button type="submit">Generate Cloned Voice</button>
        </form>
        <br><br>
        <a href="/">Upload Another</a>
    """
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/processed/<filename>')
def get_processed_audio(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

@app.route('/synthesize', methods=['POST'])
def synthesize():
    text_input = request.form['text']
    person_id = request.form['person_id']

    processed_path = os.path.join(PROCESSED_FOLDER,f"{person_id}.wav")
    embedding_path = processed_path.replace(".wav",".npy")

    output_filename = f"{person_id}.wav"
    output_path = os.path.join(PROCESSED_FOLDER, output_filename)

    #Generate speech in cloned voice
    clone_voice_from_text(text_input, processed_path, embedding_path, output_path)

    return f"""
        <h2>Input Text:</h2>
        <p>{text_input}</p>

        <h2>Cloned Voice Output:</h2>
        <audio controls autoplay>
            <source src="/processed/{output_filename}" type="audio/wav">
        </audio>
        <br><br>
        <a href="/">Clone Another</a>
    """

@app.route('/description')
def description_form():
    return render_template("description.html")

@app.route('/save_description', methods=['POST'])
def save_description():
    person_id = request.form['person_id']
    relationship = request.form['relationship']
    language = request.form['language']
    personality = request.form['personality'].split(",")
    memories = request.form['memories'].strip().splitlines()
    phrases = request.form['phrases'].strip().splitlines()

    profile_data = {
        "person_id": person_id,
        "relationship": relationship,
        "language": language,
        "personality": [trait.strip() for trait in personality],
        "memories": memories,
        "phrases": phrases
    }

    save_person_description(person_id, profile_data)

    return f"""
        <h3>Profile Saved for {person_id}!</h3>
        <a href="/start_chat/{person_id}">Start Chat</a> |
        <a href='/description'>Create Another</a> |
        <a href='/'>Home</a>
    """


@app.route('/preview_prompt/<person_id>')
def preview_prompt(person_id):
    prompt = generate_system_prompt(person_id)
    return f"<pre>{prompt}</pre>"


chat_history = {}

@app.route('/start_chat/<person_id>')
def start_chat(person_id):
    return render_template("textchat.html", person_id=person_id)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    person_id = data.get("person_id")
    user_input = data.get("message")

    print(f"[DEBUG] Received person_id: {person_id}")
    print(f"[DEBUG] Message: {user_input}")

    # Load system prompt
    system_prompt = generate_system_prompt(person_id)

    # Maintain history
    if person_id not in chat_history:
        chat_history[person_id] = []

    history = chat_history[person_id]

    response = query_llm(system_prompt, user_input, history)

    # Update chat history
    chat_history[person_id].append({"role": "user", "content": user_input})
    chat_history[person_id].append({"role": "assistant", "content": response})

    return jsonify({"reply": response})

@app.route("/voice_chat/<person_id>")
def voice_chat(person_id):
    display_name = person_id.replace("_", " ").title()  # For UI
    return render_template("voicechat.html", person_id=person_id, display_name=display_name)

@app.route('/voice_input', methods=['POST'])
def voice_input():
    try:
        text_input = request.form.get("text")
        person_id = request.form.get("person_id")

        if not text_input or not person_id:
            return jsonify({"error": "Missing text or person_id"}), 400

        print(f"[INFO] Received text from client: {text_input} for {person_id}")

        system_prompt = generate_system_prompt(person_id)
        response_text = query_llm(system_prompt, text_input)
        print(f"Response text: {response_text}")

        audio_response_path = synthesize_voice(response_text, person_id)
        print(f"Audio response path: {audio_response_path}")

        return jsonify({
            "response": response_text,
            "audio_url": f"/static/audio/{os.path.basename(audio_response_path)}"
        })

    except Exception as e:
        print("Error in /voice_input:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)