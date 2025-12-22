"""
ChromaDB Vector Store for Semantic Memory
Stores embeddings for semantic search and retrieval.
"""
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class ChromaDBStore:
    """ChromaDB vector store for semantic memory."""
    
    def __init__(self, persist_directory: Path, collection_name: str = "janet_memory"):
        """
        Initialize ChromaDB store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection
        """
        self.persist_directory = Path(persist_directory)
        try:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"⚠️  Failed to create ChromaDB directory {self.persist_directory}: {e}")
            # Non-critical, will fail during initialization if needed
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        if HAS_CHROMADB:
            self._initialize()
        else:
            print("⚠️  ChromaDB not available. Install with: pip install chromadb")
    
    def _initialize(self):
        """Initialize ChromaDB client and collection."""
        if not HAS_CHROMADB:
            return
        
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Janet's semantic memory"}
            )
            
            print("✅ ChromaDB initialized")
        except Exception as e:
            print(f"⚠️  ChromaDB initialization failed: {e}")
            self.client = None
            self.collection = None
    
    def is_available(self) -> bool:
        """Check if ChromaDB is available."""
        return HAS_CHROMADB and self.collection is not None
    
    def store_memory(self, text: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Store text in vector database.
        
        Args:
            text: Text to store
            metadata: Additional metadata
        
        Returns:
            Memory ID if successful, None otherwise
        """
        if not self.is_available():
            return None
        
        try:
            memory_id = f"memory_{datetime.utcnow().timestamp()}"
            
            # Prepare metadata
            meta = metadata or {}
            meta["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            # Add to collection
            self.collection.add(
                documents=[text],
                ids=[memory_id],
                metadatas=[meta]
            )
            
            return memory_id
        except Exception as e:
            print(f"⚠️  Failed to store memory in ChromaDB: {e}")
            return None
    
    def search_memories(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search memories by semantic similarity.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of matching memories with scores
        """
        if not self.is_available():
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            memories = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    memory = {
                        "id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None
                    }
                    memories.append(memory)
            
            return memories
        except Exception as e:
            print(f"⚠️  Failed to search memories: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: Memory ID to delete
        
        Returns:
            True if deleted, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"⚠️  Failed to delete memory: {e}")
            return False
    
    def delete_all_memories(self) -> int:
        """
        Delete all memories.
        
        Returns:
            Number of memories deleted (approximate)
        """
        if not self.is_available():
            return 0
        
        try:
            # Get all IDs
            all_data = self.collection.get()
            if all_data['ids']:
                count = len(all_data['ids'])
                self.collection.delete(ids=all_data['ids'])
                return count
            return 0
        except Exception as e:
            print(f"⚠️  Failed to delete all memories: {e}")
            return 0
    
    def get_collection_count(self) -> int:
        """Get total number of memories in collection."""
        if not self.is_available():
            return 0
        
        try:
            all_data = self.collection.get()
            return len(all_data['ids']) if all_data['ids'] else 0
        except Exception:
            return 0
    
    def get_memory(self, memory_id: str) -> Optional[Dict]:
        """
        Get a single memory by ID.
        
        Args:
            memory_id: Memory ID to retrieve
            
        Returns:
            Memory dictionary or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            results = self.collection.get(ids=[memory_id])
            if results['ids'] and len(results['ids']) > 0:
                idx = 0
                return {
                    "id": results['ids'][idx],
                    "text": results['documents'][idx] if results['documents'] else "",
                    "metadata": results['metadatas'][idx] if results['metadatas'] else {}
                }
            return None
        except Exception as e:
            print(f"⚠️  Failed to get memory: {e}")
            return None
    
    def get_all_memories(self) -> List[Dict]:
        """
        Get all memories from the collection.
        
        Returns:
            List of all memories
        """
        if not self.is_available():
            return []
        
        try:
            all_data = self.collection.get()
            memories = []
            if all_data['ids']:
                for i in range(len(all_data['ids'])):
                    memory = {
                        "id": all_data['ids'][i],
                        "text": all_data['documents'][i] if all_data['documents'] else "",
                        "metadata": all_data['metadatas'][i] if all_data['metadatas'] else {}
                    }
                    memories.append(memory)
            return memories
        except Exception as e:
            print(f"⚠️  Failed to get all memories: {e}")
            return []
    
    def update_metadata(self, memory_id: str, metadata: Dict) -> bool:
        """
        Update metadata for a memory.
        
        Note: ChromaDB doesn't support direct metadata updates, so we need to
        re-add the memory with updated metadata.
        
        Args:
            memory_id: Memory ID to update
            metadata: Updated metadata dictionary
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Get existing memory
            existing = self.get_memory(memory_id)
            if not existing:
                return False
            
            # Delete old entry
            self.collection.delete(ids=[memory_id])
            
            # Re-add with updated metadata
            self.collection.add(
                documents=[existing['text']],
                ids=[memory_id],
                metadatas=[metadata]
            )
            
            return True
        except Exception as e:
            print(f"⚠️  Failed to update metadata: {e}")
            return False

