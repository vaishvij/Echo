from flask import Flask, request, render_template, send_file, send_from_directory
import os
import uuid
from utils.processing import process_audio

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
        <a href="/">Upload Another</a>
    """
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/processed/<filename>')
def get_processed_audio(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)