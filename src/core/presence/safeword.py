"""
SafeWord Controller - Controls access to secrets via safe word unlock/lock.

The safe word controls access to secrets stored in Red Vault and Blue Vault.
When unlocked, secrets are loaded into Blue Vault for session use.
When locked, Blue Vault is immediately zeroized.
"""

import threading
from typing import Dict, Optional
from enum import Enum
from datetime import datetime, timedelta


class LockState(Enum):
    """SafeWord lock states."""
    LOCKED = "locked"
    UNLOCKED = "unlocked"


class SafeWordController:
    """
    SafeWord Controller - Manages safe word unlock/lock for secret access.
    
    Two states:
    - LOCKED: Blue Vault is empty, secrets are encrypted in Red Vault
    - UNLOCKED: Secrets are loaded into Blue Vault for session use
    
    Security:
    - Safe word is never stored
    - Safe word is never logged
    - Auto-lock after timeout
    - Immediate zeroization on lock
    """
    
    def __init__(self, auto_lock_timeout: int = 3600):
        """
        Initialize SafeWord Controller.
        
        Args:
            auto_lock_timeout: Auto-lock timeout in seconds (default: 1 hour)
        """
        self.state = LockState.LOCKED
        self.auto_lock_timeout = auto_lock_timeout
        self.unlock_time = None
        self._lock = threading.Lock()
        self._auto_lock_timer = None
    
    def unlock(self, safe_word: str, blue_vault) -> bool:
        """
        Unlock safe word - loads secrets into Blue Vault for session.
        
        Args:
            safe_word: Safe word for unlocking
            blue_vault: Blue Vault instance to load secrets into
        
        Returns:
            True if unlocked successfully, False otherwise
        
        Note:
            This method should:
            1. Verify safe word (in future, check against Red Vault)
            2. Load secrets from Red Vault into Blue Vault
            3. Set state to UNLOCKED
            4. Start auto-lock timer
        """
        with self._lock:
            if self.state == LockState.UNLOCKED:
                return True  # Already unlocked
            
            # For now, accept any non-empty safe word
            # In full implementation, verify against Red Vault
            if not safe_word or not safe_word.strip():
                return False
            
            # Set state to unlocked
            self.state = LockState.UNLOCKED
            self.unlock_time = datetime.utcnow()
            
            # Start auto-lock timer
            self._start_auto_lock_timer(blue_vault)
            
            return True
    
    def lock(self, blue_vault) -> None:
        """
        Lock safe word - zeroizes Blue Vault immediately.
        
        Args:
            blue_vault: Blue Vault instance to zeroize
        """
        with self._lock:
            if self.state == LockState.LOCKED:
                return  # Already locked
            
            # Zeroize Blue Vault
            if blue_vault:
                blue_vault.zeroize()
            
            # Set state to locked
            self.state = LockState.LOCKED
            self.unlock_time = None
            
            # Cancel auto-lock timer
            self._cancel_auto_lock_timer()
    
    def auto_lock_after(self, timeout: int, blue_vault) -> None:
        """
        Set auto-lock timeout.
        
        Args:
            timeout: Timeout in seconds
            blue_vault: Blue Vault instance to zeroize on timeout
        """
        self.auto_lock_timeout = timeout
        if self.state == LockState.UNLOCKED:
            self._start_auto_lock_timer(blue_vault)
    
    def get_status(self) -> Dict:
        """
        Get current lock status.
        
        Returns:
            Dictionary with:
                - state: "locked" or "unlocked"
                - unlocked_since: Timestamp if unlocked, None if locked
                - auto_lock_timeout: Timeout in seconds
        """
        with self._lock:
            status = {
                "state": self.state.value,
                "unlocked_since": self.unlock_time.isoformat() + "Z" if self.unlock_time else None,
                "auto_lock_timeout": self.auto_lock_timeout
            }
            
            if self.state == LockState.UNLOCKED and self.unlock_time:
                elapsed = (datetime.utcnow() - self.unlock_time).total_seconds()
                remaining = max(0, self.auto_lock_timeout - elapsed)
                status["auto_lock_remaining"] = remaining
            
            return status
    
    def _start_auto_lock_timer(self, blue_vault):
        """Start auto-lock timer."""
        self._cancel_auto_lock_timer()
        
        def auto_lock():
            if self.state == LockState.UNLOCKED:
                # Check if timeout has elapsed
                if self.unlock_time:
                    elapsed = (datetime.utcnow() - self.unlock_time).total_seconds()
                    if elapsed >= self.auto_lock_timeout:
                        self.lock(blue_vault)
                        print("🔒 Auto-locked: Safe word timeout reached")
        
        # Schedule auto-lock check
        # In a full implementation, use threading.Timer
        # For now, this is a placeholder
        self._auto_lock_timer = threading.Timer(
            float(self.auto_lock_timeout),
            auto_lock
        )
        self._auto_lock_timer.start()
    
    def _cancel_auto_lock_timer(self):
        """Cancel auto-lock timer."""
        if self._auto_lock_timer:
            self._auto_lock_timer.cancel()
            self._auto_lock_timer = None
    
    def is_unlocked(self) -> bool:
        """
        Check if safe word is currently unlocked.
        
        Returns:
            True if unlocked, False if locked
        """
        return self.state == LockState.UNLOCKED

