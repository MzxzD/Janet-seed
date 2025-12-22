"""
Conversation Classification
Rule-based classification of conversations into discard/normal/sensitive/secret categories.

This module classifies user input to determine which vault (if any) should store the information.
"""

import re
from typing import Dict, Optional


class ConversationClassifier:
    """
    Rule-based conversation classifier.
    
    Classifies conversations into:
    - discard: Ephemeral, no storage needed
    - normal: Safe for Green Vault
    - sensitive: Requires Blue Vault (unlocked)
    - secret: Requires explicit declaration before Red Vault
    """
    
    def __init__(self):
        """Initialize the conversation classifier."""
        # Discard patterns - ephemeral conversations
        self.discard_patterns = [
            r'^(hi|hello|hey|good morning|good afternoon|good evening|goodbye|bye|thanks|thank you)$',
            r'^(ok|okay|sure|yes|no|yep|nope)$',
            r'^(what|who|when|where|why|how)\s+\?*$',
        ]
        
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
            "pin", "personal identification",
            "private key", "private_key",
            "encryption key", "encryption_key"
        ]
        
        # Secret patterns
        self.secret_patterns = [
            r'\b[A-Z0-9]{20,}\b',  # Long alphanumeric strings (API keys)
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card patterns
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
        ]
        
        # Secret contexts
        self.secret_contexts = [
            "don't tell anyone",
            "keep this between us",
            "this is just for you",
            "don't log this",
            "forget this",
            "don't remember",
            "this is a secret",
            "keep this secret"
        ]
        
        # Sensitive indicators (less severe than secrets)
        self.sensitive_keywords = [
            "personal", "private information",
            "emotional", "feeling", "feelings",
            "health", "medical",
            "family", "relationship",
            "financial", "money",
            "work", "job", "employer"
        ]
        
        # Explicit secret declaration patterns
        self.explicit_secret_patterns = [
            r"store.*secret",
            r"save.*secret",
            r"remember.*secret",
            r"this is a secret",
            r"secret:",
            r"secret="
        ]
    
    def classify(self, text: str, context: Optional[Dict] = None) -> str:
        """
        Classify conversation into discard/normal/sensitive/secret.
        
        Args:
            text: User input text
            context: Additional context (tone, emotional state, etc.)
        
        Returns:
            Classification: "discard", "normal", "sensitive", or "secret"
        """
        if not text or not text.strip():
            return "discard"
        
        text_lower = text.lower().strip()
        
        # Check for explicit "don't remember" requests
        if any(phrase in text_lower for phrase in ["don't remember", "forget this", "don't save", "don't store"]):
            return "discard"
        
        # Check for discard patterns (ephemeral conversations)
        for pattern in self.discard_patterns:
            if re.match(pattern, text_lower, re.IGNORECASE):
                return "discard"
        
        # Check for secret indicators
        if self._is_secret(text, context):
            return "secret"
        
        # Check for sensitive indicators
        if self._is_sensitive(text, context):
            return "sensitive"
        
        # Default to normal (safe for Green Vault)
        return "normal"
    
    def _is_secret(self, text: str, context: Optional[Dict] = None) -> bool:
        """
        Check if text contains secret indicators.
        
        Args:
            text: Text to check
            context: Additional context
        
        Returns:
            True if secret indicators found, False otherwise
        """
        text_lower = text.lower()
        
        # Check for secret keywords
        for keyword in self.secret_keywords:
            if keyword in text_lower:
                return True
        
        # Check for secret patterns
        for pattern in self.secret_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check for secret contexts
        for context_phrase in self.secret_contexts:
            if context_phrase in text_lower:
                return True
        
        return False
    
    def _is_sensitive(self, text: str, context: Optional[Dict] = None) -> bool:
        """
        Check if text contains sensitive indicators.
        
        Args:
            text: Text to check
            context: Additional context
        
        Returns:
            True if sensitive indicators found, False otherwise
        """
        text_lower = text.lower()
        
        # Check for sensitive keywords
        for keyword in self.sensitive_keywords:
            if keyword in text_lower:
                return True
        
        # Check context for emotional distress
        if context:
            emotional_state = context.get("tone", {}).get("emotional_state", "")
            if emotional_state in ["distressed", "coerced", "under_duress", "emotional"]:
                return True
        
        return False
    
    def requires_explicit_declaration(self, text: str) -> bool:
        """
        Check if secret requires explicit user declaration.
        
        Args:
            text: Text to check
        
        Returns:
            True if explicit declaration is required, False otherwise
        """
        text_lower = text.lower()
        
        # Check for explicit secret declaration patterns
        for pattern in self.explicit_secret_patterns:
            if re.search(pattern, text_lower):
                return False  # Already explicitly declared
        
        # If secret indicators found but not explicitly declared, require declaration
        if self._is_secret(text):
            return True
        
        return False
    
    def get_classification_reason(self, text: str, context: Optional[Dict] = None) -> str:
        """
        Get reason for classification (for debugging/logging).
        
        Args:
            text: Text that was classified
            context: Additional context
        
        Returns:
            Human-readable reason for classification
        """
        classification = self.classify(text, context)
        
        if classification == "discard":
            return "Ephemeral conversation, no storage needed"
        elif classification == "normal":
            return "Safe for Green Vault storage"
        elif classification == "sensitive":
            return "Sensitive information, requires Blue Vault (unlocked)"
        elif classification == "secret":
            if self.requires_explicit_declaration(text):
                return "Secret detected, requires explicit declaration"
            else:
                return "Secret explicitly declared"
        else:
            return "Unknown classification"

