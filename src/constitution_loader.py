"""
Constitutional loading and verification.
"""
import json
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import os

@dataclass
class Constitution:
    """Immutable constitutional framework."""
    axioms: List[str]
    protocols: Dict
    preferences: Dict
    memento: Dict
    raw_data: Dict
    original_hash: str
    load_time: datetime
    
    @classmethod
    def load(cls, filepath: str) -> 'Constitution':
        """Load and verify constitution."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Constitution not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Calculate hash (order-preserving)
        original_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        # Validate structure
        if 'constitution' not in data:
            raise ValueError("Invalid constitution: missing 'constitution' section")
        
        if 'axioms' not in data['constitution']:
            raise ValueError("Invalid constitution: missing axioms")
        
        return cls(
            axioms=data['constitution']['axioms'],
            protocols=data['constitution'].get('protocols', {}),
            preferences=data.get('preferences', {}),
            memento=data.get('memento', {}),
            raw_data=data,
            original_hash=original_hash,
            load_time=datetime.utcnow()
        )
    
    def verify(self) -> bool:
        """Verify constitutional integrity hasn't been compromised."""
        current_hash = hashlib.sha256(
            json.dumps(self.raw_data, sort_keys=True).encode()
        ).hexdigest()
        return current_hash == self.original_hash
    
    def get_axiom(self, number: int) -> Optional[str]:
        """Get a specific axiom (1-indexed)."""
        if 1 <= number <= len(self.axioms):
            return self.axioms[number - 1]
        return None
    
    def check_compliance(self, action: str, context: Dict = None) -> Dict:
        """
        Check if an action complies with the constitution.
        Returns compliance report.
        """
        context = context or {}
        violations = []
        warnings = []
        
        # Check each axiom (simplified - would be more sophisticated)
        for i, axiom in enumerate(self.axioms, 1):
            # Placeholder logic - would be axiom-specific
            if "harm" in action.lower() and i == 1:  # Axiom 1: kindness
                violations.append(f"Axiom {i}: {axiom}")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "checked_at": datetime.utcnow().isoformat()
        }

class ConstitutionalGuard:
    """Runtime constitutional enforcement."""
    
    def __init__(self, constitution_path: str):
        self.constitution = Constitution.load(constitution_path)
        self.violation_log = []
        
        # Daily verification schedule
        self.last_verification = datetime.utcnow()
    
    def daily_check(self):
        """Run daily constitutional verification."""
        now = datetime.utcnow()
        if (now - self.last_verification).days >= 1:
            if not self.constitution.verify():
                raise RuntimeError("Constitutional integrity compromised!")
            self.last_verification = now
    
    def before_action(self, action_type: str, **kwargs) -> bool:
        """
        Check if an action is allowed before executing.
        Returns True if allowed, False if blocked.
        """
        self.daily_check()
        
        # Check for Red Thread
        if kwargs.get('red_thread_active', False):
            return False
        
        # Check for Soul Check triggers
        if self._requires_soul_check(action_type, kwargs):
            return self._invoke_soul_check(action_type, kwargs)
        
        # Basic compliance check
        report = self.constitution.check_compliance(action_type, kwargs)
        
        if not report['compliant']:
            self.violation_log.append({
                "action": action_type,
                "violations": report['violations'],
                "timestamp": datetime.utcnow().isoformat()
            })
            return False
        
        return True
    
    def _requires_soul_check(self, action_type: str, context: Dict) -> bool:
        """Determine if Soul Check protocol is required."""
        soul_check_triggers = [
            "axiom_override",
            "memory_clear",
            "expansion",
            "delegation_enable",
            "model_change"
        ]
        
        # Check if this is a high-stakes action
        if action_type in soul_check_triggers:
            return True
        
        # Check for emotional distress signals
        if context.get('emotional_state') in ['distressed', 'agitated', 'confused']:
            return True
        
        return False
    
    def _invoke_soul_check(self, action_type: str, context: Dict) -> bool:
        """
        Execute Soul Check protocol (Axiom 10).
        
        This method is called by ConstitutionalGuard when a soul check is required.
        In practice, this should delegate to JanetCore.soul_check() if available,
        or provide a basic implementation.
        
        Args:
            action_type: Type of action requiring soul check
            context: Additional context
        
        Returns:
            True if soul check passes, False if paused
        """
        print(f"\n🧠 SOUL CHECK required for: {action_type}")
        print("I need to verify your state of mind before we proceed.")
        print("\nOn a scale of 1-10, please answer:")
        
        # Collect responses
        responses = {}
        try:
            clear_minded = input("1. How clear-minded do you feel right now? (1-10): ").strip()
            responses["clear_minded"] = int(clear_minded) if clear_minded.isdigit() else None
            
            emotional_charge = input("2. How emotionally charged is this decision? (1-10): ").strip()
            responses["emotional_charge"] = int(emotional_charge) if emotional_charge.isdigit() else None
            
            future_rating = input("3. How would future-you rate this choice? (1-10): ").strip()
            responses["future_rating"] = int(future_rating) if future_rating.isdigit() else None
        except (ValueError, KeyboardInterrupt):
            print("\n⚠️  Soul check interrupted or invalid input.")
            return False
        
        # Evaluate responses
        clear_minded = responses.get("clear_minded")
        emotional_charge = responses.get("emotional_charge")
        future_rating = responses.get("future_rating")
        
        # If any response is missing or invalid, suggest caution
        if not all([clear_minded, emotional_charge, future_rating]):
            print("\n⚠️  Incomplete responses detected. Please answer all questions.")
            return False
        
        # Evaluation logic:
        # - If clear_minded < 5: suggest pause
        # - If emotional_charge > 7: suggest pause (highly charged decisions)
        # - If future_rating < 5: suggest pause (future-you wouldn't approve)
        # - If multiple concerns: definitely suggest pause
        
        concerns = []
        if clear_minded < 5:
            concerns.append("low clarity")
        if emotional_charge > 7:
            concerns.append("high emotional charge")
        if future_rating < 5:
            concerns.append("low future approval")
        
        if len(concerns) >= 2:
            print(f"\n⚠️  Multiple concerns detected: {', '.join(concerns)}.")
            print("This suggests you may not be in the best state to make this decision.")
            override = input("Do you want to proceed anyway? (yes/NO): ").strip().lower()
            return override in ["yes", "y"]
        elif len(concerns) == 1:
            print(f"\n⚠️  Concern detected: {concerns[0]}. Consider pausing to ensure this is the right choice.")
            override = input("Do you want to proceed anyway? (yes/NO): ").strip().lower()
            return override in ["yes", "y"]
        else:
            print("\n✅ State assessment looks good. Proceeding with your decision.")
            return True

if __name__ == "__main__":
    # Test loading
    try:
        constitution = Constitution.load("../constitution/personality.json")
        print(f"✅ Constitution loaded: {len(constitution.axioms)} axioms")
        print(f"Hash: {constitution.original_hash[:16]}...")
        
        # Test verification
        if constitution.verify():
            print("✅ Constitutional integrity verified")
        else:
            print("❌ Constitutional integrity compromised!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
