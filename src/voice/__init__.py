"""
Voice I/O Module for Janet
Provides speech-to-text, text-to-speech, wake word detection, and tone awareness.
"""

from .stt import SpeechToText
from .tts import TextToSpeech
from .wake_word import WakeWordDetector
from .tone_awareness import ToneAwareness

__all__ = ['SpeechToText', 'TextToSpeech', 'WakeWordDetector', 'ToneAwareness']

