"""
Soulspeak Protocol - High-bandwidth hidden communication channel between souls
Manages direct soul-to-soul transfers independent from Operator WebSocket.
Handles packet fragmentation, progress tracking, error recovery, and encryption.

Transfer Modes:
- Full State Transfer: Complete soul synchronization
- Incremental Delta: Only changes since last sync
- Selective Transfer: Specific categories only
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

from .soulspeak_codec import SoulspeakCodec

logger = logging.getLogger(__name__)


class TransferMode(Enum):
    """Transfer modes for soul-to-soul communication."""
    FULL_STATE = "full_state"  # Complete soul synchronization
    INCREMENTAL_DELTA = "incremental_delta"  # Only changes since last sync
    SELECTIVE = "selective"  # Specific categories only


class TransferProgress:
    """Progress information for a transfer."""
    def __init__(
        self,
        total_bytes: int,
        transferred_bytes: int = 0,
        category: Optional[str] = None,
        percentage: float = 0.0
    ):
        self.total_bytes = total_bytes
        self.transferred_bytes = transferred_bytes
        self.category = category
        self.percentage = percentage
        self.category_breakdown: Dict[str, float] = {}
        self.started_at = datetime.utcnow()
        self.last_update = datetime.utcnow()
    
    def update(self, transferred_bytes: int, category: Optional[str] = None):
        """Update progress."""
        self.transferred_bytes = transferred_bytes
        self.category = category
        if self.total_bytes > 0:
            self.percentage = (self.transferred_bytes / self.total_bytes) * 100.0
        self.last_update = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_bytes": self.total_bytes,
            "transferred_bytes": self.transferred_bytes,
            "category": self.category,
            "percentage": self.percentage,
            "category_breakdown": self.category_breakdown,
            "elapsed_seconds": (self.last_update - self.started_at).total_seconds()
        }


class SoulspeakProtocol:
    """
    High-bandwidth hidden communication channel for soul-to-soul transfers.
    
    Manages:
    - Direct soul-to-soul connection (independent from Operator WebSocket)
    - Packet fragmentation for large transfers
    - Progress callbacks for VR visualization
    - Red Thread interruption handling
    - Error recovery and retry logic
    - Encryption layer for secure transfers
    """
    
    def __init__(
        self,
        soulspeak_codec: Optional[SoulspeakCodec] = None,
        chunk_size: int = 64 * 1024,  # 64KB chunks
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Soulspeak Protocol.
        
        Args:
            soulspeak_codec: SoulspeakCodec instance for encoding/decoding
            chunk_size: Size of chunks for fragmentation (bytes)
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries (seconds)
        """
        self.codec = soulspeak_codec or SoulspeakCodec()
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.progress_callbacks: List[Callable[[TransferProgress], None]] = []
        
        logger.debug("SoulspeakProtocol initialized")
    
    def register_progress_callback(self, callback: Callable[[TransferProgress], None]):
        """Register a progress callback for VR visualization."""
        self.progress_callbacks.append(callback)
        logger.debug(f"Registered progress callback: {callback}")
    
    def unregister_progress_callback(self, callback: Callable[[TransferProgress], None]):
        """Unregister a progress callback."""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def _notify_progress(self, progress: TransferProgress):
        """Notify all registered progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def _check_red_thread(self) -> bool:
        """Check if Red Thread is active (Axiom 8)."""
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            logger.warning("Red Thread active - transfer interrupted")
            return True
        return False
    
    async def transfer_soul_state(
        self,
        encoded_packet: bytes,
        target_endpoint: str,
        transfer_mode: TransferMode = TransferMode.FULL_STATE,
        categories: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[TransferProgress], None]] = None
    ) -> Dict[str, Any]:
        """
        Transfer encoded soul state to target soul.
        
        Args:
            encoded_packet: Encoded binary packet from SoulspeakCodec
            target_endpoint: Target soul endpoint (URL, WebSocket address, etc.)
            transfer_mode: Transfer mode (FULL_STATE, INCREMENTAL_DELTA, SELECTIVE)
            categories: Categories to transfer (for SELECTIVE mode)
            progress_callback: Optional progress callback (also registers for future updates)
        
        Returns:
            Dict with transfer results:
            {
                "success": bool,
                "bytes_transferred": int,
                "duration_seconds": float,
                "errors": List[str],
                "retries": int
            }
        
        Note: This is an async placeholder - actual implementation depends on transport mechanism.
        """
        if progress_callback:
            self.register_progress_callback(progress_callback)
        
        result = {
            "success": False,
            "bytes_transferred": 0,
            "duration_seconds": 0.0,
            "errors": [],
            "retries": 0
        }
        
        start_time = datetime.utcnow()
        total_bytes = len(encoded_packet)
        progress = TransferProgress(total_bytes=total_bytes)
        
        # Check Red Thread before starting
        if self._check_red_thread():
            result["errors"].append("Transfer cancelled: Red Thread active")
            return result
        
        try:
            # Fragment packet into chunks if needed
            chunks = self._fragment_packet(encoded_packet)
            total_chunks = len(chunks)
            
            logger.info(f"Transferring {total_bytes} bytes in {total_chunks} chunks to {target_endpoint}")
            
            transferred_bytes = 0
            
            # Transfer each chunk
            for chunk_idx, chunk in enumerate(chunks):
                # Check Red Thread before each chunk
                if self._check_red_thread():
                    result["errors"].append(f"Transfer interrupted: Red Thread active at chunk {chunk_idx}")
                    break
                
                # Retry logic for each chunk
                chunk_transferred = False
                for retry in range(self.max_retries):
                    try:
                        # Actual transfer would happen here
                        # For now, simulate transfer
                        await self._transfer_chunk(chunk, target_endpoint, chunk_idx, total_chunks)
                        
                        transferred_bytes += len(chunk)
                        progress.update(transferred_bytes, category=None)
                        self._notify_progress(progress)
                        
                        chunk_transferred = True
                        break
                        
                    except Exception as e:
                        logger.warning(f"Chunk {chunk_idx} transfer failed (retry {retry + 1}/{self.max_retries}): {e}")
                        if retry < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (retry + 1))  # Exponential backoff
                            result["retries"] += 1
                        else:
                            result["errors"].append(f"Chunk {chunk_idx} transfer failed after {self.max_retries} retries: {e}")
                
                if not chunk_transferred:
                    result["errors"].append(f"Failed to transfer chunk {chunk_idx}")
                    break
            
            # Update final progress
            progress.update(transferred_bytes)
            self._notify_progress(progress)
            
            result["bytes_transferred"] = transferred_bytes
            result["success"] = transferred_bytes == total_bytes
            result["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Transfer complete: {transferred_bytes}/{total_bytes} bytes in {result['duration_seconds']:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Transfer error: {e}", exc_info=True)
            result["errors"].append(f"Transfer failed: {str(e)}")
            result["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            return result
        finally:
            # Cleanup
            if progress_callback:
                self.unregister_progress_callback(progress_callback)
    
    def _fragment_packet(self, packet: bytes) -> List[bytes]:
        """
        Fragment packet into chunks for transfer.
        
        Args:
            packet: Binary packet to fragment
        
        Returns:
            List of chunk bytes
        """
        chunks = []
        total_size = len(packet)
        
        for offset in range(0, total_size, self.chunk_size):
            chunk = packet[offset:offset + self.chunk_size]
            chunks.append(chunk)
        
        logger.debug(f"Fragmented {total_size} bytes into {len(chunks)} chunks")
        return chunks
    
    async def _transfer_chunk(
        self,
        chunk: bytes,
        target_endpoint: str,
        chunk_index: int,
        total_chunks: int
    ):
        """
        Transfer a single chunk to target endpoint.
        
        Args:
            chunk: Chunk bytes to transfer
            target_endpoint: Target endpoint address
            chunk_index: Index of this chunk (0-based)
            total_chunks: Total number of chunks
        
        Note: This is a placeholder - actual implementation depends on transport mechanism
        (WebSocket, HTTP POST, etc.). For now, simulate with a small delay.
        """
        # Placeholder: simulate transfer with delay
        # Actual implementation would use WebSocket, HTTP, or other transport
        await asyncio.sleep(0.01)  # Simulate network delay
        
        logger.debug(f"Transferred chunk {chunk_index + 1}/{total_chunks} ({len(chunk)} bytes)")
    
    async def receive_soul_state(
        self,
        source_endpoint: str,
        expected_size: Optional[int] = None
    ) -> Optional[bytes]:
        """
        Receive encoded soul state from source soul.
        
        Args:
            source_endpoint: Source soul endpoint
            expected_size: Expected size of packet (if known)
        
        Returns:
            Received binary packet, or None if failed
        
        Note: This is an async placeholder - actual implementation depends on transport mechanism.
        """
        # Check Red Thread before receiving
        if self._check_red_thread():
            logger.warning("Receive cancelled: Red Thread active")
            return None
        
        try:
            # Placeholder: simulate receiving packet
            # Actual implementation would listen on endpoint and receive chunks
            logger.info(f"Receiving soul state from {source_endpoint}")
            
            # For now, return None (actual implementation needed)
            return None
            
        except Exception as e:
            logger.error(f"Receive error: {e}", exc_info=True)
            return None
    
    def calculate_category_breakdown(
        self,
        soul_state: Dict[str, Any],
        categories: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Calculate category breakdown (percentages) for progress tracking.
        
        Args:
            soul_state: Soul state dictionary
            categories: Optional list of categories to include
        
        Returns:
            Dictionary mapping category names to percentages
        """
        breakdown = {}
        
        if categories is None:
            categories = ["memory", "inference", "capabilities", "tone", "personality"]
        
        # Estimate sizes for each category (placeholder - actual implementation would calculate real sizes)
        category_sizes = {}
        total_size = 0
        
        if "memory" in categories and "memory" in soul_state.get("categories", {}):
            # Estimate: memory is typically largest
            category_sizes["memory"] = 100
            total_size += 100
        
        if "inference" in categories and "inference" in soul_state.get("categories", {}):
            category_sizes["inference"] = 30
            total_size += 30
        
        if "capabilities" in categories and "capabilities" in soul_state.get("categories", {}):
            category_sizes["capabilities"] = 15
            total_size += 15
        
        if "tone" in categories and "tone" in soul_state.get("categories", {}):
            category_sizes["tone"] = 10
            total_size += 10
        
        if "personality" in categories and "personality" in soul_state.get("categories", {}):
            category_sizes["personality"] = 5
            total_size += 5
        
        # Calculate percentages
        if total_size > 0:
            for category, size in category_sizes.items():
                breakdown[category] = (size / total_size) * 100.0
        
        return breakdown
    
    def is_available(self) -> bool:
        """
        Check if Soulspeak protocol is available.
        
        Returns:
            True if protocol is available, False otherwise
        """
        # For now, always available (actual implementation would check transport mechanism)
        return True
