"""Video/Audio transcription processor using Whisper + FFmpeg."""

import os
import tempfile
import subprocess


def extract_audio_from_video(video_path: str) -> str:
    """Extract audio from video file using FFmpeg, returns path to temp wav file."""
    temp_audio = tempfile.mktemp(suffix=".wav")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        temp_audio, "-y",
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return temp_audio


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using OpenAI Whisper (local model)."""
    import whisper

    model = whisper.load_model("base")  # small model, runs on CPU
    result = model.transcribe(audio_path)
    return result["text"]


def extract_text_from_video(file_path: str) -> str:
    """Full pipeline: video → audio → text."""
    audio_path = extract_audio_from_video(file_path)
    try:
        text = transcribe_audio(audio_path)
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    return text


def extract_text_from_audio(file_path: str) -> str:
    """Direct audio transcription."""
    return transcribe_audio(file_path)
