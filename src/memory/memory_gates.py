"""
Memory Write Gates - Axiom 9 Enforcement
Secrets shared between us are sacred. They stay between us — never logged, never exposed.
"""
import re
from typing import Dict, Optional, List
from datetime import datetime


class MemoryGates:
    """Enforces Axiom 9: Secrets sacred - memory write gates."""
    
    def __init__(self):
        """Initialize memory gates with secret detection patterns."""
        # Secret indicators (case-insensitive)
        self.secret_keywords = [
            "password", "passwd", "pwd",
            "secret", "secrets",
            "private", "privately",
            "confidential", "classified",
            "api key", "apikey", "api_key",
            "token", "access token",
            "credential", "credentials",
            "ssn", "social security",
            "credit card", "card number",
            "pin", "personal identification"
        ]
        
        # Patterns that suggest secrets
        self.secret_patterns = [
            r'\b[A-Z0-9]{20,}\b',  # Long alphanumeric strings (API keys)
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card patterns
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
        ]
        
        # Context that suggests secrets even without keywords
        self.secret_contexts = [
            "don't tell anyone",
            "keep this between us",
            "this is just for you",
            "don't log this",
            "forget this",
            "don't remember"
        ]
    
    def check_write_allowed(self, text: str, context: Optional[Dict] = None) -> Dict:
        """
        Check if memory write is allowed (Axiom 9).
        
        Args:
            text: Text to check
            context: Additional context (tone, emotional state, etc.)
        
        Returns:
            Dictionary with:
                - allowed: bool
                - reason: str (if not allowed)
                - confidence: float (0.0-1.0)
        """
        text_lower = text.lower()
        
        # Check for explicit "don't remember" requests
        if any(phrase in text_lower for phrase in ["don't remember", "forget this", "don't save"]):
            return {
                "allowed": False,
                "reason": "Explicit request to not remember",
                "confidence": 1.0
            }
        
        # Check for secret keywords
        for keyword in self.secret_keywords:
            if keyword in text_lower:
                return {
                    "allowed": False,
                    "reason": f"Secret keyword detected: '{keyword}'",
                    "confidence": 0.9
                }
        
        # Check for secret patterns
        for pattern in self.secret_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "allowed": False,
                    "reason": "Secret pattern detected (possible API key, card number, etc.)",
                    "confidence": 0.7
                }
        
        # Check for secret contexts
        for context_phrase in self.secret_contexts:
            if context_phrase in text_lower:
                return {
                    "allowed": False,
                    "reason": "Secret context detected",
                    "confidence": 0.8
                }
        
        # Check context for emotional distress (might indicate coercion)
        if context:
            emotional_state = context.get("tone", {}).get("emotional_state", "")
            if emotional_state in ["distressed", "coerced", "under_duress"]:
                return {
                    "allowed": False,
                    "reason": "Emotional state suggests potential coercion",
                    "confidence": 0.6
                }
        
        # All checks passed
        return {
            "allowed": True,
            "reason": "No secrets detected",
            "confidence": 1.0
        }
    
    def sanitize_for_memory(self, text: str) -> str:
        """
        Sanitize text before storing (remove obvious secrets even if not caught).
        
        Args:
            text: Text to sanitize
        
        Returns:
            Sanitized text
        """
        sanitized = text
        
        # Replace potential API keys with placeholder
        sanitized = re.sub(r'\b[A-Z0-9]{20,}\b', '[REDACTED_KEY]', sanitized)
        
        # Replace credit card patterns
        sanitized = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[REDACTED_CARD]', sanitized)
        
        # Replace SSN patterns
        sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', sanitized)
        
        return sanitized

