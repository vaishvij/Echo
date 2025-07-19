from faster_whisper import WhisperModel

# Load once globally for performance
model = WhisperModel("base", compute_type="int8")  # Or "small" if accuracy is a concern

def transcribe_audio(audio_path):
    try:
        segments, _ = model.transcribe(audio_path)
        transcription = ""
        for segment in segments:
            transcription += segment.text.strip() + " "
        return transcription.strip()
    except Exception as e:
        print(f"[ERROR] Transcription failed: {e}")
        return ""
