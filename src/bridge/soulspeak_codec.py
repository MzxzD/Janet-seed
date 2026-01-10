"""
Soulspeak Codec - Custom binary codec for dense, lossless knowledge transfer between souls
Encodes/decodes model weight deltas, inference shortcuts, capability blueprints,
emotional tone matrices, and full soul state in a dense binary format.

Privacy Boundaries (CRITICAL):
- Red Vault: Include ONLY metadata (count, presence indicators) - NEVER content
- Blue Vault: Never include (ephemeral, session-only per Axiom 9)
- Green Vault: Full transfer allowed (safe summaries)
- Secrets: Acknowledge existence only
"""
import struct
import zlib
import json
import hashlib
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Binary format constants
SOULSPK_MAGIC = b"SOULSPK"  # 7 bytes
SOULSPK_VERSION = 1  # uint8
SOULSPK_HEADER_SIZE = 16  # Total header size

# Format flags
FLAG_COMPRESSED = 0x01  # Payload is compressed
FLAG_ENCRYPTED = 0x02  # Payload is encrypted (for future use)
FLAG_DELTA = 0x04  # Payload is delta-encoded (only changes)


class SoulspeakCodec:
    """
    Binary codec for dense soul state transfer.
    
    Formats:
    [Header: 16 bytes]
      - Magic: "SOULSPK" (7 bytes)
      - Version: uint8 (1)
      - Flags: uint8 (compression, encryption, delta flags)
      - Checksum: uint32 (CRC32 of payload)
      - Reserved: 4 bytes
    
    [Compressed Payload: variable]
      JSON structure containing:
      - Memory: Green Vault summaries (safe)
      - Inference: Learned patterns and shortcuts
      - Capabilities: Handler blueprints (structure, not secrets)
      - Tone: Tone awareness matrices
      - Personality: Personality state
      - Model-Delta: Model weight deltas (if available)
    """
    
    def __init__(self):
        """Initialize Soulspeak Codec."""
        self.version = SOULSPK_VERSION
        logger.debug("SoulspeakCodec initialized")
    
    def encode_soul_state(
        self,
        memory_manager,
        janet_core=None,
        conversation_uuid: Optional[str] = None,
        include_categories: Optional[List[str]] = None
    ) -> bytes:
        """
        Encode full soul state into dense binary format.
        
        Args:
            memory_manager: MemoryManager instance
            janet_core: Optional JanetCore for full state export
            conversation_uuid: Optional conversation UUID for tracking
            include_categories: List of categories to include
                               ["memory", "inference", "capabilities", "tone", "personality"]
        
        Returns:
            bytes: Compressed binary packet containing soul state
        """
        if include_categories is None:
            include_categories = ["memory", "inference", "capabilities", "tone"]
        
        logger.info(f"Encoding soul state with categories: {include_categories}")
        
        # Build soul state dictionary
        soul_state = {
            "version": self.version,
            "conversation_uuid": conversation_uuid,
            "encoded_at": datetime.utcnow().isoformat(),
            "categories": {}
        }
        
        # Extract memory state (with privacy boundaries)
        if "memory" in include_categories and memory_manager:
            soul_state["categories"]["memory"] = self._encode_memory(
                memory_manager,
                conversation_uuid
            )
        
        # Extract inference patterns
        if "inference" in include_categories and janet_core:
            soul_state["categories"]["inference"] = self._encode_inference_patterns(janet_core)
        
        # Extract capability blueprints
        if "capabilities" in include_categories and janet_core:
            soul_state["categories"]["capabilities"] = self._encode_capability_blueprints(janet_core)
        
        # Extract tone matrices
        if "tone" in include_categories and janet_core:
            soul_state["categories"]["tone"] = self._encode_tone_matrices(janet_core)
        
        # Extract personality state
        if "personality" in include_categories and janet_core:
            soul_state["categories"]["personality"] = self._encode_personality_state(janet_core)
        
        # Extract model weight deltas (if available - note: Ollama weights not directly accessible)
        # This is a placeholder for future implementation with local models
        if "model_delta" in include_categories and janet_core:
            soul_state["categories"]["model_delta"] = self._encode_model_deltas(janet_core)
        
        # Convert to JSON (for cross-platform compatibility)
        json_payload = json.dumps(soul_state, default=str).encode('utf-8')
        
        # Compress payload
        compressed_payload = zlib.compress(json_payload, level=9)
        
        # Calculate checksum
        checksum = zlib.crc32(compressed_payload) & 0xffffffff  # Ensure unsigned 32-bit
        
        # Build header
        flags = FLAG_COMPRESSED  # Always compressed for now
        header = self._build_header(flags, checksum)
        
        # Combine header + payload
        encoded_packet = header + compressed_payload
        
        logger.info(f"Encoded soul state: {len(encoded_packet)} bytes "
                   f"({len(json_payload)} original, {len(compressed_payload)} compressed)")
        
        return encoded_packet
    
    def decode_and_merge(
        self,
        encoded_packet: bytes,
        target_memory_manager,
        target_janet_core=None,
        merge_strategy: str = "merge"
    ) -> Dict[str, Any]:
        """
        Decode binary packet and merge into target soul.
        
        Args:
            encoded_packet: Binary packet from encode_soul_state
            target_memory_manager: Target MemoryManager instance
            target_janet_core: Optional target JanetCore instance
            merge_strategy: "merge" or "overwrite"
        
        Returns:
            Dict with merge results and conflict reports:
            {
                "success": bool,
                "categories_merged": List[str],
                "conflicts": List[Conflict],
                "bytes_decoded": int,
                "errors": List[str]
            }
        """
        result = {
            "success": False,
            "categories_merged": [],
            "conflicts": [],
            "bytes_decoded": len(encoded_packet),
            "errors": []
        }
        
        try:
            # Parse header
            if len(encoded_packet) < SOULSPK_HEADER_SIZE:
                result["errors"].append("Packet too short for header")
                return result
            
            header_data = self._parse_header(encoded_packet[:SOULSPK_HEADER_SIZE])
            if not header_data:
                result["errors"].append("Invalid header")
                return result
            
            flags, checksum = header_data
            payload = encoded_packet[SOULSPK_HEADER_SIZE:]
            
            # Verify checksum
            payload_checksum = zlib.crc32(payload) & 0xffffffff
            if payload_checksum != checksum:
                result["errors"].append(f"Checksum mismatch: expected {checksum}, got {payload_checksum}")
                logger.error(f"Checksum verification failed: expected {checksum}, got {payload_checksum}")
                return result
            
            # Decompress payload if compressed
            if flags & FLAG_COMPRESSED:
                try:
                    payload = zlib.decompress(payload)
                except zlib.error as e:
                    result["errors"].append(f"Decompression failed: {e}")
                    return result
            
            # Decode JSON payload
            try:
                soul_state = json.loads(payload.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                result["errors"].append(f"JSON decode failed: {e}")
                return result
            
            # Merge each category
            categories = soul_state.get("categories", {})
            
            # Merge memory
            if "memory" in categories and target_memory_manager:
                try:
                    self._merge_memory(categories["memory"], target_memory_manager, merge_strategy)
                    result["categories_merged"].append("memory")
                except Exception as e:
                    result["errors"].append(f"Memory merge failed: {e}")
                    logger.error(f"Memory merge error: {e}")
            
            # Merge inference patterns
            if "inference" in categories and target_janet_core:
                try:
                    self._merge_inference_patterns(categories["inference"], target_janet_core, merge_strategy)
                    result["categories_merged"].append("inference")
                except Exception as e:
                    result["errors"].append(f"Inference merge failed: {e}")
                    logger.error(f"Inference merge error: {e}")
            
            # Merge capability blueprints
            if "capabilities" in categories and target_janet_core:
                try:
                    self._merge_capability_blueprints(categories["capabilities"], target_janet_core, merge_strategy)
                    result["categories_merged"].append("capabilities")
                except Exception as e:
                    result["errors"].append(f"Capability merge failed: {e}")
                    logger.error(f"Capability merge error: {e}")
            
            # Merge tone matrices
            if "tone" in categories and target_janet_core:
                try:
                    self._merge_tone_matrices(categories["tone"], target_janet_core, merge_strategy)
                    result["categories_merged"].append("tone")
                except Exception as e:
                    result["errors"].append(f"Tone merge failed: {e}")
                    logger.error(f"Tone merge error: {e}")
            
            # Merge personality state
            if "personality" in categories and target_janet_core:
                try:
                    self._merge_personality_state(categories["personality"], target_janet_core, merge_strategy)
                    result["categories_merged"].append("personality")
                except Exception as e:
                    result["errors"].append(f"Personality merge failed: {e}")
                    logger.error(f"Personality merge error: {e}")
            
            result["success"] = len(result["categories_merged"]) > 0
            
            logger.info(f"Decoded and merged soul state: {len(result['categories_merged'])} categories, "
                       f"{len(result['errors'])} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"Error decoding soul state: {e}", exc_info=True)
            result["errors"].append(f"Decode error: {str(e)}")
            return result
    
    def _build_header(self, flags: int, checksum: int) -> bytes:
        """Build binary header for encoded packet."""
        # Format: magic (7 bytes) + version (1 byte) + flags (1 byte) + checksum (4 bytes) + reserved (3 bytes) = 16 bytes
        header = struct.pack(
            "7sBBL",  # 7s = 7-byte string, B = uint8, B = uint8, L = uint32 (checksum) = 13 bytes
            SOULSPK_MAGIC,
            SOULSPK_VERSION,
            flags,
            checksum & 0xffffffff  # Ensure unsigned 32-bit
        )
        # Add 3 padding bytes to reach 16 bytes total
        header += b'\x00' * 3
        return header
    
    def _parse_header(self, header_bytes: bytes) -> Optional[tuple]:
        """Parse binary header and return (flags, checksum) or None if invalid."""
        try:
            if len(header_bytes) < SOULSPK_HEADER_SIZE:
                return None
            
            # Unpack first 13 bytes: magic (7) + version (1) + flags (1) + checksum (4)
            magic, version, flags, checksum = struct.unpack(
                "7sBBL",
                header_bytes[:13]
            )
            # Remaining 3 bytes are reserved/padding, ignore them
            
            if magic != SOULSPK_MAGIC:
                logger.error(f"Invalid magic: {magic}")
                return None
            
            if version != SOULSPK_VERSION:
                logger.warning(f"Version mismatch: expected {SOULSPK_VERSION}, got {version}")
                # Continue anyway for forward compatibility
            
            return (flags, checksum)
            
        except struct.error as e:
            logger.error(f"Header parse error: {e}")
            return None
    
    def _encode_memory(self, memory_manager, conversation_uuid: Optional[str]) -> Dict[str, Any]:
        """Encode memory state with privacy boundaries."""
        memory_state = {
            "green_vault": {},
            "red_vault": {"status": "metadata_only"},  # Privacy: only metadata
            "blue_vault": {"status": "not_transferred"}  # Never transferred (Axiom 9)
        }
        
        # Export Green Vault (safe summaries)
        if hasattr(memory_manager, 'green_vault') and memory_manager.green_vault:
            try:
                # Get recent summaries (limit to avoid huge payloads)
                if hasattr(memory_manager.green_vault, 'get_recent_summaries'):
                    summaries = memory_manager.green_vault.get_recent_summaries(limit=100)
                    memory_state["green_vault"] = {
                        "summaries": summaries[:100],  # Limit to 100
                        "count": len(summaries)
                    }
                else:
                    memory_state["green_vault"] = {"summaries": [], "count": 0}
            except Exception as e:
                logger.error(f"Error encoding Green Vault: {e}")
                memory_state["green_vault"] = {"error": str(e)}
        
        # Red Vault: ONLY metadata (CRITICAL - never content)
        if hasattr(memory_manager, 'red_vault') and memory_manager.red_vault:
            try:
                # Only get count and presence - NEVER content
                if hasattr(memory_manager.red_vault, 'list_secrets'):
                    secret_keys = memory_manager.red_vault.list_secrets()
                    memory_state["red_vault"] = {
                        "status": "metadata_only",
                        "count": len(secret_keys) if secret_keys else 0,
                        "presence": len(secret_keys) > 0 if secret_keys else False,
                        "note": "Content never transferred - only presence metadata"
                    }
                else:
                    memory_state["red_vault"] = {
                        "status": "metadata_only",
                        "count": 0,
                        "presence": False
                    }
            except Exception as e:
                logger.error(f"Error encoding Red Vault metadata: {e}")
                memory_state["red_vault"] = {"status": "error", "error": str(e)}
        
        return memory_state
    
    def _encode_inference_patterns(self, janet_core) -> Dict[str, Any]:
        """Encode inference patterns (learned shortcuts)."""
        patterns = {}
        
        # Extract from janet_brain if available
        if hasattr(janet_core, 'janet_brain') and janet_core.janet_brain:
            # Placeholder - actual implementation depends on how patterns are stored
            # This would extract learned patterns like "useless" → Konosuba reference with confidence
            patterns["learned_shortcuts"] = {}
            patterns["reasoning_chains"] = []
        
        # Extract from memory_manager learning_manager if available
        if hasattr(janet_core, 'memory_manager') and janet_core.memory_manager:
            if hasattr(janet_core.memory_manager, 'learning_manager') and janet_core.memory_manager.learning_manager:
                # Export learned patterns from learning manager
                patterns["learning_patterns"] = {}
        
        return patterns
    
    def _encode_capability_blueprints(self, janet_core) -> Dict[str, Any]:
        """Encode capability blueprints (handler structures, NOT secrets)."""
        blueprints = {}
        
        if hasattr(janet_core, 'delegation_manager') and janet_core.delegation_manager:
            delegation_manager = janet_core.delegation_manager
            if hasattr(delegation_manager, 'handlers'):
                for handler_id, handler in delegation_manager.handlers.items():
                    # Export structure only - NO secrets, API keys, or sensitive data
                    blueprint = {
                        "handler_id": handler_id,
                        "name": getattr(handler, 'name', ''),
                        "capabilities": [c.value for c in handler.get_capabilities()] if hasattr(handler, 'get_capabilities') else [],
                        "requires_confirmation": getattr(handler, 'requires_confirmation', False),
                        "description": getattr(handler, 'description', ''),
                        # Explicitly exclude: API keys, tokens, secrets, credentials
                    }
                    blueprints[handler_id] = blueprint
        
        return blueprints
    
    def _encode_tone_matrices(self, janet_core) -> Dict[str, Any]:
        """Encode tone awareness matrices."""
        tone_data = {}
        
        if hasattr(janet_core, 'tone_awareness') and janet_core.tone_awareness:
            tone_awareness = janet_core.tone_awareness
            # Export tone patterns and response styles
            if hasattr(tone_awareness, 'schema'):
                tone_data["patterns"] = tone_awareness.schema.get("patterns", {}) if hasattr(tone_awareness.schema, 'get') else {}
                tone_data["emotional_indicators"] = tone_awareness.schema.get("emotional_indicators", {}) if hasattr(tone_awareness.schema, 'get') else {}
        
        return tone_data
    
    def _encode_personality_state(self, janet_core) -> Dict[str, Any]:
        """Encode personality state (response shaping)."""
        personality = {}
        
        if hasattr(janet_core, 'constitution'):
            constitution = janet_core.constitution
            # Export preferences and personality traits (NOT secrets)
            if hasattr(constitution, 'raw_data'):
                raw_data = constitution.raw_data
                personality["preferences"] = raw_data.get("preferences", {}) if isinstance(raw_data, dict) else {}
                personality["voice_style"] = raw_data.get("preferences", {}).get("voice_style", "") if isinstance(raw_data, dict) else ""
        
        return personality
    
    def _encode_model_deltas(self, janet_core) -> Dict[str, Any]:
        """Encode model weight deltas (if available - Ollama weights not directly accessible)."""
        # Placeholder for future implementation with local models
        # Note: Ollama models store weights separately and are not directly accessible
        return {
            "status": "not_available",
            "note": "Model weight deltas not available with Ollama models"
        }
    
    def _merge_memory(self, memory_data: Dict[str, Any], target_memory_manager, merge_strategy: str):
        """Merge memory data into target memory manager."""
        # Merge Green Vault summaries
        if "green_vault" in memory_data and hasattr(target_memory_manager, 'green_vault'):
            green_data = memory_data["green_vault"]
            summaries = green_data.get("summaries", [])
            for summary in summaries:
                try:
                    if hasattr(target_memory_manager.green_vault, 'add_summary'):
                        target_memory_manager.green_vault.add_summary(
                            summary=summary.get("content", ""),
                            tags=summary.get("tags", []),
                            confidence=summary.get("confidence", 0.5),
                            expiry=None
                        )
                except Exception as e:
                    logger.error(f"Error merging Green Vault summary: {e}")
        
        # Red Vault: Do not merge (secrets remain on source only)
        # Metadata already acknowledged in encoded state
    
    def _merge_inference_patterns(self, inference_data: Dict[str, Any], target_janet_core, merge_strategy: str):
        """Merge inference patterns into target soul."""
        # Placeholder - actual implementation depends on how patterns are stored
        # This would merge learned shortcuts and reasoning chains
        pass
    
    def _merge_capability_blueprints(self, capabilities_data: Dict[str, Any], target_janet_core, merge_strategy: str):
        """Merge capability blueprints into target soul."""
        # Placeholder - actual implementation would merge handler structures
        # Note: This is informational only - handlers are not automatically installed
        pass
    
    def _merge_tone_matrices(self, tone_data: Dict[str, Any], target_janet_core, merge_strategy: str):
        """Merge tone matrices into target soul."""
        if hasattr(target_janet_core, 'tone_awareness') and target_janet_core.tone_awareness:
            # Merge tone patterns if merge strategy allows
            if merge_strategy == "merge" and "patterns" in tone_data:
                # Would merge patterns into tone_awareness schema
                pass
    
    def _merge_personality_state(self, personality_data: Dict[str, Any], target_janet_core, merge_strategy: str):
        """Merge personality state into target soul (carefully - preserve core nature)."""
        # Personality merging must be careful - preserve core nature
        # Only merge non-core preferences, not fundamental traits
        if merge_strategy == "merge":
            # Would carefully merge preferences while preserving core personality
            pass
