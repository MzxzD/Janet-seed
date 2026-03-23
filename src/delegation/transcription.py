"""
Transcription delegation - "Hey Janet, transcribe this"
Audio → text. Uses Whisper (Ollama) or Apple Speech framework on iOS.
"""
from typing import Optional
from pathlib import Path


def transcribe_audio(
    audio_path: str,
    model: str = "whisper",
    llm_client=None,
) -> str:
    """
    Transcribe audio file to text.
    
    Args:
        audio_path: Path to audio file (wav, mp3, m4a)
        model: "whisper" for Ollama Whisper
        llm_client: Client for transcription (e.g. Ollama)
        
    Returns:
        Transcribed text
    """
    if not Path(audio_path).exists():
        return "[Audio file not found]"
    
    if llm_client and hasattr(llm_client, "transcribe"):
        try:
            return llm_client.transcribe(audio_path) or ""
        except Exception as e:
            return f"[Transcription error: {e}]"
    
    return "[Transcription not configured - add Whisper to Ollama]"
