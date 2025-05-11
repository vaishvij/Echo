import subprocess
import os
import shutil

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

    # Optional cleanup
    os.remove(temp_wav)
