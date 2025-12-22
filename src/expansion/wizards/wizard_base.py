"""
Wizard Base Class — Base for All Expansion Wizards

Provides common functionality for all expansion wizards.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Optional
from pathlib import Path


class ExpansionWizard(ABC):
    """Base class for all expansion wizards."""
    
    def __init__(self, config_path: Path, janet_core=None):
        """
        Initialize wizard.
        
        Args:
            config_path: Path to config directory
            janet_core: Optional JanetCore instance
        """
        self.config_path = Path(config_path)
        self.janet_core = janet_core
        self.config = {}
    
    @abstractmethod
    def run(self) -> bool:
        """
        Run the wizard.
        
        Returns:
            True if setup complete, False if cancelled or failed
        """
        pass
    
    def validate_requirements(self) -> Tuple[bool, List[str]]:
        """
        Validate that requirements are met.
        
        Returns:
            Tuple of (success: bool, missing_requirements: List[str])
        """
        return True, []
    
    @abstractmethod
    def setup(self) -> bool:
        """
        Perform the setup.
        
        Returns:
            True if setup successful
        """
        pass
    
    @abstractmethod
    def verify(self) -> bool:
        """
        Verify that setup was successful.
        
        Returns:
            True if verification passes
        """
        pass
    
    def cleanup_on_failure(self):
        """Clean up on failure (revert changes)."""
        pass
    
    def check_network_available(self) -> bool:
        """
        Check if network is available (optional, with consent).
        
        Returns:
            True if network appears available
        """
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except (OSError, socket.timeout, socket.error):
            return False
    
    def generate_offline_instructions(self) -> str:
        """
        Generate offline installation instructions.
        
        Returns:
            Instruction string
        """
        return "Offline installation instructions not implemented for this wizard."

