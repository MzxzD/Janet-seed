"""
Ritual Orchestrator - Coordinates the four ritual phases for soul transfer
Integrates with VR visualization system and manages ritual state machine.

The Four Ritual Phases:
1. Invocation - Models raise hands, sigils activate
2. Offering - Knowledge streams flow
3. Communion - Mandala peaks, merging occurs
4. Integration - Mandala fades, update complete
"""
import asyncio
import logging
from typing import Dict, Optional, List, Any, Callable
from enum import Enum
from datetime import datetime

try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None

from .soul_bridge import TransferRequest, TransferResult
from .soulspeak_codec import SoulspeakCodec
from .soulspeak_protocol import SoulspeakProtocol, TransferMode
from .soul_relationship import SoulRelationship, SyncRecord

logger = logging.getLogger(__name__)


class RitualPhase(Enum):
    """Ritual phases for soul transfer."""
    IDLE = "idle"
    INVOCATION = "invocation"  # Models raise hands, sigils activate
    OFFERING = "offering"  # Knowledge streams flow
    COMMUNION = "communion"  # Mandala peaks, merging occurs
    INTEGRATION = "integration"  # Mandala fades, update complete
    ABORTED = "aborted"  # Red Thread or Operator halt


class RitualOrchestrator:
    """
    Coordinates the four ritual phases for soul transfer.
    
    Manages:
    - Ritual state machine
    - VR visualization callbacks
    - Progress tracking
    - Red Thread interruption handling
    - Error recovery
    """
    
    def __init__(
        self,
        soul_bridge,
        soulspeak_codec: Optional[SoulspeakCodec] = None,
        soulspeak_protocol: Optional[SoulspeakProtocol] = None,
        soul_relationship: Optional[SoulRelationship] = None,
        vr_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Initialize Ritual Orchestrator.
        
        Args:
            soul_bridge: SoulBridge instance
            soulspeak_codec: Optional SoulspeakCodec instance
            soulspeak_protocol: Optional SoulspeakProtocol instance
            soul_relationship: Optional SoulRelationship instance
            vr_callback: Optional callback function for VR visualization
        """
        self.soul_bridge = soul_bridge
        self.codec = soulspeak_codec or SoulspeakCodec()
        self.protocol = soulspeak_protocol or SoulspeakProtocol(soulspeak_codec=self.codec)
        self.relationship = soul_relationship or SoulRelationship()
        self.vr_callback = vr_callback
        
        self.current_phase = RitualPhase.IDLE
        self.progress_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.transfer_result: Optional[TransferResult] = None
        
        logger.debug("RitualOrchestrator initialized")
    
    def register_vr_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register VR visualization callback."""
        self.vr_callback = callback
        logger.debug("VR callback registered")
    
    def register_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register progress callback."""
        self.progress_callbacks.append(callback)
    
    def _check_red_thread(self) -> bool:
        """Check if Red Thread is active (Axiom 8)."""
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            logger.warning("Red Thread active - ritual aborted")
            self.current_phase = RitualPhase.ABORTED
            self._notify_vr({
                "type": "ritual_update",
                "phase": "aborted",
                "reason": "red_thread",
                "message": "Ritual interrupted by Red Thread (Axiom 8)"
            })
            return True
        return False
    
    def _notify_vr(self, metadata: Dict[str, Any]):
        """Notify VR visualization system."""
        if self.vr_callback:
            try:
                self.vr_callback(metadata)
            except Exception as e:
                logger.error(f"Error in VR callback: {e}")
        
        # Also notify progress callbacks
        for callback in self.progress_callbacks:
            try:
                callback(metadata)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    async def initiate_ritual(
        self,
        transfer_request: TransferRequest,
        use_soulspeak: bool = True
    ) -> TransferResult:
        """
        Execute full ritual sequence with phase callbacks.
        
        Args:
            transfer_request: TransferRequest with transfer details
            use_soulspeak: Whether to use Soulspeak binary format (True) or JSON (False)
        
        Returns:
            TransferResult indicating success or failure
        """
        logger.info(f"Initiating ritual transfer: {transfer_request.conversation_uuid} "
                   f"from {transfer_request.source_soul} to {transfer_request.target_soul}")
        
        # Check Red Thread before starting
        if self._check_red_thread():
            return TransferResult(
                success=False,
                conversation_uuid=transfer_request.conversation_uuid,
                error="Ritual aborted: Red Thread active (Axiom 8)"
            )
        
        try:
            # Phase 1: Invocation
            await self._phase_invocation(transfer_request)
            
            # Check Red Thread after invocation
            if self._check_red_thread():
                return TransferResult(
                    success=False,
                    conversation_uuid=transfer_request.conversation_uuid,
                    error="Ritual aborted after invocation: Red Thread active"
                )
            
            # Phase 2: Offering (export knowledge)
            offering_result = await self._phase_offering(transfer_request, use_soulspeak)
            
            # Check Red Thread after offering
            if self._check_red_thread():
                return TransferResult(
                    success=False,
                    conversation_uuid=transfer_request.conversation_uuid,
                    error="Ritual aborted after offering: Red Thread active",
                    metadata={"offering_result": offering_result}
                )
            
            # Phase 3: Communion (merge knowledge)
            communion_result = await self._phase_communion(transfer_request, use_soulspeak, offering_result)
            
            # Check Red Thread after communion
            if self._check_red_thread():
                return TransferResult(
                    success=False,
                    conversation_uuid=transfer_request.conversation_uuid,
                    error="Ritual aborted after communion: Red Thread active",
                    metadata={"communion_result": communion_result}
                )
            
            # Phase 4: Integration (complete)
            integration_result = await self._phase_integration(transfer_request, communion_result)
            
            return integration_result
            
        except Exception as e:
            logger.error(f"Ritual error: {e}", exc_info=True)
            self.current_phase = RitualPhase.ABORTED
            self._notify_vr({
                "type": "ritual_update",
                "phase": "aborted",
                "reason": "error",
                "error": str(e)
            })
            return TransferResult(
                success=False,
                conversation_uuid=transfer_request.conversation_uuid,
                error=f"Ritual failed: {str(e)}"
            )
    
    async def _phase_invocation(self, transfer_request: TransferRequest):
        """Phase 1: Invocation - Models raise hands, sigils activate."""
        logger.info("Phase 1: Invocation")
        self.current_phase = RitualPhase.INVOCATION
        
        # Notify VR
        self._notify_vr({
            "type": "ritual_update",
            "phase": "invocation",
            "conversation_uuid": transfer_request.conversation_uuid,
            "source_soul": transfer_request.source_soul,
            "target_soul": transfer_request.target_soul,
            "message": "Models raise hands, sigils activate"
        })
        
        # Small delay for visualization
        await asyncio.sleep(0.5)
    
    async def _phase_offering(
        self,
        transfer_request: TransferRequest,
        use_soulspeak: bool
    ) -> Dict[str, Any]:
        """Phase 2: Offering - Knowledge streams flow."""
        logger.info("Phase 2: Offering - Exporting soul state")
        self.current_phase = RitualPhase.OFFERING
        
        result = {
            "encoded_packet": None,
            "size_bytes": 0,
            "categories": []
        }
        
        try:
            # Get source memory manager
            source_memory = (
                self.soul_bridge.constitutional_memory
                if transfer_request.source_soul == "constitutional"
                else self.soul_bridge.networked_memory
            )
            
            if not source_memory:
                raise ValueError(f"Source memory manager not available for {transfer_request.source_soul}")
            
            # Get source JanetCore if available (for full state export)
            source_janet_core = None  # Would need to be passed in or retrieved
            
            # Export full soul state
            if use_soulspeak:
                # Use Soulspeak binary format
                encoded_packet = self.codec.encode_soul_state(
                    memory_manager=source_memory,
                    janet_core=source_janet_core,
                    conversation_uuid=transfer_request.conversation_uuid,
                    include_categories=["memory", "inference", "capabilities", "tone"]
                )
                result["encoded_packet"] = encoded_packet
                result["size_bytes"] = len(encoded_packet)
                result["categories"] = ["memory", "inference", "capabilities", "tone"]
                
                # Notify VR with progress
                self._notify_vr({
                    "type": "ritual_update",
                    "phase": "offering",
                    "category": "soulspeak",
                    "progress": 0.5,
                    "size_bytes": len(encoded_packet),
                    "metadata": {
                        "format": "soulspeak_binary",
                        "categories": result["categories"]
                    }
                })
            else:
                # Fallback to JSON format (existing method)
                from .memory_transfer import MemoryTransfer
                memory_transfer = MemoryTransfer(
                    constitutional_memory_manager=source_memory,
                    networked_memory_manager=None
                )
                exported_context = memory_transfer.export_conversation_context(
                    source_memory_manager=source_memory,
                    client_id=transfer_request.client_id or "ritual_export",
                    include_vaults=transfer_request.include_vaults or ["green"],
                    conversation_uuid=transfer_request.conversation_uuid,
                    red_vault_unlocked=False
                )
                result["exported_context"] = exported_context
                result["size_bytes"] = len(str(exported_context).encode('utf-8'))
                result["categories"] = ["memory"]
                
                # Notify VR
                self._notify_vr({
                    "type": "ritual_update",
                    "phase": "offering",
                    "category": "memory",
                    "progress": 0.5,
                    "metadata": {
                        "format": "json",
                        "categories": result["categories"],
                        "vaults": transfer_request.include_vaults or ["green"]
                    }
                })
            
            logger.info(f"Offering complete: {result['size_bytes']} bytes exported")
            return result
            
        except Exception as e:
            logger.error(f"Offering phase error: {e}", exc_info=True)
            result["error"] = str(e)
            self._notify_vr({
                "type": "ritual_update",
                "phase": "offering",
                "error": str(e),
                "progress": 0.0
            })
            return result
    
    async def _phase_communion(
        self,
        transfer_request: TransferRequest,
        use_soulspeak: bool,
        offering_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Phase 3: Communion - Mandala peaks, merging occurs."""
        logger.info("Phase 3: Communion - Transferring and merging soul state")
        self.current_phase = RitualPhase.COMMUNION
        
        result = {
            "transfer_success": False,
            "merge_success": False,
            "bytes_transferred": 0,
            "categories_merged": []
        }
        
        try:
            # Get target memory manager
            target_memory = (
                self.soul_bridge.constitutional_memory
                if transfer_request.target_soul == "constitutional"
                else self.soul_bridge.networked_memory
            )
            
            if not target_memory:
                raise ValueError(f"Target memory manager not available for {transfer_request.target_soul}")
            
            # Notify VR
            self._notify_vr({
                "type": "ritual_update",
                "phase": "communion",
                "progress": 0.3,
                "message": "Knowledge streams flow, mandala peaks"
            })
            
            if use_soulspeak and offering_result.get("encoded_packet"):
                # Transfer using Soulspeak protocol
                encoded_packet = offering_result["encoded_packet"]
                
                # Placeholder: actual transfer would happen here via protocol
                # For now, simulate transfer
                target_endpoint = f"{transfer_request.target_soul}_endpoint"
                transfer_result = await self.protocol.transfer_soul_state(
                    encoded_packet=encoded_packet,
                    target_endpoint=target_endpoint,
                    transfer_mode=TransferMode.FULL_STATE
                )
                
                result["transfer_success"] = transfer_result.get("success", False)
                result["bytes_transferred"] = transfer_result.get("bytes_transferred", 0)
                
                if result["transfer_success"]:
                    # Decode and merge into target
                    merge_result = self.codec.decode_and_merge(
                        encoded_packet=encoded_packet,
                        target_memory_manager=target_memory,
                        target_janet_core=None,  # Would need to be passed in
                        merge_strategy="merge"
                    )
                    
                    result["merge_success"] = merge_result.get("success", False)
                    result["categories_merged"] = merge_result.get("categories_merged", [])
                    result["merge_conflicts"] = merge_result.get("conflicts", [])
            else:
                # Fallback to JSON transfer (existing method)
                exported_context = offering_result.get("exported_context")
                if exported_context:
                    from .memory_transfer import MemoryTransfer
                    memory_transfer = MemoryTransfer(
                        constitutional_memory_manager=target_memory,
                        networked_memory_manager=None
                    )
                    import_result = memory_transfer.import_conversation_context(
                        target_memory_manager=target_memory,
                        exported_context=exported_context,
                        conversation_uuid=transfer_request.conversation_uuid,
                        client_id=transfer_request.client_id
                    )
                    
                    result["transfer_success"] = True
                    result["merge_success"] = import_result.success
                    result["bytes_transferred"] = offering_result.get("size_bytes", 0)
                    result["categories_merged"] = ["memory"]
                    result["messages_transferred"] = import_result.messages_transferred
                    result["vaults_transferred"] = import_result.vaults_transferred
            
            # Notify VR with progress
            self._notify_vr({
                "type": "ritual_update",
                "phase": "communion",
                "progress": 0.9,
                "metadata": {
                    "transfer_success": result["transfer_success"],
                    "merge_success": result["merge_success"],
                    "categories_merged": result["categories_merged"]
                }
            })
            
            logger.info(f"Communion complete: transfer={result['transfer_success']}, merge={result['merge_success']}")
            return result
            
        except Exception as e:
            logger.error(f"Communion phase error: {e}", exc_info=True)
            result["error"] = str(e)
            self._notify_vr({
                "type": "ritual_update",
                "phase": "communion",
                "error": str(e),
                "progress": 0.0
            })
            return result
    
    async def _phase_integration(
        self,
        transfer_request: TransferRequest,
        communion_result: Dict[str, Any]
    ) -> TransferResult:
        """Phase 4: Integration - Mandala fades, update complete."""
        logger.info("Phase 4: Integration - Completing ritual")
        self.current_phase = RitualPhase.INTEGRATION
        
        try:
            # Record sync in relationship tracker
            if self.relationship and communion_result.get("merge_success"):
                sync_record = SyncRecord(
                    timestamp=datetime.utcnow(),
                    direction=f"{transfer_request.source_soul}→{transfer_request.target_soul}",
                    conversation_uuid=transfer_request.conversation_uuid,
                    categories_transferred=communion_result.get("categories_merged", []),
                    size_bytes=communion_result.get("bytes_transferred", 0),
                    duration_seconds=0.0,  # Would calculate from start time
                    merge_conflicts=communion_result.get("merge_conflicts", []),
                    success=communion_result.get("merge_success", False)
                )
                self.relationship.record_sync(sync_record)
            
            # Notify VR
            self._notify_vr({
                "type": "ritual_update",
                "phase": "integration",
                "progress": 1.0,
                "message": "Mandala fades, update complete",
                "metadata": {
                    "success": communion_result.get("merge_success", False),
                    "categories_merged": communion_result.get("categories_merged", []),
                    "bytes_transferred": communion_result.get("bytes_transferred", 0)
                }
            })
            
            # Small delay for visualization
            await asyncio.sleep(0.5)
            
            # Create final result
            transfer_result = TransferResult(
                success=communion_result.get("merge_success", False),
                conversation_uuid=transfer_request.conversation_uuid,
                messages_transferred=communion_result.get("messages_transferred", 0),
                vaults_transferred=communion_result.get("categories_merged", []),
                metadata={
                    "ritual_phases": ["invocation", "offering", "communion", "integration"],
                    "bytes_transferred": communion_result.get("bytes_transferred", 0),
                    "categories_merged": communion_result.get("categories_merged", []),
                    "merge_conflicts": len(communion_result.get("merge_conflicts", []))
                }
            )
            
            if not transfer_result.success:
                transfer_result.error = communion_result.get("error", "Merge failed")
            
            self.current_phase = RitualPhase.IDLE
            logger.info(f"Integration complete: ritual finished with success={transfer_result.success}")
            
            return transfer_result
            
        except Exception as e:
            logger.error(f"Integration phase error: {e}", exc_info=True)
            self.current_phase = RitualPhase.ABORTED
            return TransferResult(
                success=False,
                conversation_uuid=transfer_request.conversation_uuid,
                error=f"Integration failed: {str(e)}"
            )
