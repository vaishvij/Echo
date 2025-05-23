from flask import Flask, request, render_template, send_file, send_from_directory, jsonify
import os
import uuid
from utils.audio_processing import process_audio
from utils.audio_processing import clone_voice_from_text
from utils.save_description import save_person_description
from utils.prompting import generate_system_prompt

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER,exist_ok=True)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_audio():
    audio = request.files['audio']
    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio.save(filepath)
    processed_filename = f"processed_{filename}"
    processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
    process_audio(filepath,processed_path)

    return f"""
        <h2>Here’s your audio:</h2>
        <audio controls autoplay>
            <source src="/uploads/{filename}" type="audio/wav">
        </audio>
        <br><br>
        <h2>Enhanced Audio:</h2>
        <audio controls autoplay>
            <source src="/processed/{processed_filename}" type="audio/wav">
        </audio>
        <br><br>
        <form action="/synthesize" method="post">
            <input type="hidden" name="processed_audio" value="{processed_filename}">
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
    processed_audio = request.form['processed_audio']

    processed_path = os.path.join(PROCESSED_FOLDER, processed_audio)
    embedding_path = processed_path.replace(".wav",".npy")

    output_filename = f"cloned_{uuid.uuid4()}.wav"
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

    return f"<h3>Profile Saved for {person_id}!</h3><a href='/description'>Create Another</a> | <a href='/'>Home</a>"


@app.route('/preview_prompt/<person_id>')
def preview_prompt(person_id):
    prompt = generate_system_prompt(person_id)
    return f"<pre>{prompt}</pre>"



if __name__ == '__main__':
    app.run(debug=True)