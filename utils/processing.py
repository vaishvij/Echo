import subprocess
import os
import shutil

from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np

import torchaudio
torchaudio.set_audio_backend("soundfile")

def process_audio(input_path, output_path):
    temp_wav = input_path.replace(".wav", "_converted.wav")

    # Step 1: Convert to 16kHz mono WAV using ffmpeg
    cmd_ffmpeg = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1", temp_wav
    ]
    subprocess.run(cmd_ffmpeg, check=True)

    # Step 2: Run Demucs on converted WAV
    try:
        subprocess.run(["demucs", temp_wav], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Demucs failed: {e}")

    # Step 3: Move vocals.wav to final output path
    basename = os.path.basename(temp_wav).replace(".wav", "")
    vocals_path = os.path.join("separated", "htdemucs", basename, "vocals.wav")

    if not os.path.exists(vocals_path):
        raise FileNotFoundError(f"Expected vocals.wav not found at: {vocals_path}")

    shutil.move(vocals_path, output_path)

     # Step 4: Extract speaker embedding
    embedding_filename = os.path.basename(output_path).replace(".wav", ".npy")
    embedding_path = os.path.join("processed", embedding_filename)
    extract_speaker_embedding(output_path, embedding_path)

    # Optional cleanup
    os.remove(temp_wav)


def extract_speaker_embedding(enhanced_audio_path, save_embedding_path):
    # Load and preprocess the enhanced audio
    wav = preprocess_wav(enhanced_audio_path)

    # Load speaker encoder
    encoder = VoiceEncoder()

    # Get the 128-D embedding
    embedding = encoder.embed_utterance(wav)

    # Save the embedding to disk
    np.save(save_embedding_path, embedding)