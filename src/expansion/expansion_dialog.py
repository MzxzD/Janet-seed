"""
Expansion Dialog — Proactive Suggestion System

Janet's "I could do more elsewhere" dialogue system.
Presents expansion opportunities respectfully and waits for user consent.
"""

from typing import Optional, List
from .expansion_types import ExpansionOpportunity

# Import Red Thread event for constitutional integration (Axiom 8)
try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    # Fallback if core module not available
    RED_THREAD_EVENT = None


class ExpansionDialog:
    """Handles proactive expansion suggestions and dialogues."""
    
    def __init__(self, janet_core=None):
        """
        Initialize expansion dialog.
        
        Args:
            janet_core: Optional JanetCore instance for context
        """
        self.janet_core = janet_core
        self.recently_declined = {}  # Track recently declined expansions
    
    def suggest_expansion(self, opportunity: ExpansionOpportunity) -> bool:
        """
        Suggest an expansion opportunity to the user.
        
        Args:
            opportunity: Expansion opportunity to suggest
        
        Returns:
            True if user accepts, False if declined
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - expansion suggestion blocked")
            return False
        
        # Check if recently declined (don't ask again too soon)
        if self._was_recently_declined(opportunity.expansion_type):
            return False
        
        # Present the opportunity
        return self.present_expansion_opportunity(opportunity)
    
    def present_expansion_opportunity(self, opportunity: ExpansionOpportunity) -> bool:
        """
        Present an expansion opportunity to the user.
        
        Args:
            opportunity: Expansion opportunity
        
        Returns:
            True if user accepts, False if declined
        """
        print(f"\n{'='*60}")
        print(f"🌱 Expansion Opportunity: {opportunity.name}")
        print(f"{'='*60}")
        print(f"\n{opportunity.description}\n")
        
        # Show benefits
        if opportunity.benefits:
            print("✨ Benefits:")
            for benefit in opportunity.benefits:
                print(f"  • {benefit}")
            print()
        
        # Show risks
        if opportunity.risks:
            print("⚠️  Considerations:")
            for risk in opportunity.risks:
                print(f"  • {risk}")
            print()
        
        # Show requirements
        if opportunity.requirements:
            print("📋 Requirements:")
            for key, value in opportunity.requirements.items():
                if isinstance(value, bool):
                    if value:
                        print(f"  • {key.replace('_', ' ').title()}")
                elif isinstance(value, (int, float)):
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
                else:
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
            print()
        
        print(f"⏱️  Estimated setup time: {opportunity.estimated_setup_time}")
        print(f"{'='*60}\n")
        
        # Get user response
        while True:
            response = input("Would you like to explore this? (yes/no/tell me more/not now): ").strip().lower()
            
            if response in ["yes", "y"]:
                return True
            elif response in ["no", "n"]:
                self._record_decline(opportunity.expansion_type)
                return False
            elif response in ["tell me more", "more", "info"]:
                self.explain_benefits_and_risks(opportunity)
                # Ask again after explanation
                continue
            elif response in ["not now", "later"]:
                self._record_decline(opportunity.expansion_type, temporary=True)
                return False
            else:
                print("Please respond with: yes, no, tell me more, or not now")
    
    def explain_benefits_and_risks(self, opportunity: ExpansionOpportunity):
        """
        Provide detailed explanation of benefits and risks.
        
        Args:
            opportunity: Expansion opportunity to explain
        """
        print(f"\n{'='*60}")
        print(f"📖 Detailed Information: {opportunity.name}")
        print(f"{'='*60}\n")
        
        if opportunity.benefits:
            print("✨ Benefits in Detail:")
            for i, benefit in enumerate(opportunity.benefits, 1):
                print(f"  {i}. {benefit}")
            print()
        
        if opportunity.risks:
            print("⚠️  Considerations in Detail:")
            for i, risk in enumerate(opportunity.risks, 1):
                print(f"  {i}. {risk}")
            print()
        
        if opportunity.requirements:
            print("📋 Technical Requirements:")
            for key, value in opportunity.requirements.items():
                if isinstance(value, bool):
                    if value:
                        print(f"  • {key.replace('_', ' ').title()}: Required")
                elif isinstance(value, (int, float)):
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
                elif isinstance(value, list):
                    print(f"  • {key.replace('_', ' ').title()}: {', '.join(value)}")
                else:
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
            print()
        
        print(f"🔄 Reversible: {'Yes' if opportunity.reversible else 'No'}")
        print(f"🌐 Requires Network: {'Yes' if opportunity.requires_network else 'No'}")
        print(f"💻 Hardware Sufficient: {'Yes' if opportunity.hardware_sufficient else 'No'}")
        print(f"{'='*60}\n")
    
    def _was_recently_declined(self, expansion_type: str) -> bool:
        """Check if expansion was recently declined."""
        if expansion_type not in self.recently_declined:
            return False
        
        from datetime import datetime, timedelta
        decline_time = self.recently_declined[expansion_type]
        # Don't ask again for 24 hours if permanently declined, 1 hour if temporary
        if decline_time.get("permanent", False):
            return (datetime.now() - decline_time["timestamp"]).total_seconds() < 86400
        else:
            return (datetime.now() - decline_time["timestamp"]).total_seconds() < 3600
    
    def _record_decline(self, expansion_type: str, temporary: bool = False):
        """Record that user declined an expansion."""
        from datetime import datetime
        self.recently_declined[expansion_type] = {
            "timestamp": datetime.now(),
            "permanent": not temporary
        }

