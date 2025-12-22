"""
Red Vault - Encrypted Secret Storage
Long-term encrypted storage of secrets that must persist across sessions.

ALLOWED:
- Encrypted secret data
- Secret metadata (ID, timestamp, tags)
- Encrypted storage at rest

FORBIDDEN:
- Embeddings or vector representations
- Summaries or abstractions
- Training data usage
- Decryption without explicit safe word
- Any form of learning from secrets
- Embedding generation from secrets
- Semantic search over secrets
- Using secrets to influence model behavior

SECURITY:
- Secrets are encrypted at rest using Fernet
- Encryption keys are derived from safe word (never stored)
- Secrets are never decrypted except for explicit session use
- No metadata about secret content is stored unencrypted
"""

from pathlib import Path
from typing import Dict, Optional, List
import json
import hashlib

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Import Red Thread event for constitutional integration (Axiom 8)
try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None


class RedVault:
    """
    Red Vault - Encrypted storage for secrets that must persist.
    
    This vault stores secrets encrypted at rest. Secrets are never
    embedded, summarized, or used for learning. They exist only for
    explicit decryption when the safe word is provided.
    
    FORBIDDEN BEHAVIORS:
    - No embeddings or vector representations
    - No summaries or abstractions
    - No training data usage
    - No semantic search
    - No model behavior influence
    """
    
    def __init__(self, vault_dir: Path):
        """
        Initialize Red Vault.
        
        Args:
            vault_dir: Directory for encrypted vault storage
        """
        self.vault_dir = Path(vault_dir)
        try:
            self.vault_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to create Red Vault directory {self.vault_dir}: {e}")
        
        # Metadata file (stores only IDs and timestamps, no secret content)
        self.metadata_file = self.vault_dir / "red_vault_metadata.json"
        self._metadata = self._load_metadata()
    
    def _derive_key(self, safe_word: str) -> bytes:
        """
        Derive encryption key from safe word.
        
        Args:
            safe_word: Safe word for key derivation
        
        Returns:
            Fernet key derived from safe word
        
        Note:
            This uses PBKDF2 with SHA256. The safe word is never stored.
        """
        if not HAS_CRYPTO:
            # Fallback if crypto not available (not secure, but allows testing)
            key_bytes = safe_word.encode()[:32].ljust(32, b'0')
            return base64.urlsafe_b64encode(key_bytes)
        
        # Use PBKDF2 to derive key from safe word
        # Salt is fixed per vault (in production, consider per-secret salts)
        salt = b'janet_red_vault_salt'  # In production, use random salt per secret
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(safe_word.encode()))
        return key
    
    def _get_cipher(self, safe_word: str) -> Optional[Fernet]:
        """
        Get Fernet cipher for safe word.
        
        Args:
            safe_word: Safe word for key derivation
        
        Returns:
            Fernet cipher instance or None if crypto unavailable
        """
        if not HAS_CRYPTO:
            return None
        
        key = self._derive_key(safe_word)
        return Fernet(key)
    
    def _load_metadata(self) -> Dict:
        """Load metadata file (only IDs and timestamps)."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Failed to load Red Vault metadata: {e}")
            return {}
    
    def _save_metadata(self):
        """Save metadata file (only IDs and timestamps)."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save Red Vault metadata: {e}")
    
    def store_secret(
        self,
        secret_id: str,
        secret_data: str,
        safe_word: str
    ) -> bool:
        """
        Store a secret in Red Vault (encrypted at rest).
        
        Args:
            secret_id: Unique identifier for the secret
            secret_data: Secret data to encrypt and store
            safe_word: Safe word for key derivation (not stored)
        
        Returns:
            True if stored successfully, False otherwise
        
        Note:
            The safe word is used to derive the encryption key but is never stored.
            Secrets are encrypted using Fernet before storage.
            
            FORBIDDEN: This method does NOT:
            - Create embeddings
            - Generate summaries
            - Store unencrypted metadata about secret content
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Red Vault write blocked")
            return False
        
        if not secret_id or not secret_data or not safe_word:
            return False
        
        try:
            cipher = self._get_cipher(safe_word)
            if not cipher:
                print("⚠️  Cryptography not available - cannot store secret")
                return False
            
            # Encrypt secret data
            encrypted_data = cipher.encrypt(secret_data.encode())
            
            # Store encrypted file
            secret_file = self.vault_dir / f"{secret_id}.enc"
            with open(secret_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Update metadata (only ID and timestamp, no content)
            from datetime import datetime
            self._metadata[secret_id] = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "encrypted": True
            }
            self._save_metadata()
            
            return True
        except Exception as e:
            print(f"⚠️  Error storing secret in Red Vault: {e}")
            return False
    
    def decrypt_for_session(
        self,
        secret_id: str,
        safe_word: str
    ) -> Optional[str]:
        """
        Decrypt a secret for session use.
        
        Args:
            secret_id: Secret identifier
            safe_word: Safe word for key derivation
        
        Returns:
            Decrypted secret if successful, None otherwise
        
        Note:
            This decrypts the secret for temporary use. The decrypted
            value should be moved to Blue Vault for session access.
            
            FORBIDDEN: This method does NOT:
            - Create embeddings from the decrypted secret
            - Summarize the secret
            - Use the secret for learning
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Red Vault read blocked")
            return None
        
        if not secret_id or not safe_word:
            return None
        
        try:
            secret_file = self.vault_dir / f"{secret_id}.enc"
            if not secret_file.exists():
                return None
            
            # Read encrypted data
            with open(secret_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt
            cipher = self._get_cipher(safe_word)
            if not cipher:
                print("⚠️  Cryptography not available - cannot decrypt secret")
                return None
            
            decrypted_data = cipher.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            print(f"⚠️  Error decrypting secret from Red Vault: {e}")
            return None
    
    def list_secrets(self) -> List[str]:
        """
        List all secret IDs in Red Vault.
        
        Returns:
            List of secret IDs (no decryption occurs)
        
        Note:
            This returns only metadata (IDs), not secret content.
            No decryption is performed.
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Red Vault list blocked")
            return []
        
        return list(self._metadata.keys())
    
    def delete_secret(self, secret_id: str) -> bool:
        """
        Delete a secret from Red Vault.
        
        Args:
            secret_id: Secret identifier to delete
        
        Returns:
            True if deleted, False otherwise
        
        Note:
            Deletion is permanent. The encrypted file is removed.
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Red Vault deletion blocked")
            return False
        
        if not secret_id:
            return False
        
        try:
            # Delete encrypted file
            secret_file = self.vault_dir / f"{secret_id}.enc"
            if secret_file.exists():
                secret_file.unlink()
            
            # Remove from metadata
            if secret_id in self._metadata:
                del self._metadata[secret_id]
                self._save_metadata()
            
            return True
        except Exception as e:
            print(f"⚠️  Error deleting secret from Red Vault: {e}")
            return False

