"""
Memory Manager - Unified interface for persistent memory
Uses vault system (Green, Blue, Red) with classification and distillation.
"""
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json

from .green_vault import GreenVault
from .blue_vault import BlueVault
from .red_vault import RedVault
from .classification import ConversationClassifier
from .distillation import ConversationDistiller
from .memory_gates import MemoryGates

# Import Red Thread event for constitutional integration (Axiom 8)
try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    # Fallback if core module not available
    RED_THREAD_EVENT = None


class MemoryManager:
    """
    Unified memory manager using vault system.
    
    Routes conversations through classifier to appropriate vault:
    - discard: No storage
    - normal: Green Vault (distilled summaries)
    - sensitive: Blue Vault (ephemeral, requires unlock)
    - secret: Red Vault (encrypted, requires explicit declaration)
    """
    
    def __init__(self, memory_dir: Path, encryption_key: Optional[bytes] = None, safe_word_controller=None):
        """
        Initialize memory manager with vault system.
        
        Args:
            memory_dir: Directory for memory storage
            encryption_key: Encryption key for SQLite (legacy, may be used for Green Vault)
            safe_word_controller: SafeWordController instance (optional)
        """
        self.memory_dir = Path(memory_dir)
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to create memory directory {self.memory_dir}: {e}")
        
        # Initialize vaults
        self.green_vault = GreenVault(self.memory_dir / "green_vault")
        self.blue_vault = BlueVault()
        self.red_vault = RedVault(self.memory_dir / "red_vault")
        
        # Initialize classification and distillation
        self.classifier = ConversationClassifier()
        self.distiller = ConversationDistiller()
        
        # Keep memory gates for backward compatibility
        self.gates = MemoryGates()
        
        # Safe word controller (optional, for Blue/Red Vault access)
        self.safe_word_controller = safe_word_controller
        
        # Initialize learning system
        self.learning_manager = None
        self.learning_audit = None
        self._initialize_learning()
        
        # Legacy support: Keep SQLite and ChromaDB for backward compatibility
        # These are now used internally by Green Vault
        from .encrypted_sqlite import EncryptedSQLite
        from .chromadb_store import ChromaDBStore
        self.sqlite = EncryptedSQLite(
            self.memory_dir / "episodic_memory.db",
            encryption_key
        )
        self.chromadb = ChromaDBStore(
            self.memory_dir / "chromadb",
            collection_name="janet_memory"
        )
        
        self.last_summary_date = None
        self._load_last_summary_date()
    
    def _initialize_learning(self):
        """Initialize learning system (Green Vault learning)."""
        try:
            from .learning_manager import LearningManager
            from .learning_audit import LearningAuditLogger
            
            # Initialize audit logger
            audit_dir = self.memory_dir / "learning_audit"
            self.learning_audit = LearningAuditLogger(audit_dir)
            
            # Initialize learning manager
            self.learning_manager = LearningManager(
                green_vault=self.green_vault,
                audit_logger=self.learning_audit
            )
        except Exception as e:
            print(f"⚠️  Learning system initialization failed: {e}")
            self.learning_manager = None
            self.learning_audit = None
    
    def _load_last_summary_date(self):
        """Load last summary date from metadata."""
        # In a full implementation, this would be stored in SQLite metadata
        # For now, we'll calculate it on the fly
        try:
            summaries = self.sqlite.get_weekly_summaries(limit=1)
            if summaries:
                self.last_summary_date = datetime.fromisoformat(summaries[0]['week_end'].replace('Z', '+00:00'))
            else:
                self.last_summary_date = None
        except Exception as e:
            print(f"⚠️  Failed to load last summary date: {e}")
            self.last_summary_date = None
    
    def store(self, user_input: str, janet_response: str, context: Optional[Dict] = None) -> bool:
        """
        Store memory using vault system with classification.
        
        Args:
            user_input: User's input
            janet_response: Janet's response
            context: Additional context
        
        Returns:
            True if stored, False if blocked or discarded
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - memory write blocked")
            return False
        
        # Skip empty or whitespace-only inputs
        if not user_input or not user_input.strip():
            return False
        
        # Classify conversation
        classification = self.classifier.classify(user_input, context)
        
        if classification == "discard":
            # Ephemeral conversation, no storage needed
            return False
        
        elif classification == "normal":
            # Safe for Green Vault - distill and store summary
            try:
                distilled = self.distiller.distill(user_input, janet_response, context)
                entry_id = self.green_vault.add_summary(
                    summary=distilled.get("summary", ""),
                    tags=distilled.get("tags", []),
                    confidence=distilled.get("confidence", 0.5),
                    expiry=None
                )
                return entry_id != ""
            except Exception as e:
                print(f"⚠️  Error storing in Green Vault: {e}")
                return False
        
        elif classification == "sensitive":
            # Requires Blue Vault (unlocked)
            if not self.safe_word_controller or not self.safe_word_controller.is_unlocked():
                print("⚠️  Sensitive information requires safe word unlock")
                return False
            
            # Store in Blue Vault as context note
            try:
                combined_note = f"User: {user_input}\nJanet: {janet_response}"
                self.blue_vault.store_context_note(combined_note)
                return True
            except Exception as e:
                print(f"⚠️  Error storing in Blue Vault: {e}")
                return False
        
        elif classification == "secret":
            # Requires explicit declaration before Red Vault
            if self.classifier.requires_explicit_declaration(user_input):
                print("⚠️  Secret detected but requires explicit declaration. Use 'store secret: <id>' format.")
                return False
            
            # For now, secrets are not auto-stored
            # User must explicitly request storage with safe word
            print("⚠️  Secret detected. Use explicit storage command with safe word.")
            return False
        
        return False
    
    def store_conversation(self, conversation_history: List[Dict[str, str]], context: Optional[Dict] = None) -> bool:
        """
        Store entire conversation as single distilled summary.
        
        Args:
            conversation_history: List of messages with 'role' and 'content' keys
            context: Additional context (tone, emotional state, etc.)
        
        Returns:
            True if stored, False if blocked or discarded
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - conversation storage blocked")
            return False
        
        if not conversation_history:
            return False
        
        # Combine conversation into text for classification and distillation
        conversation_text_parts = []
        first_user_message = None
        
        for msg in conversation_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                if not first_user_message:
                    first_user_message = content
                conversation_text_parts.append(f"User: {content}")
            elif role == "assistant":
                conversation_text_parts.append(f"Janet: {content}")
        
        if not first_user_message:
            # No user messages, skip storage
            return False
        
        combined_conversation = "\n".join(conversation_text_parts)
        
        # Classify conversation using first user message
        classification = self.classifier.classify(first_user_message, context)
        
        if classification == "discard":
            # Ephemeral conversation, no storage needed
            return False
        
        elif classification == "normal":
            # Safe for Green Vault - distill entire conversation into single summary
            try:
                # Create a combined user/response for distillation
                # Extract all user messages and all assistant messages
                user_messages = [msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"]
                assistant_messages = [msg.get("content", "") for msg in conversation_history if msg.get("role") == "assistant"]
                
                combined_user = " ".join(user_messages)
                combined_assistant = " ".join(assistant_messages)
                
                # Distill entire conversation
                distilled = self.distiller.distill(combined_user, combined_assistant, context)
                
                # Store in Green Vault
                entry_id = self.green_vault.add_summary(
                    summary=distilled.get("summary", ""),
                    tags=distilled.get("tags", []),
                    confidence=distilled.get("confidence", 0.5),
                    expiry=None
                )
                return entry_id != ""
            except Exception as e:
                print(f"⚠️  Error storing conversation in Green Vault: {e}")
                return False
        
        elif classification == "sensitive":
            # Requires Blue Vault (unlocked)
            if not self.safe_word_controller or not self.safe_word_controller.is_unlocked():
                print("⚠️  Sensitive conversation requires safe word unlock")
                return False
            
            # Store in Blue Vault as context note
            try:
                self.blue_vault.store_context_note(combined_conversation)
                return True
            except Exception as e:
                print(f"⚠️  Error storing conversation in Blue Vault: {e}")
                return False
        
        elif classification == "secret":
            # Secrets are not auto-stored from conversations
            print("⚠️  Secret conversation detected. Use explicit storage command with safe word.")
            return False
        
        return False
    
    def undo_last(self) -> bool:
        """
        Undo the last Green Vault add or delete (JBJanet).

        Returns:
            True if undo succeeded, False otherwise
        """
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - undo blocked")
            return False
        return self.green_vault.undo_last_summary()

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search memories semantically (Green Vault only).
        
        Args:
            query: Search query
            n_results: Number of results
        
        Returns:
            List of matching summaries from Green Vault
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - memory search blocked")
            return []
        
        # Search Green Vault (safe summaries only)
        return self.green_vault.query_context(query, n_results)
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """
        Get recent episodic memories.
        
        Args:
            limit: Number of memories
        
        Returns:
            List of recent memories
        """
        return self.sqlite.get_recent_memories(limit)
    
    def forget(self, memory_id: Optional[int] = None) -> Dict:
        """
        Forget memory (delete from all vaults).
        
        Args:
            memory_id: Specific memory ID to forget, or None for all
        
        Returns:
            Dictionary with deletion results
        """
        # Axiom 8: Red Thread Protocol - Stop all operations if Red Thread is active
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - memory deletion blocked")
            return {
                "success": False,
                "message": "Memory deletion blocked by Red Thread"
            }
        
        if memory_id is None:
            # Forget all
            # Zeroize Blue Vault
            self.blue_vault.zeroize()
            
            # Delete all from Green Vault (legacy support)
            sqlite_count = self.sqlite.delete_all_memories()
            chromadb_count = self.chromadb.delete_all_memories()
            
            # Note: Red Vault secrets are not deleted by default
            # User must explicitly delete secrets
            
            return {
                "success": True,
                "green_vault_deleted": sqlite_count + chromadb_count,
                "blue_vault_zeroized": True,
                "message": f"Forgot {sqlite_count + chromadb_count} memories from Green Vault, zeroized Blue Vault"
            }
        else:
            # Forget specific memory (Green Vault only for now)
            # Convert memory_id to entry_id format
            entry_id = f"summary_{memory_id}_"
            green_success = self.green_vault.delete_entry(entry_id)
            sqlite_success = self.sqlite.delete_memory(memory_id)
            
            return {
                "success": green_success or sqlite_success,
                "memory_id": memory_id,
                "message": f"Forgot memory {memory_id}" if (green_success or sqlite_success) else "Memory not found"
            }
    
    def _check_weekly_summary(self):
        """Check if weekly summary should be generated."""
        now = datetime.utcnow()
        
        # Generate summary if:
        # 1. No previous summary exists, OR
        # 2. Last summary was more than 7 days ago
        should_generate = False
        
        if self.last_summary_date is None:
            should_generate = True
        else:
            days_since = (now - self.last_summary_date.replace(tzinfo=None)).days
            if days_since >= 7:
                should_generate = True
        
        if should_generate:
            self._generate_weekly_summary()
    
    def _generate_weekly_summary(self):
        """Generate weekly summary of memories."""
        now = datetime.utcnow()
        week_start = (now - timedelta(days=7)).isoformat() + "Z"
        week_end = now.isoformat() + "Z"
        
        # Get memories from the past week
        recent_memories = self.sqlite.get_recent_memories(limit=100)
        
        # Filter to last week
        week_memories = []
        week_start_dt = datetime.fromisoformat(week_start.replace('Z', '+00:00'))
        
        for memory in recent_memories:
            memory_dt = datetime.fromisoformat(memory['timestamp'].replace('Z', '+00:00'))
            if memory_dt >= week_start_dt:
                week_memories.append(memory)
        
        if not week_memories:
            return
        
        # Generate summary (simplified - in full implementation, use LLM)
        summary_lines = [
            f"Weekly Summary ({week_start} to {week_end})",
            f"Total conversations: {len(week_memories)}",
            "",
            "Key topics discussed:",
        ]
        
        # Extract topics (simplified - just first few memories)
        for memory in week_memories[:5]:
            summary_lines.append(f"- {memory['user_input'][:50]}...")
        
        summary = "\n".join(summary_lines)
        
        # Store summary
        self.sqlite.store_weekly_summary(week_start, week_end, summary)
        self.last_summary_date = datetime.fromisoformat(week_end.replace('Z', '+00:00'))
        
        print(f"📊 Weekly summary generated: {len(week_memories)} conversations")
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        try:
            episodic_count = len(self.sqlite.get_recent_memories(limit=10000))
        except Exception as e:
            print(f"⚠️  Failed to get episodic memory count: {e}")
            episodic_count = 0
        
        try:
            semantic_count = self.chromadb.get_collection_count()
        except Exception as e:
            print(f"⚠️  Failed to get semantic memory count: {e}")
            semantic_count = 0
        
        return {
            "episodic_count": episodic_count,
            "semantic_count": semantic_count,
            "last_summary": self.last_summary_date.isoformat() if self.last_summary_date else None
        }

