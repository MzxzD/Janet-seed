"""
Expansion Types and Data Structures

Defines the types of expansions available and the data structures
used to represent expansion opportunities.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ExpansionType(str, Enum):
    """Types of expansions available."""
    
    VOICE_IO = "voice_io"
    PERSISTENT_MEMORY = "persistent_memory"
    DELEGATION = "delegation"
    MODEL_INSTALLATION = "model_installation"
    N8N_INTEGRATION = "n8n_integration"
    HOME_ASSISTANT_INTEGRATION = "home_assistant_integration"
    PLEX_INTEGRATION = "plex_integration"


@dataclass
class ExpansionOpportunity:
    """Represents an opportunity to expand Janet's capabilities."""
    
    expansion_type: str
    name: str
    description: str
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    requirements: Dict = field(default_factory=dict)
    estimated_setup_time: str = "5-10 minutes"
    reversible: bool = True
    requires_network: bool = False
    hardware_sufficient: bool = False
    current_state: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "expansion_type": self.expansion_type,
            "name": self.name,
            "description": self.description,
            "benefits": self.benefits,
            "risks": self.risks,
            "requirements": self.requirements,
            "estimated_setup_time": self.estimated_setup_time,
            "reversible": self.reversible,
            "requires_network": self.requires_network,
            "hardware_sufficient": self.hardware_sufficient,
            "current_state": self.current_state,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExpansionOpportunity':
        """Create from dictionary."""
        return cls(
            expansion_type=data["expansion_type"],
            name=data["name"],
            description=data["description"],
            benefits=data.get("benefits", []),
            risks=data.get("risks", []),
            requirements=data.get("requirements", {}),
            estimated_setup_time=data.get("estimated_setup_time", "5-10 minutes"),
            reversible=data.get("reversible", True),
            requires_network=data.get("requires_network", False),
            hardware_sufficient=data.get("hardware_sufficient", False),
            current_state=data.get("current_state"),
        )

