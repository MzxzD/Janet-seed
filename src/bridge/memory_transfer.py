"""
Memory Transfer Protocol - Transfer memory between souls respecting vault rules
Green Vault: Safe summaries transferable with consent
Blue Vault: Never transferred (ephemeral, session-only)
Red Vault: Encrypted secrets require explicit Operator approval + safe word
"""
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
from pathlib import Path

from .soul_bridge import TransferRequest, TransferResult

logger = logging.getLogger(__name__)


class MemoryTransfer:
    """
    Handles memory transfer between Constitutional and Networked Souls
    respecting vault privacy rules and consent gates.
    """
    
    def __init__(
        self,
        constitutional_memory_manager=None,
        networked_memory_manager=None,
        red_vault_unlock_required: bool = True
    ):
        """
        Initialize Memory Transfer.
        
        Args:
            constitutional_memory_manager: MemoryManager from Janet-seed
            networked_memory_manager: MemoryManager from Janet Mesh (SQLite-based)
            red_vault_unlock_required: Whether Red Vault requires safe word unlock
        """
        self.constitutional_memory = constitutional_memory_manager
        self.networked_memory = networked_memory_manager
        self.red_vault_unlock_required = red_vault_unlock_required
    
    def export_conversation_context(
        self,
        source_memory_manager,
        client_id: str,
        include_vaults: List[str],
        conversation_uuid: str,
        red_vault_unlocked: bool = False
    ) -> Dict[str, Any]:
        """
        Export conversation context from source memory manager.
        
        Args:
            source_memory_manager: Source memory manager (constitutional or networked)
            client_id: Client identifier
            include_vaults: List of vaults to include ["green", "red"]
            conversation_uuid: Conversation UUID for tracking
            red_vault_unlocked: Whether Red Vault is unlocked and can be accessed
            
        Returns:
            Dictionary containing exported context
        """
        exported = {
            "conversation_uuid": conversation_uuid,
            "client_id": client_id,
            "exported_at": datetime.utcnow().isoformat(),
            "vaults": {},
            "messages": []
        }
        
        # Export Green Vault (safe summaries)
        if "green" in include_vaults and source_memory_manager:
            try:
                if hasattr(source_memory_manager, 'green_vault'):
                    # Get Green Vault summaries
                    green_context = self._export_green_vault(
                        source_memory_manager.green_vault,
                        client_id
                    )
                    exported["vaults"]["green"] = green_context
                    logger.info(f"Exported Green Vault for {conversation_uuid}")
            except Exception as e:
                logger.error(f"Error exporting Green Vault: {e}")
                exported["vaults"]["green"] = {"error": str(e)}
        
        # Export Red Vault (encrypted secrets) - requires explicit unlock
        if "red" in include_vaults:
            if not red_vault_unlocked and self.red_vault_unlock_required:
                logger.warning(f"Red Vault export requested but not unlocked for {conversation_uuid}")
                exported["vaults"]["red"] = {
                    "status": "locked",
                    "message": "Red Vault requires safe word unlock before transfer"
                }
            elif source_memory_manager and hasattr(source_memory_manager, 'red_vault'):
                try:
                    red_context = self._export_red_vault(
                        source_memory_manager.red_vault,
                        client_id
                    )
                    exported["vaults"]["red"] = red_context
                    logger.info(f"Exported Red Vault for {conversation_uuid}")
                except Exception as e:
                    logger.error(f"Error exporting Red Vault: {e}")
                    exported["vaults"]["red"] = {"error": str(e)}
        
        # Export conversation messages
        try:
            if source_memory_manager:
                messages = self._export_conversation_messages(
                    source_memory_manager,
                    client_id
                )
                exported["messages"] = messages
                logger.info(f"Exported {len(messages)} messages for {conversation_uuid}")
        except Exception as e:
            logger.error(f"Error exporting messages: {e}")
            exported["messages"] = []
        
        # Note: Blue Vault is NEVER exported (ephemeral, session-only)
        exported["vaults"]["blue"] = {
            "status": "not_transferred",
            "message": "Blue Vault is ephemeral and never transferred (Axiom 9)"
        }
        
        return exported
    
    def _export_green_vault(self, green_vault, client_id: str) -> Dict[str, Any]:
        """Export Green Vault safe summaries."""
        try:
            # Green Vault stores safe, distilled summaries
            # Get summaries related to this client/conversation
            summaries = []
            
            if hasattr(green_vault, 'get_summaries'):
                summaries_data = green_vault.get_summaries(client_id=client_id)
                if summaries_data:
                    summaries = summaries_data
            elif hasattr(green_vault, 'get_recent_summaries'):
                # Fallback: get recent summaries
                summaries_data = green_vault.get_recent_summaries(limit=50)
                if summaries_data:
                    summaries = summaries_data
            
            return {
                "status": "exported",
                "summary_count": len(summaries),
                "summaries": summaries[:100],  # Limit to 100 for transfer
                "note": "Green Vault contains safe, distilled summaries only"
            }
        except Exception as e:
            logger.error(f"Error exporting Green Vault: {e}")
            return {"status": "error", "error": str(e)}
    
    def _export_red_vault(self, red_vault, client_id: str) -> Dict[str, Any]:
        """Export Red Vault encrypted secrets (requires unlock)."""
        try:
            # Red Vault stores encrypted secrets
            # Only export if unlocked
            secrets = []
            
            if hasattr(red_vault, 'get_unlocked_secrets'):
                secrets_data = red_vault.get_unlocked_secrets(client_id=client_id)
                if secrets_data:
                    secrets = secrets_data
            elif hasattr(red_vault, 'list_secrets'):
                # Fallback: list secret keys (not values, unless unlocked)
                secret_keys = red_vault.list_secrets(client_id=client_id)
                if secret_keys:
                    secrets = [{"key": k, "encrypted": True} for k in secret_keys]
            
            return {
                "status": "exported",
                "secret_count": len(secrets),
                "secrets": secrets[:50],  # Limit to 50 for transfer
                "note": "Red Vault contains encrypted secrets (require safe word to decrypt)"
            }
        except Exception as e:
            logger.error(f"Error exporting Red Vault: {e}")
            return {"status": "error", "error": str(e)}
    
    def _export_conversation_messages(
        self,
        memory_manager,
        client_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Export conversation messages from memory manager."""
        try:
            # Try different methods depending on memory manager type
            messages = []
            
            # For Janet-seed MemoryManager (vault system)
            if hasattr(memory_manager, 'get_client_memory_context'):
                messages = memory_manager.get_client_memory_context(client_id, limit=limit)
            elif hasattr(memory_manager, 'get_conversation_history'):
                messages = memory_manager.get_conversation_history(client_id, limit=limit)
            # For Janet Mesh MemoryManager (SQLite-based)
            elif hasattr(memory_manager, 'get_client_memory_context'):
                messages = memory_manager.get_client_memory_context(client_id)
                if messages and len(messages) > limit:
                    messages = messages[-limit:]
            
            # Convert to standard format
            exported_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    exported_messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                        "timestamp": msg.get("timestamp"),
                        "metadata": msg.get("metadata", {})
                    })
                else:
                    # Handle different formats
                    exported_messages.append({
                        "role": getattr(msg, "role", "user"),
                        "content": getattr(msg, "content", str(msg)),
                        "timestamp": getattr(msg, "timestamp", None),
                        "metadata": {}
                    })
            
            return exported_messages
            
        except Exception as e:
            logger.error(f"Error exporting conversation messages: {e}")
            return []
    
    def import_conversation_context(
        self,
        target_memory_manager,
        exported_context: Dict[str, Any],
        conversation_uuid: str,
        client_id: Optional[str] = None
    ) -> TransferResult:
        """
        Import conversation context into target memory manager.
        
        Args:
            target_memory_manager: Target memory manager (constitutional or networked)
            exported_context: Exported context dictionary
            conversation_uuid: Conversation UUID for tracking
            client_id: Optional client identifier override
            
        Returns:
            TransferResult indicating success or failure
        """
        if not target_memory_manager:
            return TransferResult(
                success=False,
                conversation_uuid=conversation_uuid,
                error="Target memory manager not available"
            )
        
        client_id = client_id or exported_context.get("client_id")
        if not client_id:
            return TransferResult(
                success=False,
                conversation_uuid=conversation_uuid,
                error="Client ID required for import"
            )
        
        messages_transferred = 0
        vaults_transferred = []
        errors = []
        
        try:
            # Import conversation messages
            messages = exported_context.get("messages", [])
            # Group messages into conversation pairs (user + assistant)
            conversation_pairs = []
            current_user = None
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    current_user = {"role": role, "content": content}
                elif role == "assistant" and current_user:
                    # Pair found
                    conversation_pairs.append([current_user, {"role": role, "content": content}])
                    current_user = None
            
            # Import conversation pairs
            for pair in conversation_pairs:
                try:
                    # Try Janet-seed MemoryManager.store_conversation() method
                    if hasattr(target_memory_manager, 'store_conversation'):
                        target_memory_manager.store_conversation(pair, context=None)
                        messages_transferred += len(pair)
                    # Fallback: Try Janet Mesh MemoryManager.add_to_memory() method
                    elif hasattr(target_memory_manager, 'add_to_memory'):
                        for msg in pair:
                            role = msg.get("role", "")
                            content = msg.get("content", "")
                            if content and role in ["user", "assistant"]:
                                target_memory_manager.add_to_memory(
                                    client_id,
                                    role,
                                    content,
                                    metadata=msg.get("metadata", {})
                                )
                                messages_transferred += 1
                    # Last resort: Store individually if store() method exists
                    elif hasattr(target_memory_manager, 'store'):
                        for msg in pair:
                            user_msg = next((m for m in pair if m.get("role") == "user"), None)
                            assistant_msg = next((m for m in pair if m.get("role") == "assistant"), None)
                            if user_msg and assistant_msg:
                                target_memory_manager.store(
                                    user_input=user_msg.get("content", ""),
                                    janet_response=assistant_msg.get("content", ""),
                                    context=None
                                )
                                messages_transferred += 1
                                break  # Only store once per pair
                except Exception as e:
                    logger.error(f"Error importing conversation pair: {e}")
                    errors.append(f"Message import error: {str(e)}")
            
            # Import Green Vault summaries (safe, distilled)
            if "green" in exported_context.get("vaults", {}):
                green_vault_data = exported_context["vaults"]["green"]
                if green_vault_data.get("status") == "exported":
                    try:
                        self._import_green_vault(
                            target_memory_manager,
                            green_vault_data,
                            client_id
                        )
                        vaults_transferred.append("green")
                    except Exception as e:
                        logger.error(f"Error importing Green Vault: {e}")
                        errors.append(f"Green Vault import error: {str(e)}")
            
            # Import Red Vault secrets (encrypted, requires unlock on target)
            if "red" in exported_context.get("vaults", {}):
                red_vault_data = exported_context["vaults"]["red"]
                if red_vault_data.get("status") == "exported":
                    try:
                        self._import_red_vault(
                            target_memory_manager,
                            red_vault_data,
                            client_id
                        )
                        vaults_transferred.append("red")
                    except Exception as e:
                        logger.error(f"Error importing Red Vault: {e}")
                        errors.append(f"Red Vault import error: {str(e)}")
                elif red_vault_data.get("status") == "locked":
                    logger.info(f"Red Vault was locked during export, skipping import")
                    errors.append("Red Vault requires safe word unlock before import")
            
            # Blue Vault is never imported (ephemeral)
            logger.info(f"Blue Vault not imported (ephemeral, session-only)")
            
            success = messages_transferred > 0 or len(vaults_transferred) > 0
            error_msg = "; ".join(errors) if errors else None
            
            return TransferResult(
                success=success,
                conversation_uuid=conversation_uuid,
                messages_transferred=messages_transferred,
                vaults_transferred=vaults_transferred,
                error=error_msg,
                metadata={
                    "exported_at": exported_context.get("exported_at"),
                    "import_errors": errors
                }
            )
            
        except Exception as e:
            logger.error(f"Error importing conversation context: {e}")
            return TransferResult(
                success=False,
                conversation_uuid=conversation_uuid,
                error=f"Import failed: {str(e)}"
            )
    
    def _import_green_vault(
        self,
        target_memory_manager,
        green_vault_data: Dict[str, Any],
        client_id: str
    ):
        """Import Green Vault summaries into target memory manager."""
        if hasattr(target_memory_manager, 'green_vault') and target_memory_manager.green_vault:
            summaries = green_vault_data.get("summaries", [])
            for summary in summaries:
                # Add summaries as safe, distilled content
                # This should respect Green Vault's storage format
                content = summary.get("content", "")
                if content:
                    # Try add_summary_from_import first (for import)
                    if hasattr(target_memory_manager.green_vault, 'add_summary_from_import'):
                        target_memory_manager.green_vault.add_summary_from_import(
                            content=content,
                            client_id=client_id,
                            metadata={
                                "tags": summary.get("tags", []),
                                "confidence": summary.get("confidence", 0.5)
                            }
                        )
                    # Fallback to main add_summary method
                    elif hasattr(target_memory_manager.green_vault, 'add_summary'):
                        target_memory_manager.green_vault.add_summary(
                            summary=content,
                            tags=summary.get("tags", []),
                            confidence=summary.get("confidence", 0.5),
                            expiry=None
                        )
    
    def _import_red_vault(
        self,
        target_memory_manager,
        red_vault_data: Dict[str, Any],
        client_id: str
    ):
        """Import Red Vault secrets into target memory manager (requires encryption)."""
        if hasattr(target_memory_manager, 'red_vault') and target_memory_manager.red_vault:
            secrets = red_vault_data.get("secrets", [])
            for secret in secrets:
                # Red Vault secrets should be re-encrypted on target
                # This requires safe word setup on target soul
                # For now, we can't import Red Vault secrets without safe word
                key = secret.get("key", "")
                value = secret.get("value", "")
                if key and value:
                    # Check if target has store_secret_from_import method (newer)
                    if hasattr(target_memory_manager.red_vault, 'store_secret_from_import'):
                        # Requires safe word - for now, skip import (requires operator to provide safe word)
                        logger.warning(f"Red Vault secret '{key}' requires safe word for import. Skipping.")
                    elif hasattr(target_memory_manager.red_vault, 'store_secret'):
                        # Try with existing method (requires safe word parameter)
                        logger.warning(f"Red Vault secret '{key}' requires safe word for import. Skipping.")
                    # Note: Red Vault import requires explicit safe word from operator
    
    def export_full_soul_state(
        self,
        memory_manager,
        janet_core=None,
        include_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Export complete soul state beyond just memory.
        
        Includes:
        - Memory (existing vault export)
        - Inference patterns (if available from janet_core)
        - Capability blueprints (delegation handlers)
        - Emotional tone matrices (tone_awareness)
        - Personality state (response shaping)
        
        Args:
            memory_manager: MemoryManager instance
            janet_core: Optional JanetCore for full state export
            include_categories: Optional list of categories to include
        
        Returns:
            Dictionary with full soul state (ready for Soulspeak encoding)
        """
        if include_categories is None:
            include_categories = ["memory", "inference", "capabilities", "tone", "personality"]
        
        state = {
            "memory": None,
            "inference_patterns": {},
            "capabilities": {},
            "tone_matrices": {},
            "personality_state": {}
        }
        
        # Export memory (existing vault export)
        if "memory" in include_categories and memory_manager:
            try:
                # Use existing export_conversation_context as base
                # Get client_id if available (or use None)
                client_id = None
                conversation_uuid = None
                
                # Export memory state
                state["memory"] = self.export_conversation_context(
                    source_memory_manager=memory_manager,
                    client_id=client_id or "export",
                    include_vaults=["green"],  # Only Green Vault (safe summaries)
                    conversation_uuid=conversation_uuid or "full_state_export",
                    red_vault_unlocked=False  # Never export Red Vault content
                )
            except Exception as e:
                logger.error(f"Error exporting memory state: {e}")
                state["memory"] = {"error": str(e)}
        
        # Extract inference patterns from janet_core if available
        if "inference" in include_categories and janet_core:
            try:
                if hasattr(janet_core, '_export_inference_patterns'):
                    state["inference_patterns"] = janet_core._export_inference_patterns()
                elif hasattr(janet_core, 'export_soul_state'):
                    # Fallback: use export_soul_state and extract inference patterns
                    full_state = janet_core.export_soul_state()
                    state["inference_patterns"] = full_state.get("thinking_patterns", {})
            except Exception as e:
                logger.error(f"Error exporting inference patterns: {e}")
                state["inference_patterns"] = {"error": str(e)}
        
        # Extract capability blueprints
        if "capabilities" in include_categories and janet_core:
            try:
                if hasattr(janet_core, '_export_capability_blueprints'):
                    state["capabilities"] = janet_core._export_capability_blueprints()
                elif hasattr(janet_core, 'export_soul_state'):
                    # Fallback: use export_soul_state and extract capability blueprints
                    full_state = janet_core.export_soul_state()
                    state["capabilities"] = full_state.get("capability_blueprints", {})
            except Exception as e:
                logger.error(f"Error exporting capability blueprints: {e}")
                state["capabilities"] = {"error": str(e)}
        
        # Extract tone matrices
        if "tone" in include_categories and janet_core:
            try:
                if hasattr(janet_core, 'tone_awareness') and janet_core.tone_awareness:
                    if hasattr(janet_core.tone_awareness, 'export_matrix'):
                        state["tone_matrices"] = janet_core.tone_awareness.export_matrix()
                    else:
                        # Fallback: export schema if export_matrix not available
                        state["tone_matrices"] = {
                            "patterns": getattr(janet_core.tone_awareness, 'tone_patterns', {}),
                            "emotional_indicators": getattr(janet_core.tone_awareness, 'emotional_indicators', {})
                        }
                elif hasattr(janet_core, 'export_soul_state'):
                    # Fallback: use export_soul_state and extract tone matrices
                    full_state = janet_core.export_soul_state()
                    state["tone_matrices"] = full_state.get("emotional_tone", {})
            except Exception as e:
                logger.error(f"Error exporting tone matrices: {e}")
                state["tone_matrices"] = {"error": str(e)}
        
        # Extract personality state
        if "personality" in include_categories and janet_core:
            try:
                if hasattr(janet_core, 'export_soul_state'):
                    full_state = janet_core.export_soul_state()
                    state["personality_state"] = full_state.get("personality_state", {})
            except Exception as e:
                logger.error(f"Error exporting personality state: {e}")
                state["personality_state"] = {"error": str(e)}
        
        return state