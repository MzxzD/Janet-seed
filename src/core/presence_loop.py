"""
Presence Loop for J.A.N.E.T. Seed
Handles wake word detection, acknowledgment, greeting, and device selection.
"""

import random
import sys
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .janet_core import JanetCore


def play_ack_sound():
    """Play acknowledgment sound when wake word is detected."""
    # Simple beep sound (can be enhanced with audio file)
    print("🔔")  # Visual indicator for now
    # In full implementation: play audio file or system beep
    if sys.platform == "darwin":  # macOS
        try:
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], 
                         capture_output=True, timeout=0.5)
        except:
            pass


def speak_greeting(janet: 'JanetCore'):
    """Speak greeting when activated."""
    greeting_phrases = janet.constitution.raw_data.get("wake_word", {}).get("response", 
                                                                           ["Hi there!", "Yes?", "I'm here."])
    greeting = random.choice(greeting_phrases)
    
    if janet.tts and janet.tts.is_available():
        janet.tts.speak(greeting)
    else:
        print(f"\nJanet: {greeting}")


def wait_for_wake_word(janet: 'JanetCore') -> bool:
    """Wait for wake word detection (Presence Loop)."""
    if not janet.voice_mode or not janet.wake_detector:
        return True  # In text mode, always ready
    
    if not janet.wake_detector.is_available():
        return True  # Wake word not available, proceed directly
    
    # Reset flag and start listening
    # Flag will be set by callback when wake word is detected
    if not janet.wake_detector.listening:
        janet.wake_detector.start_listening()
    
    # Wait for wake word (non-blocking check)
    # In a real implementation, this would use a threading.Event or callback
    # For now, return True and let the main loop handle wake word detection
    return True


def select_input_device(janet: 'JanetCore') -> str:
    """Select appropriate input device (voice or text)."""
    if janet.voice_mode and janet.stt and janet.stt.is_available():
        return "voice"
    return "text"


def run_presence_loop(janet: 'JanetCore', voice_mode: bool) -> str:
    """
    Run presence loop: wait for wake word, acknowledge, greet, select input device.
    
    Returns:
        str: Input device ("voice" or "text")
    """
    # Wait for wake word (or proceed directly in text mode)
    if not wait_for_wake_word(janet):
        # Not ready yet, should return to wait again
        return select_input_device(janet)
    
    # Handle wake word detection (voice mode) - thread-safe check and reset
    if voice_mode and janet._check_and_reset_wake_flag():
        play_ack_sound()  # Play acknowledgment sound
        speak_greeting(janet)  # Speak greeting
        # Start new conversation session after greeting
        if janet.janet_brain:
            janet.janet_brain.start_conversation()
    
    # Select input device (voice or text)
    input_device = select_input_device(janet)
    
    return input_device

