"""
Text-to-Speech using Piper TTS
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import tempfile

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    import piper
    HAS_PIPER = True
except ImportError:
    HAS_PIPER = False


class TextToSpeech:
    """Text-to-speech using Piper or pyttsx3 fallback."""
    
    def __init__(self, voice_style: str = "clear, warm, slightly synthetic"):
        """
        Initialize TTS engine.
        
        Args:
            voice_style: Voice style description (for future Piper voice profile)
        """
        self.voice_style = voice_style
        self.engine = None
        self.initialized = False
        self.use_piper = False
        
        # Try Piper first, fallback to pyttsx3
        if HAS_PIPER:
            self._initialize_piper()
        elif HAS_PYTTSX3:
            self._initialize_pyttsx3()
        else:
            print("⚠️  No TTS engine available. Install with: pip install piper-tts or pip install pyttsx3")
    
    def _initialize_piper(self):
        """Initialize Piper TTS (preferred)."""
        # Piper integration would go here
        # For now, fallback to pyttsx3
        if HAS_PYTTSX3:
            self._initialize_pyttsx3()
        else:
            print("⚠️  Piper TTS not yet fully implemented, falling back to system TTS")
    
    def _initialize_pyttsx3(self):
        """Initialize pyttsx3 TTS (fallback)."""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice settings for Janet's style
            # Set rate (words per minute) - slightly slower for clarity
            rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', rate - 20)  # Slightly slower
            
            # Set volume
            self.engine.setProperty('volume', 0.9)
            
            # Try to find a clear, warm voice
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voices (often clearer/smoother)
                for voice in voices:
                    if 'female' in voice.name.lower() or 'karen' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            self.initialized = True
            print("✅ TTS initialized (pyttsx3)")
        except Exception as e:
            print(f"⚠️  TTS initialization failed: {e}")
            self.initialized = False
    
    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self.initialized and self.engine is not None
    
    def speak(self, text: str, remove_emojis: bool = True) -> bool:
        """
        Speak text aloud.
        
        Args:
            text: Text to speak
            remove_emojis: Remove emojis from text before speaking (Janet preference)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        # Remove emojis if requested (Janet's preference for voice mode)
        if remove_emojis:
            import re
            # Remove emoji and other symbols that don't sound good in TTS
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )
            text = emoji_pattern.sub('', text)
            # Replace common emoji-like patterns
            text = text.replace(':)', '')
            text = text.replace(':(', '')
            text = text.replace(':D', '')
        
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            print(f"⚠️  TTS failed: {e}")
            return False
    
    def speak_async(self, text: str, remove_emojis: bool = True):
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: Text to speak
            remove_emojis: Remove emojis from text before speaking
        """
        if not self.is_available():
            return
        
        # Remove emojis if requested
        if remove_emojis:
            import re
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"
                "\U0001F300-\U0001F5FF"
                "\U0001F680-\U0001F6FF"
                "\U0001F1E0-\U0001F1FF"
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )
            text = emoji_pattern.sub('', text)
            text = text.replace(':)', '').replace(':(', '').replace(':D', '')
        
        try:
            self.engine.say(text)
            self.engine.startLoop(False)
        except Exception as e:
            print(f"⚠️  TTS async failed: {e}")


def get_default_tts() -> Optional[TextToSpeech]:
    """Get default TTS instance."""
    try:
        return TextToSpeech()
    except Exception:
        return None

