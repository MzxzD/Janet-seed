"""
Encrypted SQLite for Episodic Memory and Metadata
Stores conversation history, timestamps, and metadata with encryption.
"""
import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import os

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class EncryptedSQLite:
    """Encrypted SQLite database for episodic memory."""
    
    def __init__(self, db_path: Path, encryption_key: Optional[bytes] = None):
        """
        Initialize encrypted SQLite database.
        
        Args:
            db_path: Path to SQLite database file
            encryption_key: Encryption key (derived from safe word if None)
        """
        self.db_path = Path(db_path)
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to create database directory {self.db_path.parent}: {e}")
        
        # Derive encryption key if not provided
        if encryption_key is None:
            # Default key derivation (in production, use safe word)
            default_key = b"janet_memory_default_key_change_in_production"
            self.encryption_key = self._derive_key(default_key)
        else:
            self.encryption_key = encryption_key
        
        self.cipher = Fernet(self.encryption_key) if HAS_CRYPTO else None
        self._init_database()
    
    def _derive_key(self, password: bytes) -> bytes:
        """Derive encryption key from password."""
        if not HAS_CRYPTO:
            return password[:32]  # Fallback if crypto not available
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'janet_memory_salt',  # In production, use random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _init_database(self):
        """Initialize database schema."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Episodic memory table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS episodic_memory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        user_input TEXT NOT NULL,
                        janet_response TEXT NOT NULL,
                        context TEXT,
                        encrypted INTEGER DEFAULT 0
                    )
                ''')
                
                # Metadata table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memory_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        memory_id INTEGER,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        FOREIGN KEY (memory_id) REFERENCES episodic_memory(id)
                    )
                ''')
                
                # Weekly summaries table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS weekly_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        week_start TEXT NOT NULL,
                        week_end TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        encrypted INTEGER DEFAULT 0
                    )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"⚠️  Failed to initialize SQLite database: {e}")
            raise  # Re-raise since database initialization is critical
        except Exception as e:
            print(f"⚠️  Unexpected error initializing database: {e}")
            raise
    
    def store_memory(self, user_input: str, janet_response: str, context: Optional[Dict] = None) -> Optional[int]:
        """
        Store episodic memory.
        
        Args:
            user_input: User's input text
            janet_response: Janet's response
            context: Additional context (tone, emotional state, etc.)
        
        Returns:
            Memory ID if successful, None if failed
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                timestamp = datetime.utcnow().isoformat() + "Z"
                context_json = json.dumps(context) if context else None
                
                # Encrypt if crypto available
                try:
                    if self.cipher:
                        encrypted_input = self.cipher.encrypt(user_input.encode()).decode()
                        encrypted_response = self.cipher.encrypt(janet_response.encode()).decode()
                        encrypted = 1
                    else:
                        encrypted_input = user_input
                        encrypted_response = janet_response
                        encrypted = 0
                except Exception as e:
                    print(f"⚠️  Encryption failed, storing unencrypted: {e}")
                    encrypted_input = user_input
                    encrypted_response = janet_response
                    encrypted = 0
                
                cursor.execute('''
                    INSERT INTO episodic_memory (timestamp, user_input, janet_response, context, encrypted)
                    VALUES (?, ?, ?, ?, ?)
                ''', (timestamp, encrypted_input, encrypted_response, context_json, encrypted))
                
                memory_id = cursor.lastrowid
                conn.commit()
                
                return memory_id
        except sqlite3.Error as e:
            print(f"⚠️  SQLite error storing memory: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Unexpected error storing memory: {e}")
            return None
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict]:
        """
        Get recent memories.
        
        Args:
            limit: Number of memories to retrieve
        
        Returns:
            List of memory dictionaries
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, user_input, janet_response, context, encrypted
                    FROM episodic_memory
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                memories = []
                
                for row in rows:
                    user_input = row['user_input']
                    janet_response = row['janet_response']
                    
                    # Decrypt if encrypted
                    if row['encrypted'] and self.cipher:
                        try:
                            user_input = self.cipher.decrypt(user_input.encode()).decode()
                            janet_response = self.cipher.decrypt(janet_response.encode()).decode()
                        except Exception:
                            user_input = "[DECRYPTION_FAILED]"
                            janet_response = "[DECRYPTION_FAILED]"
                    
                    memory = {
                        "id": row['id'],
                        "timestamp": row['timestamp'],
                        "user_input": user_input,
                        "janet_response": janet_response,
                        "context": json.loads(row['context']) if row['context'] else None
                    }
                    memories.append(memory)
                
                return memories
        except sqlite3.Error as e:
            print(f"⚠️  SQLite error retrieving memories: {e}")
            return []
        except Exception as e:
            print(f"⚠️  Unexpected error retrieving memories: {e}")
            return []
    
    def delete_memory(self, memory_id: int) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: Memory ID to delete
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM episodic_memory WHERE id = ?', (memory_id,))
                cursor.execute('DELETE FROM memory_metadata WHERE memory_id = ?', (memory_id,))
                
                deleted = cursor.rowcount > 0
                conn.commit()
                
                return deleted
        except sqlite3.Error as e:
            print(f"⚠️  SQLite error deleting memory: {e}")
            return False
        except Exception as e:
            print(f"⚠️  Unexpected error deleting memory: {e}")
            return False
    
    def delete_all_memories(self) -> int:
        """
        Delete all memories (forget everything).
        
        Returns:
            Number of memories deleted
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM episodic_memory')
                count = cursor.fetchone()[0]
                
                cursor.execute('DELETE FROM episodic_memory')
                cursor.execute('DELETE FROM memory_metadata')
                
                conn.commit()
                
                return count
        except sqlite3.Error as e:
            print(f"⚠️  SQLite error deleting all memories: {e}")
            return 0
        except Exception as e:
            print(f"⚠️  Unexpected error deleting all memories: {e}")
            return 0
    
    def store_weekly_summary(self, week_start: str, week_end: str, summary: str):
        """Store a weekly summary."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                created_at = datetime.utcnow().isoformat() + "Z"
                
                # Encrypt if crypto available
                try:
                    if self.cipher:
                        encrypted_summary = self.cipher.encrypt(summary.encode()).decode()
                        encrypted = 1
                    else:
                        encrypted_summary = summary
                        encrypted = 0
                except Exception as e:
                    print(f"⚠️  Encryption failed, storing unencrypted summary: {e}")
                    encrypted_summary = summary
                    encrypted = 0
                
                cursor.execute('''
                    INSERT INTO weekly_summaries (week_start, week_end, summary, created_at, encrypted)
                    VALUES (?, ?, ?, ?, ?)
                ''', (week_start, week_end, encrypted_summary, created_at, encrypted))
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"⚠️  SQLite error storing weekly summary: {e}")
            raise
        except Exception as e:
            print(f"⚠️  Unexpected error storing weekly summary: {e}")
            raise
    
    def get_weekly_summaries(self, limit: int = 10) -> List[Dict]:
        """Get recent weekly summaries."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, week_start, week_end, summary, created_at, encrypted
                    FROM weekly_summaries
                    ORDER BY week_start DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                summaries = []
                
                for row in rows:
                    summary = row['summary']
                    
                    # Decrypt if encrypted
                    if row['encrypted'] and self.cipher:
                        try:
                            summary = self.cipher.decrypt(summary.encode()).decode()
                        except Exception:
                            summary = "[DECRYPTION_FAILED]"
                    
                    summaries.append({
                        "id": row['id'],
                        "week_start": row['week_start'],
                        "week_end": row['week_end'],
                        "summary": summary,
                        "created_at": row['created_at']
                    })
                
                return summaries
        except sqlite3.Error as e:
            print(f"⚠️  SQLite error retrieving weekly summaries: {e}")
            return []
        except Exception as e:
            print(f"⚠️  Unexpected error retrieving weekly summaries: {e}")
            return []

