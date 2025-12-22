"""
Tone Awareness - Detects emotional tone, sarcasm, stress in speech
"""
from typing import Dict, Optional, List
import json
from pathlib import Path


class ToneAwareness:
    """Analyzes tone and emotional state from text and voice patterns."""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize tone awareness with schema.
        
        Args:
            schema_path: Path to tone awareness schema JSON file
        """
        self.schema = self._load_schema(schema_path)
        self.tone_patterns = self.schema.get("patterns", {})
        self.emotional_indicators = self.schema.get("emotional_indicators", {})
    
    def _load_schema(self, schema_path: Optional[Path]) -> Dict:
        """Load tone awareness schema."""
        default_schema = {
            "patterns": {
                "sarcasm": {
                    "text_indicators": ["sure", "right", "totally", "obviously", "of course"],
                    "prosodic_mismatch": True,
                    "context_clues": ["contradiction", "irony"]
                },
                "stress": {
                    "text_indicators": ["urgent", "hurry", "need", "must", "can't"],
                    "prosodic_indicators": ["high_pitch", "fast_speech", "repetition"]
                },
                "excitement": {
                    "text_indicators": ["!", "wow", "amazing", "incredible"],
                    "prosodic_indicators": ["high_pitch", "fast_speech"]
                },
                "frustration": {
                    "text_indicators": ["ugh", "seriously", "again", "why"],
                    "prosodic_indicators": ["sigh", "pause", "loud"]
                }
            },
            "emotional_indicators": {
                "positive": ["happy", "excited", "grateful", "content"],
                "negative": ["sad", "angry", "frustrated", "anxious"],
                "neutral": ["calm", "curious", "thoughtful"]
            },
            "prosodic_features": {
                "pitch": "detect_high_low",
                "speed": "detect_fast_slow",
                "volume": "detect_loud_quiet",
                "pause_patterns": "detect_hesitation"
            }
        }
        
        if schema_path and schema_path.exists():
            try:
                with open(schema_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    default_schema.update(loaded)
            except Exception as e:
                print(f"⚠️  Failed to load tone schema: {e}, using defaults")
        
        return default_schema
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze text for tone indicators.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Dictionary with tone analysis results
        """
        text_lower = text.lower()
        analysis = {
            "detected_tones": [],
            "emotional_state": "neutral",
            "confidence": 0.0,
            "suggested_response_style": "neutral"
        }
        
        # Check for sarcasm
        sarcasm_indicators = self.tone_patterns.get("sarcasm", {}).get("text_indicators", [])
        sarcasm_count = sum(1 for indicator in sarcasm_indicators if indicator in text_lower)
        if sarcasm_count >= 2:
            analysis["detected_tones"].append("sarcasm")
            analysis["suggested_response_style"] = "tentative_clarification"
        
        # Check for stress
        stress_indicators = self.tone_patterns.get("stress", {}).get("text_indicators", [])
        if any(indicator in text_lower for indicator in stress_indicators):
            analysis["detected_tones"].append("stress")
            analysis["emotional_state"] = "stressed"
            analysis["suggested_response_style"] = "calm_reassuring"
        
        # Check for excitement
        excitement_indicators = self.tone_patterns.get("excitement", {}).get("text_indicators", [])
        if any(indicator in text_lower for indicator in excitement_indicators) or "!" in text:
            analysis["detected_tones"].append("excitement")
            analysis["emotional_state"] = "positive"
            analysis["suggested_response_style"] = "enthusiastic"
        
        # Check for frustration
        frustration_indicators = self.tone_patterns.get("frustration", {}).get("text_indicators", [])
        if any(indicator in text_lower for indicator in frustration_indicators):
            analysis["detected_tones"].append("frustration")
            analysis["emotional_state"] = "negative"
            analysis["suggested_response_style"] = "empathetic_patient"
        
        # Calculate confidence based on indicator matches
        total_matches = sum(len(analysis["detected_tones"]), sarcasm_count)
        analysis["confidence"] = min(0.9, total_matches * 0.3)
        
        return analysis
    
    def analyze_prosodic(self, audio_features: Dict) -> Dict:
        """
        Analyze prosodic features (pitch, speed, volume).
        
        Args:
            audio_features: Dictionary with pitch, speed, volume data
        
        Returns:
            Prosodic analysis results
        """
        analysis = {
            "pitch_level": "normal",
            "speed_level": "normal",
            "volume_level": "normal",
            "detected_patterns": []
        }
        
        # Analyze pitch
        pitch = audio_features.get("pitch", 0)
        if pitch > 200:  # High pitch threshold
            analysis["pitch_level"] = "high"
            analysis["detected_patterns"].append("high_pitch")
        elif pitch < 100:  # Low pitch threshold
            analysis["pitch_level"] = "low"
            analysis["detected_patterns"].append("low_pitch")
        
        # Analyze speed
        speed = audio_features.get("speed", 0)  # words per minute
        if speed > 180:
            analysis["speed_level"] = "fast"
            analysis["detected_patterns"].append("fast_speech")
        elif speed < 100:
            analysis["speed_level"] = "slow"
            analysis["detected_patterns"].append("slow_speech")
        
        # Analyze volume
        volume = audio_features.get("volume", 0)  # dB
        if volume > -10:
            analysis["volume_level"] = "loud"
            analysis["detected_patterns"].append("loud")
        elif volume < -30:
            analysis["volume_level"] = "quiet"
            analysis["detected_patterns"].append("quiet")
        
        return analysis
    
    def combine_analysis(self, text_analysis: Dict, prosodic_analysis: Dict) -> Dict:
        """
        Combine text and prosodic analysis for comprehensive tone detection.
        
        Args:
            text_analysis: Results from analyze_text()
            prosodic_analysis: Results from analyze_prosodic()
        
        Returns:
            Combined analysis with tone-aware response suggestions
        """
        combined = {
            **text_analysis,
            "prosodic": prosodic_analysis,
            "final_tone": text_analysis.get("detected_tones", ["neutral"])[0] if text_analysis.get("detected_tones") else "neutral",
            "response_guidance": self._generate_response_guidance(text_analysis, prosodic_analysis)
        }
        
        # Detect prosodic-text mismatches (possible sarcasm)
        if prosodic_analysis.get("pitch_level") == "high" and "excitement" not in text_analysis.get("detected_tones", []):
            combined["detected_tones"].append("potential_mismatch")
            combined["response_guidance"]["clarify_tentatively"] = True
        
        return combined
    
    def _generate_response_guidance(self, text_analysis: Dict, prosodic_analysis: Dict) -> Dict:
        """Generate guidance for Janet's response based on tone analysis."""
        guidance = {
            "tone": "neutral",
            "pace": "normal",
            "clarify_tentatively": False,
            "show_empathy": False
        }
        
        detected_tones = text_analysis.get("detected_tones", [])
        
        if "stress" in detected_tones:
            guidance["tone"] = "calm"
            guidance["pace"] = "slower"
            guidance["show_empathy"] = True
        elif "frustration" in detected_tones:
            guidance["tone"] = "patient"
            guidance["show_empathy"] = True
        elif "sarcasm" in detected_tones or "potential_mismatch" in detected_tones:
            guidance["clarify_tentatively"] = True
            guidance["tone"] = "gentle"
        elif "excitement" in detected_tones:
            guidance["tone"] = "enthusiastic"
            guidance["pace"] = "slightly_faster"
        
        return guidance


def get_default_tone_awareness() -> ToneAwareness:
    """Get default tone awareness instance."""
    return ToneAwareness()

