"""
Expansion Detector — Detects Available Expansion Opportunities

Analyzes hardware and current state to identify expansion opportunities.
Never auto-installs - only detects and suggests.
"""

from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from hardware_detector import HardwareProfile

from .expansion_types import ExpansionType, ExpansionOpportunity


class ExpansionDetector:
    """Detects expansion opportunities based on hardware and current state."""
    
    def __init__(self, hardware_profile: 'HardwareProfile', current_state: Optional[Dict] = None):
        """
        Initialize expansion detector.
        
        Args:
            hardware_profile: Detected hardware capabilities
            current_state: Current expansion state (enabled features, etc.)
        """
        self.hardware = hardware_profile
        self.current_state = current_state or {}
    
    def detect_available_expansions(self) -> List[ExpansionOpportunity]:
        """
        Detect all available expansion opportunities.
        
        Returns:
            List of expansion opportunities
        """
        opportunities = []
        
        # Check each expansion type
        if self._can_expand_voice_io():
            opportunities.append(self._create_voice_io_opportunity())
        
        if self._can_expand_memory():
            opportunities.append(self._create_memory_opportunity())
        
        if self._can_expand_delegation():
            opportunities.append(self._create_delegation_opportunity())
        
        if self._can_expand_models():
            opportunities.extend(self._create_model_opportunities())
        
        if self._can_expand_n8n():
            opportunities.append(self._create_n8n_opportunity())
        
        if self._can_expand_home_assistant():
            opportunities.append(self._create_home_assistant_opportunity())
        
        if self._can_expand_plex():
            opportunities.append(self._create_plex_opportunity())
        
        return opportunities
    
    def can_expand_to(self, expansion_type: str, hardware: Optional['HardwareProfile'] = None) -> bool:
        """
        Check if a specific expansion type is possible.
        
        Args:
            expansion_type: Type of expansion to check
            hardware: Optional hardware profile (uses self.hardware if None)
        
        Returns:
            True if expansion is possible
        """
        hw = hardware or self.hardware
        
        if expansion_type == ExpansionType.VOICE_IO:
            return self._can_expand_voice_io(hw)
        elif expansion_type == ExpansionType.PERSISTENT_MEMORY:
            return self._can_expand_memory(hw)
        elif expansion_type == ExpansionType.DELEGATION:
            return self._can_expand_delegation(hw)
        elif expansion_type == ExpansionType.MODEL_INSTALLATION:
            return self._can_expand_models(hw)
        elif expansion_type == ExpansionType.N8N_INTEGRATION:
            return self._can_expand_n8n(hw)
        elif expansion_type == ExpansionType.HOME_ASSISTANT_INTEGRATION:
            return self._can_expand_home_assistant(hw)
        elif expansion_type == ExpansionType.PLEX_INTEGRATION:
            return self._can_expand_plex(hw)
        
        return False
    
    def get_expansion_requirements(self, expansion_type: str) -> Dict:
        """
        Get requirements for a specific expansion type.
        
        Args:
            expansion_type: Type of expansion
        
        Returns:
            Dictionary of requirements
        """
        requirements_map = {
            ExpansionType.VOICE_IO: {
                "memory_gb": 4,
                "disk_gb": 2,
                "microphone": True,
                "speaker": True,
                "dependencies": ["openai-whisper", "sounddevice", "pyttsx3"],
            },
            ExpansionType.PERSISTENT_MEMORY: {
                "memory_gb": 6,
                "disk_gb": 5,
                "dependencies": ["chromadb", "cryptography"],
            },
            ExpansionType.DELEGATION: {
                "memory_gb": 8,
                "disk_gb": 3,
                "dependencies": ["litellm"],
            },
            ExpansionType.MODEL_INSTALLATION: {
                "memory_gb": 8,
                "disk_gb": 10,
                "ollama": True,
            },
            ExpansionType.N8N_INTEGRATION: {
                "network": True,
                "n8n_instance": True,
            },
            ExpansionType.HOME_ASSISTANT_INTEGRATION: {
                "network": True,
                "home_assistant_instance": True,
            },
        }
        
        return requirements_map.get(expansion_type, {})
    
    # Private helper methods
    
    def _can_expand_voice_io(self, hardware: Optional['HardwareProfile'] = None) -> bool:
        """Check if voice I/O expansion is possible."""
        hw = hardware or self.hardware
        if self.current_state.get("voice_io_enabled", False):
            return False  # Already enabled
        
        return hw.can_run_feature("voice_stt") and hw.can_run_feature("voice_tts")
    
    def _can_expand_memory(self, hardware: Optional['HardwareProfile'] = None) -> bool:
        """Check if persistent memory expansion is possible."""
        hw = hardware or self.hardware
        if self.current_state.get("memory_enabled", False):
            return False  # Already enabled
        
        return hw.can_run_feature("memory_persistence")
    
    def _can_expand_delegation(self, hardware: Optional['HardwareProfile'] = None) -> bool:
        """Check if delegation expansion is possible."""
        hw = hardware or self.hardware
        if self.current_state.get("delegation_enabled", False):
            return False  # Already enabled
        
        return hw.can_run_feature("delegation")
    
    def _can_expand_models(self, hardware: Optional['HardwareProfile'] = None) -> bool:
        """Check if model installation expansion is possible."""
        hw = hardware or self.hardware
        # Models can be added if hardware supports it and Ollama is available
        return hw.memory_gb >= 8 and hw.disk_free_gb >= 10
    
    def _can_expand_n8n(self, hardware: Optional['HardwareProfile'] = None) -> bool:
        """Check if n8n integration is possible."""
        # n8n requires network access and an n8n instance
        # This is a placeholder - actual check would verify n8n availability
        return True  # Always possible if user has n8n set up
    
    def _can_expand_home_assistant(self, hardware: Optional['HardwareProfile'] = None) -> bool:
        """Check if Home Assistant integration is possible."""
        # Home Assistant requires network access and a Home Assistant instance
        # This is a placeholder - actual check would verify HA availability
        return True  # Always possible if user has HA set up
    
    def _create_voice_io_opportunity(self) -> ExpansionOpportunity:
        """Create voice I/O expansion opportunity."""
        return ExpansionOpportunity(
            expansion_type=ExpansionType.VOICE_IO,
            name="Voice Input/Output",
            description="Enable voice interaction with Janet using speech-to-text and text-to-speech.",
            benefits=[
                "Hands-free interaction",
                "More natural conversation flow",
                "Wake word detection ('Hey Janet')",
                "Tone-aware responses"
            ],
            risks=[
                "Requires microphone permissions",
                "May consume more resources",
                "Audio quality depends on hardware"
            ],
            requirements={
                "memory_gb": 4,
                "disk_gb": 2,
                "microphone": True,
                "speaker": True,
            },
            estimated_setup_time="5-10 minutes",
            reversible=True,
            requires_network=False,  # Can install dependencies offline
            hardware_sufficient=self.hardware.can_run_feature("voice_stt"),
        )
    
    def _create_memory_opportunity(self) -> ExpansionOpportunity:
        """Create persistent memory expansion opportunity."""
        return ExpansionOpportunity(
            expansion_type=ExpansionType.PERSISTENT_MEMORY,
            name="Persistent Memory",
            description="Enable long-term memory storage for conversations and learned patterns.",
            benefits=[
                "Conversation continuity across sessions",
                "Learned preferences and patterns",
                "Semantic search through past conversations",
                "Encrypted episodic memory"
            ],
            risks=[
                "Requires additional disk space",
                "Memory writes are gated by constitutional rules",
                "Privacy considerations for stored data"
            ],
            requirements={
                "memory_gb": 6,
                "disk_gb": 5,
            },
            estimated_setup_time="5 minutes",
            reversible=True,
            requires_network=False,
            hardware_sufficient=self.hardware.can_run_feature("memory_persistence"),
        )
    
    def _create_delegation_opportunity(self) -> ExpansionOpportunity:
        """Create delegation expansion opportunity."""
        return ExpansionOpportunity(
            expansion_type=ExpansionType.DELEGATION,
            name="Task Delegation",
            description="Enable routing tasks to specialized models or automation tools.",
            benefits=[
                "Specialized model routing (programming, deep thinking)",
                "Integration with n8n for automation",
                "Home Assistant control",
                "More capable task handling"
            ],
            risks=[
                "Requires additional models (disk space)",
                "Network access needed for some integrations",
                "More complex error handling"
            ],
            requirements={
                "memory_gb": 8,
                "disk_gb": 3,
            },
            estimated_setup_time="10-15 minutes",
            reversible=True,
            requires_network=False,  # Models can be installed offline
            hardware_sufficient=self.hardware.can_run_feature("delegation"),
        )
    
    def _create_model_opportunities(self) -> List[ExpansionOpportunity]:
        """Create model installation opportunities."""
        opportunities = []
        
        # Suggest common useful models based on hardware
        if self.hardware.memory_gb >= 8:
            opportunities.append(ExpansionOpportunity(
                expansion_type=ExpansionType.MODEL_INSTALLATION,
                name="DeepSeek Coder (6.7B)",
                description="Add DeepSeek Coder model for advanced programming assistance.",
                benefits=[
                    "Specialized coding assistance",
                    "Better code generation and debugging",
                    "Rubber ducking for complex problems"
                ],
                risks=[
                    "Requires ~4GB disk space",
                    "May be slower on lower-end hardware"
                ],
                requirements={
                    "memory_gb": 8,
                    "disk_gb": 4,
                    "ollama": True,
                },
                estimated_setup_time="10-30 minutes (depending on download method)",
                reversible=True,
                requires_network=False,  # Can be installed offline
                hardware_sufficient=self.hardware.memory_gb >= 8,
            ))
        
        return opportunities
    
    def _create_n8n_opportunity(self) -> ExpansionOpportunity:
        """Create n8n integration opportunity."""
        return ExpansionOpportunity(
            expansion_type=ExpansionType.N8N_INTEGRATION,
            name="n8n Automation Integration",
            description="Connect Janet to n8n for workflow automation and task delegation.",
            benefits=[
                "Automate repetitive tasks",
                "Integrate with external services",
                "Create custom workflows",
                "Extend Janet's capabilities"
            ],
            risks=[
                "Requires n8n instance running",
                "Network access needed",
                "Security considerations for API access"
            ],
            requirements={
                "network": True,
                "n8n_instance": True,
            },
            estimated_setup_time="10-15 minutes",
            reversible=True,
            requires_network=True,
            hardware_sufficient=True,  # Depends on n8n availability, not local hardware
        )
    
    def _create_home_assistant_opportunity(self) -> ExpansionOpportunity:
        """Create Home Assistant integration opportunity."""
        return ExpansionOpportunity(
            expansion_type=ExpansionType.HOME_ASSISTANT_INTEGRATION,
            name="Home Assistant Integration",
            description="Connect Janet to Home Assistant for smart home control.",
            benefits=[
                "Voice control of smart home devices",
                "Automated home management",
                "Integration with existing HA automations"
            ],
            risks=[
                "Requires Home Assistant instance",
                "Network access needed",
                "Security considerations for device control"
            ],
            requirements={
                "network": True,
                "home_assistant_instance": True,
            },
            estimated_setup_time="10-15 minutes",
            reversible=True,
            requires_network=True,
            hardware_sufficient=True,  # Depends on HA availability, not local hardware
        )
    
    def _can_expand_plex(self, hardware: Optional['HardwareProfile'] = None) -> bool:
        """
        Check if Plex integration is possible.
        
        Args:
            hardware: Optional hardware profile (uses self.hardware if None)
            
        Returns:
            True if Plex integration is possible (depends on local Plex server availability)
        """
        hw = hardware or self.hardware
        
        # Check if already enabled
        if self.current_state.get("plex_integration_enabled", False):
            return False
        
        # Check if network available (for Plex server discovery)
        # Plex integration requires local network access to Plex server
        # We can't auto-detect Plex server, but we can suggest if network is available
        # or if user has plexapi installed
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            network_available = True
        except (OSError, socket.timeout, socket.error):
            network_available = False
        
        # Check if plexapi is available (optional, can be installed during wizard)
        try:
            import plexapi
            plexapi_available = True
        except ImportError:
            plexapi_available = False
        
        # Suggest Plex if network available (user can configure manually if offline)
        # Plex server itself may be on local network, so we suggest if network available
        return network_available or plexapi_available
    
    def _create_plex_opportunity(self) -> ExpansionOpportunity:
        """Create Plex Media Server integration opportunity."""
        return ExpansionOpportunity(
            expansion_type=ExpansionType.PLEX_INTEGRATION,
            name="Plex Media Server Integration",
            description="Connect Janet to your local Plex Media Server for media browsing and playback control.",
            benefits=[
                "Browse your Plex library via voice/text",
                "Control playback on Plex clients (TV, speakers, etc.)",
                "Get recommendations based on watch history (with consent)",
                "Query library statistics (unwatched episodes, recent additions)"
            ],
            risks=[
                "Requires local Plex Media Server running",
                "Network access to Plex server needed",
                "Media preferences stored in Green Vault (with consent only)",
                "Watch history tracking requires explicit consent"
            ],
            requirements={
                "network": True,  # Local network for Plex server
                "plex_server": True,  # User's local Plex server
                "plex_token": True,  # Authentication token
            },
            estimated_setup_time="10-15 minutes",
            reversible=True,
            requires_network=True,  # Local network for Plex server
            hardware_sufficient=True,  # Depends on Plex server availability, not local hardware
        )

