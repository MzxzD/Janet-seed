"""
Speech-to-Text using Whisper
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable
import json

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False


class SpeechToText:
    """Speech-to-text using Whisper model."""
    
    def __init__(self, model_size: str = "base", language: Optional[str] = None):
        """
        Initialize Whisper STT.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code (None for auto-detection)
        """
        self.model_size = model_size
        self.language = language
        self.model = None
        self.initialized = False
        
        if not HAS_SOUNDDEVICE:
            print("⚠️  sounddevice not available. Voice input will be disabled.")
        if not HAS_WHISPER:
            print("⚠️  openai-whisper not available. Install with: pip install openai-whisper")
        else:
            self._initialize_model()
    
    def _initialize_model(self):
        """Load Whisper model."""
        if not HAS_WHISPER:
            return
        
        try:
            print(f"Loading Whisper model ({self.model_size})...")
            print("   (First run may download model, this may take a minute)")
            self.model = whisper.load_model(self.model_size)
            self.initialized = True
            print("✅ Whisper model loaded")
        except Exception as e:
            print(f"⚠️  Failed to load Whisper model: {e}")
            print("   If download failed, check internet connection or disk space")
            self.initialized = False
    
    def is_available(self) -> bool:
        """Check if STT is available."""
        return HAS_SOUNDDEVICE and HAS_NUMPY and HAS_WHISPER and self.initialized
    
    def record_audio(self, duration: float = 5.0, sample_rate: int = 16000):
        """
        Record audio from microphone.
        
        Args:
            duration: Recording duration in seconds
            sample_rate: Sample rate in Hz (16000 for Whisper)
        
        Returns:
            Audio data as numpy array, or None if unavailable
        """
        if not HAS_SOUNDDEVICE or not HAS_NUMPY or np is None:
            return None
        
        try:
            print(f"🎤 Recording for {duration} seconds... (speak now)")
            audio = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()  # Wait until recording is finished
            return audio.flatten()
        except PermissionError as e:
            print(f"⚠️  Microphone permission denied. Please grant microphone access in System Settings.")
            print(f"   Error details: {e}")
            return None
        except OSError as e:
            if "No audio device" in str(e) or "PortAudio" in str(e):
                print(f"⚠️  Audio device unavailable. Ensure PortAudio is installed:")
                print(f"   macOS: brew install portaudio")
                print(f"   Linux: sudo apt-get install portaudio19-dev")
            else:
                print(f"⚠️  Audio recording failed: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Audio recording failed: {e}")
            return None
    
    def transcribe(self, audio, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate in Hz
        
        Returns:
            Transcribed text, or None if unavailable
        """
        if not self.is_available() or audio is None or not HAS_NUMPY or np is None:
            return None
        
        try:
            # Whisper expects float32 audio normalized to [-1, 1]
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Transcribe
            result = self.model.transcribe(
                audio,
                language=self.language,
                task="transcribe"
            )
            
            text = result["text"].strip()
            return text if text else None
        except Exception as e:
            print(f"⚠️  Transcription failed: {e}")
            return None
    
    def listen_and_transcribe(self, duration: float = 5.0, sample_rate: int = 16000):
        """
        Record audio and transcribe in one step.
        
        Args:
            duration: Recording duration in seconds
            sample_rate: Sample rate in Hz
        
        Returns:
            Transcribed text, or None if unavailable
        """
        audio = self.record_audio(duration, sample_rate)
        if audio is None:
            return None
        return self.transcribe(audio, sample_rate)


def get_default_stt() -> Optional[SpeechToText]:
    """Get default STT instance."""
    try:
        return SpeechToText(model_size="base")
    except Exception:
        return None

