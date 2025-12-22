"""
Green Vault - Safe Summary Storage
Stores distilled, non-sensitive summaries for context retrieval.

ALLOWED:
- Abstract summaries of conversations
- Topic tags and themes
- Emotional tone indicators (general)
- Actionable insights
- Timestamps and metadata

FORBIDDEN:
- Raw conversation transcripts
- Personally identifiable information (unless explicitly consented)
- Secrets or sensitive data
- Verbatim quotes (unless essential)
"""

from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import json

from .chromadb_store import ChromaDBStore
from .encrypted_sqlite import EncryptedSQLite

# Import Red Thread event for constitutional integration (Axiom 8)
try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None


class GreenVault:
    """
    Green Vault - Safe summary storage for non-sensitive information.
    
    This vault stores only distilled summaries, never raw conversations.
    All entries are safe for semantic search and long-term storage.
    """
    
    def __init__(self, memory_dir: Path):
        """
        Initialize Green Vault.
        
        Args:
            memory_dir: Directory for memory storage
        """
        self.memory_dir = Path(memory_dir)
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to create Green Vault directory {self.memory_dir}: {e}")
        
        # Initialize storage backends
        self.sqlite = EncryptedSQLite(
            self.memory_dir / "green_vault.db",
            encryption_key=None  # Green Vault can use default encryption
        )
        self.chromadb = ChromaDBStore(
            self.memory_dir / "green_vault_chromadb",
            collection_name="green_vault_summaries"
        )
    
    def add_summary(
        self,
        summary: str,
        tags: List[str],
        confidence: float,
        expiry: Optional[datetime] = None
    ) -> str:
        """
        Add a distilled summary to Green Vault.
        
        Args:
            summary: Distilled summary text (no raw conversations)
            tags: List of topic tags
            confidence: Confidence score (0.0-1.0)
            expiry: Optional expiry date for the entry
        
        Returns:
            Entry ID if successful, empty string otherwise
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Green Vault write blocked")
            return ""
        
        if not summary or not summary.strip():
            return ""
        
        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            expiry_str = expiry.isoformat() + "Z" if expiry else None
            
            # Store in SQLite (episodic)
            # Use a simplified storage format for summaries
            context = {
                "tags": tags,
                "confidence": confidence,
                "expiry": expiry_str,
                "type": "summary"
            }
            
            # Store summary as both input and response (for compatibility)
            memory_id = self.sqlite.store_memory(
                user_input=summary,
                janet_response="",  # Summary is self-contained
                context=context
            )
            
            if memory_id is None:
                return ""
            
            # Store in ChromaDB for semantic search
            entry_id = f"summary_{memory_id}_{timestamp}"
            metadata = {
                "memory_id": str(memory_id),
                "tags": json.dumps(tags),
                "confidence": str(confidence),
                "expiry": expiry_str or "",
                "timestamp": timestamp,
                "type": "summary"
            }
            
            chromadb_id = self.chromadb.store_memory(summary, metadata)
            if chromadb_id is None:
                # SQLite storage succeeded, but ChromaDB failed
                # This is acceptable - episodic memory is more important
                print("⚠️  Warning: Summary stored in SQLite but not in ChromaDB")
            
            return entry_id
        except Exception as e:
            print(f"⚠️  Error storing summary in Green Vault: {e}")
            return ""
    
    def query_context(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Query context from Green Vault using semantic search.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of matching summaries with metadata
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Green Vault read blocked")
            return []
        
        if not query or not query.strip():
            return []
        
        try:
            # Query ChromaDB for semantic matches
            results = self.chromadb.search_memories(query, n_results)
            
            # Format results
            formatted_results = []
            for result in results:
                metadata = result.get("metadata", {})
                formatted_result = {
                    "id": result.get("id", ""),
                    "summary": result.get("text", ""),
                    "tags": json.loads(metadata.get("tags", "[]")),
                    "confidence": float(metadata.get("confidence", "0.0")),
                    "timestamp": metadata.get("timestamp", ""),
                    "distance": result.get("distance")
                }
                
                # Check expiry
                expiry_str = metadata.get("expiry", "")
                if expiry_str:
                    try:
                        expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                        if datetime.utcnow().replace(tzinfo=None) > expiry.replace(tzinfo=None):
                            continue  # Skip expired entries
                    except Exception:
                        pass  # If expiry parsing fails, include the entry
                
                formatted_results.append(formatted_result)
            
            return formatted_results
        except Exception as e:
            print(f"⚠️  Error querying Green Vault: {e}")
            return []
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete an entry from Green Vault.
        
        Args:
            entry_id: Entry ID to delete
        
        Returns:
            True if deleted, False otherwise
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - Green Vault deletion blocked")
            return False
        
        try:
            # Extract memory_id from entry_id (format: summary_{memory_id}_{timestamp})
            if entry_id.startswith("summary_"):
                parts = entry_id.split("_")
                if len(parts) >= 2:
                    try:
                        memory_id = int(parts[1])
                        # Delete from SQLite
                        sqlite_success = self.sqlite.delete_memory(memory_id)
                        # Delete from ChromaDB
                        chromadb_success = self.chromadb.delete_memory(entry_id)
                        return sqlite_success or chromadb_success
                    except (ValueError, IndexError):
                        pass
            
            # Try direct ChromaDB deletion
            return self.chromadb.delete_memory(entry_id)
        except Exception as e:
            print(f"⚠️  Error deleting entry from Green Vault: {e}")
            return False
    
    def get_training_data(
        self,
        limit: Optional[int] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get training data from Green Vault summaries.
        
        Returns summaries formatted for training, respecting consent and opt-out flags.
        
        Args:
            limit: Maximum number of summaries to return
            exclude_ids: List of summary IDs to exclude
            
        Returns:
            List of training data dictionaries
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - training data access blocked")
            return []
        
        if exclude_ids is None:
            exclude_ids = []
        
        # Get all summaries
        all_summaries = self.get_all_summaries()
        
        # Filter and format
        training_data = []
        for summary in all_summaries:
            entry_id = summary.get("id", "")
            if entry_id in exclude_ids:
                continue
            
            metadata = summary.get("metadata", {})
            # Only include if has consent and not opted out
            if (metadata.get("consent_for_learning", False) and 
                not metadata.get("opted_out_from_learning", False)):
                training_data.append({
                    "id": entry_id,
                    "summary": summary.get("summary", ""),
                    "tags": summary.get("tags", []),
                    "confidence": summary.get("confidence", 0.0),
                    "timestamp": summary.get("timestamp", ""),
                    "metadata": metadata
                })
        
        # Apply limit
        if limit:
            training_data = training_data[:limit]
        
        return training_data
    
    def grant_consent(self, entry_id: str) -> bool:
        """
        Grant consent for a summary to be used for learning.
        
        Args:
            entry_id: ID of summary to grant consent for
            
        Returns:
            True if consent granted successfully, False otherwise
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - consent grant blocked")
            return False
        
        try:
            # Get summary from ChromaDB
            summary = self.get_summary(entry_id)
            if not summary:
                return False
            
            # Update metadata
            metadata = summary.get("metadata", {})
            metadata["consent_for_learning"] = True
            metadata["consent_granted_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Update in ChromaDB
            # Note: ChromaDB update requires re-storing with updated metadata
            self.chromadb.update_metadata(entry_id, metadata)
            
            return True
        except Exception as e:
            print(f"⚠️  Error granting consent: {e}")
            return False
    
    def opt_out_summary(self, entry_id: str) -> bool:
        """
        Mark summary as opted out from learning.
        
        Args:
            entry_id: ID of summary to opt out
            
        Returns:
            True if opt-out successful, False otherwise
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - opt-out blocked")
            return False
        
        try:
            # Get summary from ChromaDB
            summary = self.get_summary(entry_id)
            if not summary:
                return False
            
            # Update metadata
            metadata = summary.get("metadata", {})
            metadata["opted_out_from_learning"] = True
            metadata["opted_out_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Update in ChromaDB
            self.chromadb.update_metadata(entry_id, metadata)
            
            return True
        except Exception as e:
            print(f"⚠️  Error opting out summary: {e}")
            return False
    
    def get_summary(self, entry_id: str) -> Optional[Dict]:
        """
        Get a single summary by ID.
        
        Args:
            entry_id: ID of summary to retrieve
            
        Returns:
            Summary dictionary or None if not found
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - summary retrieval blocked")
            return None
        
        try:
            # Query ChromaDB by ID
            result = self.chromadb.get_memory(entry_id)
            if not result:
                return None
            
            metadata = result.get("metadata", {})
            return {
                "id": entry_id,
                "summary": result.get("text", ""),
                "tags": json.loads(metadata.get("tags", "[]")),
                "confidence": float(metadata.get("confidence", "0.0")),
                "timestamp": metadata.get("timestamp", ""),
                "metadata": metadata
            }
        except Exception as e:
            print(f"⚠️  Error getting summary: {e}")
            return None
    
    def get_all_summaries(self) -> List[Dict]:
        """
        Get all summaries from Green Vault.
        
        Returns:
            List of all summaries with metadata
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - summary retrieval blocked")
            return []
        
        try:
            # Get all from ChromaDB
            all_results = self.chromadb.get_all_memories()
            
            summaries = []
            for result in all_results:
                metadata = result.get("metadata", {})
                entry_id = result.get("id", "")
                summaries.append({
                    "id": entry_id,
                    "summary": result.get("text", ""),
                    "tags": json.loads(metadata.get("tags", "[]")),
                    "confidence": float(metadata.get("confidence", "0.0")),
                    "timestamp": metadata.get("timestamp", ""),
                    "metadata": metadata
                })
            
            return summaries
        except Exception as e:
            print(f"⚠️  Error getting all summaries: {e}")
            return []

