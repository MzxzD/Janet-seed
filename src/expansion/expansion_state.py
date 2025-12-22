"""
Expansion State Manager — Tracks Enabled Expansions and Consent Records

Manages expansion state, consent records, and configuration storage.
All expansions require explicit consent with timestamps and fingerprints.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ExpansionState:
    """Represents the current expansion state."""
    
    enabled_expansions: Dict[str, Dict] = field(default_factory=dict)
    consent_records: List[Dict] = field(default_factory=list)
    
    def is_enabled(self, expansion_type: str) -> bool:
        """Check if an expansion is enabled."""
        return expansion_type in self.enabled_expansions
    
    def get_config(self, expansion_type: str) -> Optional[Dict]:
        """Get configuration for an expansion."""
        return self.enabled_expansions.get(expansion_type)
    
    def enable(self, expansion_type: str, config: Dict, consent_data: Dict):
        """Enable an expansion with configuration and consent record."""
        self.enabled_expansions[expansion_type] = config
        self.consent_records.append({
            "expansion_type": expansion_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": "enabled",
            **consent_data
        })
    
    def disable(self, expansion_type: str, consent_data: Dict):
        """Disable an expansion and record consent."""
        if expansion_type in self.enabled_expansions:
            del self.enabled_expansions[expansion_type]
            self.consent_records.append({
                "expansion_type": expansion_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "action": "disabled",
                **consent_data
            })


class ExpansionStateManager:
    """Manages expansion state persistence and retrieval."""
    
    def __init__(self, config_path: Path):
        """
        Initialize expansion state manager.
        
        Args:
            config_path: Path to config directory
        """
        self.config_path = Path(config_path)
        self.state_file = self.config_path / "expansion_state.json"
        self.consent_file = self.config_path / "expansion_consent.json"
        
        # Ensure config directory exists
        self.config_path.mkdir(parents=True, exist_ok=True)
    
    def load_expansion_state(self) -> ExpansionState:
        """
        Load expansion state from disk.
        
        Returns:
            ExpansionState object
        """
        state = ExpansionState()
        
        # Load enabled expansions
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    state.enabled_expansions = data.get("enabled_expansions", {})
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Error loading expansion state: {e}")
                state.enabled_expansions = {}
        
        # Load consent records
        if self.consent_file.exists():
            try:
                with open(self.consent_file, 'r') as f:
                    state.consent_records = json.load(f).get("consent_records", [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Error loading consent records: {e}")
                state.consent_records = []
        
        return state
    
    def save_expansion_state(self, state: ExpansionState):
        """
        Save expansion state to disk.
        
        Args:
            state: ExpansionState to save
        """
        try:
            # Save enabled expansions
            with open(self.state_file, 'w') as f:
                json.dump({
                    "enabled_expansions": state.enabled_expansions,
                    "last_updated": datetime.utcnow().isoformat() + "Z"
                }, f, indent=2)
            
            # Save consent records
            with open(self.consent_file, 'w') as f:
                json.dump({
                    "consent_records": state.consent_records,
                    "last_updated": datetime.utcnow().isoformat() + "Z"
                }, f, indent=2)
        except IOError as e:
            print(f"⚠️  Error saving expansion state: {e}")
    
    def save_expansion_consent(self, expansion_type: str, consent_data: Dict):
        """
        Save a consent record for an expansion.
        
        Args:
            expansion_type: Type of expansion
            consent_data: Consent data (timestamp, fingerprint, etc.)
        """
        state = self.load_expansion_state()
        state.consent_records.append({
            "expansion_type": expansion_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **consent_data
        })
        self.save_expansion_state(state)
    
    def is_expansion_enabled(self, expansion_type: str) -> bool:
        """
        Check if an expansion is enabled.
        
        Args:
            expansion_type: Type of expansion
        
        Returns:
            True if enabled
        """
        state = self.load_expansion_state()
        return state.is_enabled(expansion_type)
    
    def enable_expansion(self, expansion_type: str, config: Dict, consent_data: Dict):
        """
        Enable an expansion.
        
        Args:
            expansion_type: Type of expansion
            config: Configuration for the expansion
            consent_data: Consent data (hardware fingerprint, etc.)
        """
        state = self.load_expansion_state()
        state.enable(expansion_type, config, consent_data)
        self.save_expansion_state(state)
    
    def disable_expansion(self, expansion_type: str, consent_data: Dict):
        """
        Disable an expansion.
        
        Args:
            expansion_type: Type of expansion
            consent_data: Consent data for disabling
        """
        state = self.load_expansion_state()
        state.disable(expansion_type, consent_data)
        self.save_expansion_state(state)
    
    def get_expansion_config(self, expansion_type: str) -> Optional[Dict]:
        """
        Get configuration for an expansion.
        
        Args:
            expansion_type: Type of expansion
        
        Returns:
            Configuration dict or None
        """
        state = self.load_expansion_state()
        return state.get_config(expansion_type)
    
    def generate_hardware_fingerprint(self, hardware_dict: Dict) -> str:
        """
        Generate hardware fingerprint for consent records.
        
        Args:
            hardware_dict: Hardware profile dictionary
        
        Returns:
            Hardware fingerprint hash
        """
        # Create a stable fingerprint from hardware characteristics
        fingerprint_data = json.dumps({
            "platform": hardware_dict.get("platform"),
            "architecture": hardware_dict.get("architecture"),
            "memory_gb": hardware_dict.get("memory_gb"),
            "cpu_cores": hardware_dict.get("cpu_cores_physical"),
        }, sort_keys=True)
        
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

