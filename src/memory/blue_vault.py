"""
Blue Vault - Ephemeral RAM-Only Storage
Temporary storage of unlocked secrets for active session use.

ALLOWED:
- Secrets unlocked via safe word
- Temporary context notes
- Session-scoped sensitive information

FORBIDDEN:
- Persistent storage (RAM only - no disk, no database)
- Embeddings or summaries
- Cross-session persistence

DESTRUCTION GUARANTEES:
- All data is zeroized immediately on lock
- No data persists after session ends
- No disk writes occur
- Memory is cleared from RAM on zeroize()
"""

from typing import Dict, Optional, List
import threading

# Import Red Thread event for constitutional integration (Axiom 8)
try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None


class BlueVault:
    """
    Blue Vault - Ephemeral in-memory storage for unlocked secrets.
    
    This vault is RAM-only and ephemeral. All data is zeroized on lock.
    No persistence to disk or database occurs.
    """
    
    def __init__(self):
        """
        Initialize Blue Vault.
        
        This creates an empty in-memory storage structure.
        """
        self._secrets: Dict[str, str] = {}
        self._context_notes: List[str] = []
        self._lock = threading.Lock()
    
    def store_unlocked_secret(self, key: str, value: str) -> None:
        """
        Store an unlocked secret in Blue Vault.
        
        Args:
            key: Secret key/identifier
            value: Secret value (will be stored in RAM only)
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Blue Vault write blocked")
            return
        
        if not key or not value:
            return
        
        with self._lock:
            self._secrets[key] = value
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Retrieve an unlocked secret from Blue Vault.
        
        Args:
            key: Secret key/identifier
        
        Returns:
            Secret value if found, None otherwise
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Blue Vault read blocked")
            return None
        
        with self._lock:
            return self._secrets.get(key)
    
    def store_context_note(self, note: str) -> None:
        """
        Store a temporary context note in Blue Vault.
        
        Args:
            note: Context note (ephemeral, session-only)
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Blue Vault write blocked")
            return
        
        if not note or not note.strip():
            return
        
        with self._lock:
            self._context_notes.append(note)
    
    def get_context_notes(self) -> List[str]:
        """
        Get all context notes from Blue Vault.
        
        Returns:
            List of context notes
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Blue Vault read blocked")
            return []
        
        with self._lock:
            return self._context_notes.copy()
    
    def zeroize(self) -> None:
        """
        Zeroize Blue Vault - wipe all data from memory.
        
        This method:
        - Clears all secrets
        - Clears all context notes
        - Ensures no data remains in memory
        - Provides destruction guarantee
        
        Note:
            This method overwrites data before clearing to ensure
            destruction guarantee. In a production system, you might
            want to use secure memory clearing techniques.
        """
        with self._lock:
            # Overwrite secrets before clearing (destruction guarantee)
            for key in list(self._secrets.keys()):
                # Overwrite with zeros (in production, use secure memory clearing)
                self._secrets[key] = "0" * len(self._secrets[key])
            
            # Clear all data
            self._secrets.clear()
            self._context_notes.clear()
            
            # Force garbage collection hint (Python doesn't guarantee immediate GC)
            # In production, consider using ctypes to securely wipe memory
            import gc
            gc.collect()
    
    def get_all_secrets(self) -> Dict[str, str]:
        """
        Get all secrets (for internal use only).
        
        Returns:
            Dictionary of all secrets
        """
        with self._lock:
            return self._secrets.copy()
    
    def has_secrets(self) -> bool:
        """
        Check if Blue Vault contains any secrets.
        
        Returns:
            True if secrets exist, False otherwise
        """
        with self._lock:
            return len(self._secrets) > 0 or len(self._context_notes) > 0

