"""
Voice I/O Module for Janet
Provides speech-to-text, text-to-speech, wake word detection, and tone awareness.
"""

from .stt import SpeechToText
from .tts import SpeakOutcome, TextToSpeech, resolve_speak_lang
from .wake_word import WakeWordDetector
from .tone_awareness import ToneAwareness

__all__ = [
    'SpeechToText',
    'TextToSpeech',
    'SpeakOutcome',
    'resolve_speak_lang',
    'WakeWordDetector',
    'ToneAwareness',
]

