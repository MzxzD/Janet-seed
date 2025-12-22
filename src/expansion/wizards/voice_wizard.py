"""
Voice I/O Wizard — Voice Input/Output Setup

Guides users through setting up voice I/O capabilities.
"""

import subprocess
import sys
from pathlib import Path
from typing import Tuple, List
from .wizard_base import ExpansionWizard


class VoiceWizard(ExpansionWizard):
    """Wizard for setting up voice I/O."""
    
    def run(self) -> bool:
        """Run the voice I/O setup wizard."""
        print(f"\n{'='*60}")
        print("🎤 Voice I/O Setup Wizard")
        print(f"{'='*60}\n")
        
        # Validate requirements
        valid, missing = self.validate_requirements()
        if not valid:
            print("❌ Requirements not met:")
            for req in missing:
                print(f"  • {req}")
            return False
        
        # Check dependencies
        print("Checking dependencies...")
        deps_ok = self._check_dependencies()
        if not deps_ok:
            print("\n⚠️  Some dependencies are missing.")
            print("You'll need to install:")
            print("  • openai-whisper (for speech-to-text)")
            print("  • sounddevice (for audio recording)")
            print("  • pyttsx3 (for text-to-speech)")
            print("\nInstall with: pip install openai-whisper sounddevice pyttsx3")
            return False
        
        # Test microphone
        print("\nTesting microphone...")
        mic_ok = self._test_microphone()
        if not mic_ok:
            print("⚠️  Microphone test failed. Please check your microphone setup.")
            return False
        
        # Configure voice settings
        print("\nConfiguring voice settings...")
        self.config = self._configure_voice_settings()
        
        # Verify setup
        if self.verify():
            print("\n✅ Voice I/O setup complete!")
            return True
        else:
            print("\n❌ Verification failed.")
            return False
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """Validate voice I/O requirements."""
        missing = []
        
        # Check for microphone (basic check)
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            has_mic = any(dev['max_input_channels'] > 0 for dev in devices)
            if not has_mic:
                missing.append("Microphone not detected")
        except ImportError:
            missing.append("sounddevice not installed")
        except Exception:
            missing.append("Could not detect audio devices")
        
        return len(missing) == 0, missing
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        try:
            import whisper
            import sounddevice
            import pyttsx3
            return True
        except ImportError:
            return False
    
    def _test_microphone(self) -> bool:
        """Test microphone availability."""
        try:
            import sounddevice as sd
            # Try to query default input device
            default_device = sd.query_devices(kind='input')
            return True
        except Exception:
            return False
    
    def _configure_voice_settings(self) -> dict:
        """Configure voice settings."""
        config = {
            "voice_style": "clear, warm, slightly synthetic",
            "wake_word": "Hey Janet",
            "stt_model": "base",
        }
        
        print("\nVoice configuration:")
        print(f"  Wake word: {config['wake_word']}")
        print(f"  Voice style: {config['voice_style']}")
        print(f"  STT model: {config['stt_model']}")
        
        return config
    
    def setup(self) -> bool:
        """Setup is handled in run()."""
        return self.run()
    
    def verify(self) -> bool:
        """Verify voice I/O setup."""
        try:
            # Try to import voice modules
            from voice import SpeechToText, TextToSpeech
            stt = SpeechToText(model_size="base")
            tts = TextToSpeech()
            
            # Check if they're available
            if stt.is_available() and tts.is_available():
                return True
        except Exception:
            pass
        
        return False
    
    def cleanup_on_failure(self):
        """Cleanup on failure."""
        pass

