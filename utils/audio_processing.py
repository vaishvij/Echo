import subprocess
import os
import re
import wave
import shutil

from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np

import torch
from torch.serialization import add_safe_globals

# All required classes for XTTS checkpoint loading
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig

# Allowlist all XTTS-related config classes
add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

from TTS.api import TTS

import torchaudio
torchaudio.set_audio_backend("soundfile")

tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)

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


def clone_voice_from_text(text_input, enhanced_audio_path, output_path, language="en"):
    """#Load the saved speaker embedding
    #speaker_embedding = np.load(embedding_path)"""

    #Generate cloned voice audio file
    tts_model.tts_to_file(
        text = text_input,
        speaker_wav = enhanced_audio_path,
        file_path = output_path,
        language=language
    )


def concatenate_wavs(input_paths, output_path):
    data = []
    params = None
    for path in input_paths:
        with wave.open(path, 'rb') as f:
            if params is None:
                params = f.getparams()
            data.append(f.readframes(f.getnframes()))
    with wave.open(output_path, 'wb') as f:
        f.setparams(params)
        for d in data:
            f.writeframes(d)


def synthesize_voice(text_input, person_id, language="en"):
    enhanced_audio_path = os.path.join("processed", f"{person_id}.wav")
 
    if not os.path.exists(enhanced_audio_path):
        raise FileNotFoundError(f"Enhanced audio not found for person_id: {person_id}")
 
    # Split response into sentences for faster first-audio delivery
    sentences = [s.strip() for s in re.split(r'(?<=[.!?।])\s+', text_input) if s.strip()]
 
    output_dir = os.path.join("static", "audio")
    os.makedirs(output_dir, exist_ok=True)
 
    audio_paths = []
    for i, sentence in enumerate(sentences):
        out_path = os.path.join(output_dir, f"{person_id}_response_{i}.wav")
        clone_voice_from_text(sentence, enhanced_audio_path, out_path, language=language)
        audio_paths.append(out_path)
 
    # Merge all sentence WAVs into one final file
    final_output = os.path.join(output_dir, f"{person_id}_response.wav")
    concatenate_wavs(audio_paths, final_output)
 
    # Cleanup individual sentence files
    for p in audio_paths:
        os.remove(p)

    return final_output
