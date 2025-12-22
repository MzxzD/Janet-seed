"""
Wake Word Detection for "Hey Janet"
"""
import threading
import time
from typing import Optional, Callable
from .stt import SpeechToText

# Import Red Thread event for constitutional integration (Axiom 8)
try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    # Fallback if core module not available
    RED_THREAD_EVENT = None


class WakeWordDetector:
    """Detects wake word "Hey Janet" to activate voice interaction."""
    
    def __init__(self, stt: Optional[SpeechToText] = None, callback: Optional[Callable] = None):
        """
        Initialize wake word detector.
        
        Args:
            stt: SpeechToText instance for continuous listening
            callback: Function to call when wake word is detected
        """
        self.stt = stt or SpeechToText(model_size="tiny")  # Use tiny model for speed
        self.callback = callback
        self._listening = False
        self._lock = threading.Lock()  # Thread-safe flag access
        self.thread: Optional[threading.Thread] = None
        self.wake_phrases = ["hey janet", "janet", "hey jan", "janet wake up"]
        self.response_phrases = ["hi there", "yes", "i'm here", "hello", "hi"]
    
    @property
    def listening(self) -> bool:
        """Thread-safe access to listening flag."""
        with self._lock:
            return self._listening
    
    @listening.setter
    def listening(self, value: bool):
        """Thread-safe setting of listening flag."""
        with self._lock:
            self._listening = value
    
    def is_available(self) -> bool:
        """Check if wake word detection is available."""
        return self.stt.is_available()
    
    def _check_wake_word(self, text: str) -> bool:
        """
        Check if text contains wake word.
        
        Args:
            text: Transcribed text
        
        Returns:
            True if wake word detected
        """
        if not text:
            return False
        
        text_lower = text.lower().strip()
        for phrase in self.wake_phrases:
            if phrase in text_lower:
                return True
        return False
    
    def start_listening(self, check_interval: float = 2.0, record_duration: float = 2.0):
        """
        Start continuous listening for wake word.
        
        Args:
            check_interval: Seconds between wake word checks
            record_duration: Duration of each audio recording
        """
        if not self.is_available():
            print("⚠️  Wake word detection not available (STT required)")
            return
        
        # Thread-safe check if already listening
        with self._lock:
            if self._listening:
                print("⚠️  Already listening for wake word")
                return
            self._listening = True
        
        self.thread = threading.Thread(
            target=self._listen_loop,
            args=(check_interval, record_duration),
            daemon=True
        )
        self.thread.start()
        print("👂 Listening for wake word 'Hey Janet'...")
    
    def stop_listening(self):
        """Stop listening for wake word."""
        # Thread-safe stop
        with self._lock:
            was_listening = self._listening
            self._listening = False
        
        if was_listening and self.thread:
            self.thread.join(timeout=2.0)  # Increased timeout for cleaner shutdown
            if self.thread.is_alive():
                print("⚠️  Wake word thread did not stop within timeout")
        print("🔇 Stopped listening for wake word")
    
    def _listen_loop(self, check_interval: float, record_duration: float):
        """Internal loop for continuous listening."""
        while self.listening:  # Uses property for thread-safe access
            # Axiom 8: Red Thread Protocol - Check for emergency stop
            if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
                print("🔴 Red Thread detected - stopping wake word detection")
                with self._lock:
                    self._listening = False
                break
            
            try:
                # Record and transcribe
                text = self.stt.listen_and_transcribe(duration=record_duration)
                
                # Check flag again after potentially long operation
                if not self.listening:
                    break
                
                # Axiom 8: Red Thread Protocol - Check again after transcription
                if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
                    print("🔴 Red Thread detected - stopping wake word detection")
                    with self._lock:
                        self._listening = False
                    break
                
                if text and self._check_wake_word(text):
                    print(f"🔔 Wake word detected: '{text}'")
                    
                    # Call callback if provided
                    if self.callback:
                        try:
                            self.callback()
                        except Exception as e:
                            print(f"⚠️  Wake word callback failed: {e}")
                    
                    # Pause briefly after wake word to avoid re-triggering
                    # Check flag periodically during sleep
                    sleep_time = 1.0
                    check_every = 0.1
                    while sleep_time > 0 and self.listening:
                        time.sleep(min(check_every, sleep_time))
                        sleep_time -= check_every
                else:
                    # Short pause between checks - check flag periodically
                    sleep_time = check_interval
                    check_every = 0.2
                    while sleep_time > 0 and self.listening:
                        time.sleep(min(check_every, sleep_time))
                        sleep_time -= check_every
                    
            except Exception as e:
                print(f"⚠️  Wake word detection error: {e}")
                # Check flag before continuing
                if not self.listening:
                    break
                time.sleep(min(check_interval, 1.0))
    
    def detect_once(self, record_duration: float = 3.0) -> bool:
        """
        Check once for wake word (non-continuous).
        
        Args:
            record_duration: Duration of audio recording
        
        Returns:
            True if wake word detected
        """
        if not self.is_available():
            return False
        
        text = self.stt.listen_and_transcribe(duration=record_duration)
        return self._check_wake_word(text) if text else False


def get_default_wake_detector(callback: Optional[Callable] = None) -> Optional[WakeWordDetector]:
    """Get default wake word detector."""
    try:
        stt = SpeechToText(model_size="tiny")
        if stt.is_available():
            return WakeWordDetector(stt=stt, callback=callback)
    except Exception:
        pass
    return None

