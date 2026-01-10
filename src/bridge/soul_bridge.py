"""
Soul Bridge Service - WebSocket bridge for state transfer between souls
Enables seamless, consent-based transfer of conversation context between
Janet-seed (Constitutional Soul) and Janet Mesh (Networked Soul).
"""
import uuid
import json
import asyncio
from typing import Dict, Optional, List, Any, Callable
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TransferRequest:
    """Request for soul transfer."""
    def __init__(
        self,
        conversation_uuid: str,
        source_soul: str,  # "constitutional" or "networked"
        target_soul: str,
        client_id: Optional[str] = None,
        include_vaults: Optional[List[str]] = None,  # ["green", "red"] - never blue
        consent_required: bool = True
    ):
        self.conversation_uuid = conversation_uuid
        self.source_soul = source_soul
        self.target_soul = target_soul
        self.client_id = client_id
        self.include_vaults = include_vaults or ["green"]  # Default: only safe Green Vault
        self.consent_required = consent_required
        self.created_at = datetime.utcnow()
        self.status = "pending"
        self.consent_granted = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "conversation_uuid": self.conversation_uuid,
            "source_soul": self.source_soul,
            "target_soul": self.target_soul,
            "client_id": self.client_id,
            "include_vaults": self.include_vaults,
            "consent_required": self.consent_required,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "consent_granted": self.consent_granted
        }


class TransferResult:
    """Result of soul transfer operation."""
    def __init__(
        self,
        success: bool,
        conversation_uuid: str,
        messages_transferred: int = 0,
        vaults_transferred: List[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.conversation_uuid = conversation_uuid
        self.messages_transferred = messages_transferred
        self.vaults_transferred = vaults_transferred or []
        self.error = error
        self.metadata = metadata or {}
        self.completed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "conversation_uuid": self.conversation_uuid,
            "messages_transferred": self.messages_transferred,
            "vaults_transferred": self.vaults_transferred,
            "error": self.error,
            "metadata": self.metadata,
            "completed_at": self.completed_at.isoformat()
        }


class SoulBridge:
    """
    WebSocket bridge service for state transfer between Constitutional and Networked Souls.
    
    Manages conversation UUID generation and tracking, handles memory-diff protocol
    (only transfer new messages), and enforces consent gates.
    """
    
    def __init__(
        self,
        constitutional_memory_manager=None,
        networked_memory_manager=None,
        consent_callback: Optional[Callable[[TransferRequest], bool]] = None
    ):
        """
        Initialize Soul Bridge.
        
        Args:
            constitutional_memory_manager: MemoryManager from Janet-seed (Constitutional Soul)
            networked_memory_manager: MemoryManager from Janet Mesh (Networked Soul)
            consent_callback: Async callback function to request consent (returns bool)
        """
        self.constitutional_memory = constitutional_memory_manager
        self.networked_memory = networked_memory_manager
        self.consent_callback = consent_callback
        
        # Track active transfers
        self.active_transfers: Dict[str, TransferRequest] = {}
        self.transfer_history: List[TransferResult] = []
        
        # Conversation UUID tracking
        self.conversation_registry: Dict[str, Dict[str, Any]] = {}
        
        # Optional ritual components
        self.soulspeak_codec = None
        self.ritual_orchestrator = None
        self.soul_relationship = None
        
        # Initialize if available
        try:
            from .soulspeak_codec import SoulspeakCodec
            from .ritual_orchestrator import RitualOrchestrator
            from .soul_relationship import SoulRelationship
            
            self.soulspeak_codec = SoulspeakCodec()
            self.soul_relationship = SoulRelationship()
            self.ritual_orchestrator = RitualOrchestrator(
                soul_bridge=self,
                soulspeak_codec=self.soulspeak_codec,
                soul_relationship=self.soul_relationship
            )
            logger.debug("Ritual components initialized")
        except ImportError as e:
            logger.warning(f"Ritual components not available, using basic transfer: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize ritual components: {e}")
    
    def generate_conversation_uuid(self, client_id: Optional[str] = None) -> str:
        """
        Generate a unique conversation UUID for tracking across souls.
        
        Args:
            client_id: Optional client identifier to associate with UUID
            
        Returns:
            Unique conversation UUID string
        """
        conversation_uuid = str(uuid.uuid4())
        
        # Register conversation
        self.conversation_registry[conversation_uuid] = {
            "uuid": conversation_uuid,
            "client_id": client_id,
            "created_at": datetime.utcnow().isoformat(),
            "souls": {
                "constitutional": False,
                "networked": False
            },
            "last_transfer": None
        }
        
        logger.info(f"Generated conversation UUID: {conversation_uuid} for client: {client_id}")
        return conversation_uuid
    
    def register_conversation(self, conversation_uuid: str, soul_type: str, client_id: Optional[str] = None):
        """
        Register that a conversation exists in a specific soul.
        
        Args:
            conversation_uuid: Conversation UUID
            soul_type: "constitutional" or "networked"
            client_id: Optional client identifier
        """
        if conversation_uuid not in self.conversation_registry:
            self.conversation_registry[conversation_uuid] = {
                "uuid": conversation_uuid,
                "client_id": client_id,
                "created_at": datetime.utcnow().isoformat(),
                "souls": {
                    "constitutional": False,
                    "networked": False
                },
                "last_transfer": None
            }
        
        if soul_type in self.conversation_registry[conversation_uuid]["souls"]:
            self.conversation_registry[conversation_uuid]["souls"][soul_type] = True
            if client_id:
                self.conversation_registry[conversation_uuid]["client_id"] = client_id
        
        logger.debug(f"Registered conversation {conversation_uuid} in {soul_type} soul")
    
    async def request_transfer(
        self,
        source_soul: str,
        target_soul: str,
        conversation_uuid: Optional[str] = None,
        client_id: Optional[str] = None,
        include_vaults: Optional[List[str]] = None
    ) -> TransferRequest:
        """
        Create a transfer request and trigger consent gate if needed.
        
        Args:
            source_soul: "constitutional" or "networked"
            target_soul: "constitutional" or "networked"
            conversation_uuid: Optional existing UUID, generates new if None
            client_id: Optional client identifier
            include_vaults: List of vaults to include ["green", "red"] - never "blue"
            
        Returns:
            TransferRequest object
        """
        # Generate UUID if not provided
        if not conversation_uuid:
            conversation_uuid = self.generate_conversation_uuid(client_id)
        
        # Validate vault selection (never allow Blue Vault)
        if include_vaults:
            include_vaults = [v for v in include_vaults if v != "blue"]
        
        # Create transfer request
        request = TransferRequest(
            conversation_uuid=conversation_uuid,
            source_soul=source_soul,
            target_soul=target_soul,
            client_id=client_id,
            include_vaults=include_vaults or ["green"],
            consent_required=True
        )
        
        # Store active transfer
        self.active_transfers[conversation_uuid] = request
        
        # Request consent if callback provided
        if self.consent_callback:
            try:
                request.consent_granted = await self.consent_callback(request)
                if not request.consent_granted:
                    request.status = "consent_denied"
                    logger.info(f"Transfer consent denied for {conversation_uuid}")
                    return request
            except Exception as e:
                logger.error(f"Error requesting consent: {e}")
                request.status = "consent_error"
                request.consent_granted = False
                return request
        
        request.status = "consent_granted"
        logger.info(f"Transfer request created: {conversation_uuid} from {source_soul} to {target_soul}")
        return request
    
    def get_transfer_status(self, conversation_uuid: str) -> Optional[TransferRequest]:
        """Get status of a transfer request."""
        return self.active_transfers.get(conversation_uuid)
    
    def get_conversation_info(self, conversation_uuid: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered conversation."""
        return self.conversation_registry.get(conversation_uuid)
    
    def record_transfer_result(self, result: TransferResult):
        """Record a completed transfer result."""
        self.transfer_history.append(result)
        
        # Update conversation registry
        if result.conversation_uuid in self.conversation_registry:
            self.conversation_registry[result.conversation_uuid]["last_transfer"] = result.completed_at.isoformat()
        
        # Clean up active transfer
        if result.conversation_uuid in self.active_transfers:
            del self.active_transfers[result.conversation_uuid]
        
        logger.info(f"Recorded transfer result for {result.conversation_uuid}: success={result.success}")
    
    async def initiate_ritual_transfer(
        self,
        transfer_request: TransferRequest,
        use_soulspeak: bool = True,
        trigger_vr_visualization: bool = False,
        vr_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> TransferResult:
        """
        Initiate transfer using ritual protocol with optional VR visualization.
        
        Falls back to standard transfer if ritual components unavailable.
        
        Args:
            transfer_request: TransferRequest with transfer details
            use_soulspeak: Whether to use Soulspeak binary format (True) or JSON (False)
            trigger_vr_visualization: Whether to trigger VR visualization
            vr_callback: Optional callback function for VR visualization updates
        
        Returns:
            TransferResult indicating success or failure
        """
        # Check if ritual components are available
        if not self.ritual_orchestrator:
            logger.warning("Ritual components not available, falling back to standard transfer")
            # Fallback to standard transfer
            request = await self.request_transfer(
                source_soul=transfer_request.source_soul,
                target_soul=transfer_request.target_soul,
                conversation_uuid=transfer_request.conversation_uuid,
                client_id=transfer_request.client_id,
                include_vaults=transfer_request.include_vaults
            )
            
            if not request.consent_granted:
                return TransferResult(
                    success=False,
                    conversation_uuid=transfer_request.conversation_uuid,
                    error="Transfer cancelled: consent denied"
                )
            
            # Use existing memory transfer (would need to be implemented)
            # For now, return a placeholder result
            return TransferResult(
                success=False,
                conversation_uuid=transfer_request.conversation_uuid,
                error="Standard transfer not fully implemented - use ritual transfer"
            )
        
        # Register VR callback if provided
        if trigger_vr_visualization and vr_callback:
            self.ritual_orchestrator.register_vr_callback(vr_callback)
        
        # Execute ritual
        try:
            result = await self.ritual_orchestrator.initiate_ritual(
                transfer_request,
                use_soulspeak=use_soulspeak
            )
            
            # Record result
            if result:
                self.record_transfer_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Ritual transfer error: {e}", exc_info=True)
            return TransferResult(
                success=False,
                conversation_uuid=transfer_request.conversation_uuid,
                error=f"Ritual transfer failed: {str(e)}"
            )