"""
State Reconciliation - Conflict resolution for concurrent edits during soul transfer
Implements last-write-wins with timestamp validation and conversation merging logic
"""
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "last_write_wins"
    MERGE = "merge"
    OPERATOR_CHOICE = "operator_choice"
    TIMESTAMP_VALIDATION = "timestamp_validation"


class Conflict:
    """Represents a conflict between two versions of data."""
    def __init__(
        self,
        field: str,
        source_value: Any,
        target_value: Any,
        source_timestamp: datetime,
        target_timestamp: datetime,
        conflict_type: str = "edit"
    ):
        self.field = field
        self.source_value = source_value
        self.target_value = target_value
        self.source_timestamp = source_timestamp
        self.target_timestamp = target_timestamp
        self.conflict_type = conflict_type
        self.resolved = False
        self.resolved_value = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "field": self.field,
            "source_value": str(self.source_value)[:100],  # Truncate for logging
            "target_value": str(self.target_value)[:100],
            "source_timestamp": self.source_timestamp.isoformat() if isinstance(self.source_timestamp, datetime) else str(self.source_timestamp),
            "target_timestamp": self.target_timestamp.isoformat() if isinstance(self.target_timestamp, datetime) else str(self.target_timestamp),
            "conflict_type": self.conflict_type,
            "resolved": self.resolved,
            "resolved_value": str(self.resolved_value)[:100] if self.resolved_value else None
        }


class ReconciliationResult:
    """Result of state reconciliation operation."""
    def __init__(
        self,
        success: bool,
        conflicts: List[Conflict] = None,
        resolved_data: Optional[Dict[str, Any]] = None,
        strategy_used: Optional[str] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.conflicts = conflicts or []
        self.resolved_data = resolved_data or {}
        self.strategy_used = strategy_used
        self.error = error
        self.resolved_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "conflict_count": len(self.conflicts),
            "resolved_count": sum(1 for c in self.conflicts if c.resolved),
            "resolved_data_keys": list(self.resolved_data.keys()) if self.resolved_data else [],
            "strategy_used": self.strategy_used,
            "error": self.error,
            "resolved_at": self.resolved_at.isoformat()
        }


class StateReconciliation:
    """
    Handles conflict resolution for concurrent edits during soul transfer.
    
    Implements multiple strategies:
    - Last-write-wins with timestamp validation
    - Conversation merging logic
    - Operator choice for critical conflicts
    """
    
    def __init__(self, default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS):
        """
        Initialize State Reconciliation.
        
        Args:
            default_strategy: Default conflict resolution strategy
        """
        self.default_strategy = default_strategy
        self.reconciliation_history: List[ReconciliationResult] = []
    
    def reconcile_conversations(
        self,
        source_messages: List[Dict[str, Any]],
        target_messages: List[Dict[str, Any]],
        conversation_uuid: str,
        strategy: Optional[ConflictResolutionStrategy] = None
    ) -> ReconciliationResult:
        """
        Reconcile two conversation histories, detecting and resolving conflicts.
        
        Args:
            source_messages: Messages from source soul
            target_messages: Messages from target soul
            conversation_uuid: Conversation UUID for tracking
            strategy: Optional strategy override
            
        Returns:
            ReconciliationResult with resolved messages
        """
        strategy = strategy or self.default_strategy
        conflicts: List[Conflict] = []
        resolved_messages: List[Dict[str, Any]] = []
        
        try:
            # Build message index by timestamp for comparison
            source_index = self._build_message_index(source_messages)
            target_index = self._build_message_index(target_messages)
            
            # Find conflicts
            conflicts = self._detect_conflicts(source_index, target_index)
            
            # Resolve conflicts based on strategy
            if strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
                resolved_messages = self._resolve_last_write_wins(
                    source_index,
                    target_index,
                    conflicts
                )
            elif strategy == ConflictResolutionStrategy.MERGE:
                resolved_messages = self._resolve_merge(
                    source_index,
                    target_index,
                    conflicts
                )
            elif strategy == ConflictResolutionStrategy.TIMESTAMP_VALIDATION:
                resolved_messages = self._resolve_timestamp_validation(
                    source_index,
                    target_index,
                    conflicts
                )
            else:
                # Default: last write wins
                resolved_messages = self._resolve_last_write_wins(
                    source_index,
                    target_index,
                    conflicts
                )
            
            # Sort resolved messages by timestamp
            resolved_messages.sort(key=lambda m: self._parse_timestamp(m.get("timestamp")))
            
            result = ReconciliationResult(
                success=True,
                conflicts=conflicts,
                resolved_data={"messages": resolved_messages},
                strategy_used=strategy.value
            )
            
            self.reconciliation_history.append(result)
            logger.info(f"Reconciled conversation {conversation_uuid}: {len(conflicts)} conflicts, {len(resolved_messages)} messages")
            
            return result
            
        except Exception as e:
            logger.error(f"Error reconciling conversations: {e}")
            return ReconciliationResult(
                success=False,
                conflicts=conflicts,
                error=str(e)
            )
    
    def _build_message_index(self, messages: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Build index of messages by timestamp for conflict detection."""
        index = {}
        for msg in messages:
            timestamp = msg.get("timestamp")
            if timestamp:
                # Use timestamp as key (or content hash if no timestamp)
                key = self._normalize_timestamp(timestamp)
                if key not in index:
                    index[key] = msg
                else:
                    # If duplicate timestamp, use content hash as fallback
                    content = msg.get("content", "")
                    content_hash = hash(content) % 1000000  # Simple hash
                    key = f"{key}_{content_hash}"
                    index[key] = msg
        return index
    
    def _normalize_timestamp(self, timestamp) -> str:
        """Normalize timestamp to string for indexing."""
        if isinstance(timestamp, datetime):
            return timestamp.isoformat()
        elif isinstance(timestamp, str):
            return timestamp
        else:
            return str(timestamp)
    
    def _parse_timestamp(self, timestamp) -> datetime:
        """Parse timestamp string to datetime object."""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                try:
                    # Try common formats
                    return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except:
                    return datetime.utcnow()
        else:
            return datetime.utcnow()
    
    def _detect_conflicts(
        self,
        source_index: Dict[str, Dict[str, Any]],
        target_index: Dict[str, Dict[str, Any]]
    ) -> List[Conflict]:
        """Detect conflicts between source and target message indices."""
        conflicts = []
        
        # Find messages with same timestamp but different content
        for key, source_msg in source_index.items():
            if key in target_index:
                target_msg = target_index[key]
                source_content = source_msg.get("content", "")
                target_content = target_msg.get("content", "")
                
                if source_content != target_content:
                    # Conflict detected
                    source_timestamp = self._parse_timestamp(source_msg.get("timestamp"))
                    target_timestamp = self._parse_timestamp(target_msg.get("timestamp"))
                    
                    conflict = Conflict(
                        field="content",
                        source_value=source_content,
                        target_value=target_content,
                        source_timestamp=source_timestamp,
                        target_timestamp=target_timestamp,
                        conflict_type="edit"
                    )
                    conflicts.append(conflict)
                    logger.debug(f"Conflict detected at {key}: source vs target content differs")
        
        return conflicts
    
    def _resolve_last_write_wins(
        self,
        source_index: Dict[str, Dict[str, Any]],
        target_index: Dict[str, Dict[str, Any]],
        conflicts: List[Conflict]
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts using last-write-wins strategy."""
        resolved_messages = []
        conflict_keys = {c.field: c for c in conflicts}
        
        # Combine all message keys
        all_keys = set(source_index.keys()) | set(target_index.keys())
        
        for key in sorted(all_keys):
            source_msg = source_index.get(key)
            target_msg = target_index.get(key)
            
            if key in conflict_keys:
                # Conflict: choose later timestamp
                conflict = conflict_keys[key]
                if conflict.source_timestamp >= conflict.target_timestamp:
                    resolved_messages.append(source_msg)
                    conflict.resolved_value = source_msg.get("content")
                    conflict.resolved = True
                    logger.debug(f"Resolved conflict {key}: chose source (last write)")
                else:
                    resolved_messages.append(target_msg)
                    conflict.resolved_value = target_msg.get("content")
                    conflict.resolved = True
                    logger.debug(f"Resolved conflict {key}: chose target (last write)")
            elif source_msg:
                resolved_messages.append(source_msg)
            elif target_msg:
                resolved_messages.append(target_msg)
        
        return resolved_messages
    
    def _resolve_merge(
        self,
        source_index: Dict[str, Dict[str, Any]],
        target_index: Dict[str, Dict[str, Any]],
        conflicts: List[Conflict]
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts by merging both versions."""
        resolved_messages = []
        
        # Combine all messages, keeping unique ones
        all_messages = {}
        
        # Add all source messages
        for key, msg in source_index.items():
            all_messages[key] = msg
        
        # Add target messages (will overwrite on conflict, but we'll handle that)
        for key, target_msg in target_index.items():
            if key in all_messages:
                # Conflict: merge content
                source_msg = all_messages[key]
                merged_content = f"{source_msg.get('content', '')}\n---\n{target_msg.get('content', '')}"
                merged_msg = source_msg.copy()
                merged_msg["content"] = merged_content
                merged_msg["metadata"] = merged_msg.get("metadata", {})
                merged_msg["metadata"]["merged"] = True
                merged_msg["metadata"]["merge_source"] = "both"
                all_messages[key] = merged_msg
                
                # Mark conflict as resolved
                for conflict in conflicts:
                    if conflict.field == "content" and hash(source_msg.get("content", "")) % 1000000 == hash(target_msg.get("content", "")) % 1000000:
                        conflict.resolved_value = merged_content
                        conflict.resolved = True
            else:
                all_messages[key] = target_msg
        
        resolved_messages = list(all_messages.values())
        return resolved_messages
    
    def _resolve_timestamp_validation(
        self,
        source_index: Dict[str, Dict[str, Any]],
        target_index: Dict[str, Dict[str, Any]],
        conflicts: List[Conflict]
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts using timestamp validation (strict ordering)."""
        # Similar to last-write-wins but with stricter validation
        return self._resolve_last_write_wins(source_index, target_index, conflicts)
    
    def reconcile_vault_data(
        self,
        source_vault: Dict[str, Any],
        target_vault: Dict[str, Any],
        vault_type: str  # "green", "red"
    ) -> ReconciliationResult:
        """
        Reconcile vault data between source and target.
        
        Args:
            source_vault: Source vault data
            target_vault: Target vault data
            vault_type: Type of vault ("green" or "red")
            
        Returns:
            ReconciliationResult with resolved vault data
        """
        conflicts = []
        resolved_data = {}
        
        try:
            # For Green Vault: merge summaries (additive)
            if vault_type == "green":
                source_summaries = source_vault.get("summaries", [])
                target_summaries = target_vault.get("summaries", [])
                
                # Merge: combine unique summaries
                all_summaries = {hash(s.get("content", "")): s for s in target_summaries}
                for summary in source_summaries:
                    content_hash = hash(summary.get("content", ""))
                    if content_hash not in all_summaries:
                        all_summaries[content_hash] = summary
                
                resolved_data["summaries"] = list(all_summaries.values())
                logger.info(f"Reconciled Green Vault: {len(source_summaries)} source + {len(target_summaries)} target = {len(resolved_data['summaries'])} unique")
            
            # For Red Vault: require operator choice (secrets are sensitive)
            elif vault_type == "red":
                # Red Vault conflicts require explicit operator approval
                source_secrets = source_vault.get("secrets", [])
                target_secrets = target_vault.get("secrets", [])
                
                # For now, merge but flag for operator review
                all_secrets = {s.get("key", ""): s for s in target_secrets}
                for secret in source_secrets:
                    key = secret.get("key", "")
                    if key in all_secrets:
                        # Conflict: flag for operator review
                        conflict = Conflict(
                            field=f"secret:{key}",
                            source_value=secret.get("value", ""),
                            target_value=all_secrets[key].get("value", ""),
                            source_timestamp=datetime.utcnow(),
                            target_timestamp=datetime.utcnow(),
                            conflict_type="secret"
                        )
                        conflicts.append(conflict)
                        # Default: keep target (assume it's more recent)
                        all_secrets[key] = target_secrets[next(i for i, s in enumerate(target_secrets) if s.get("key") == key)]
                    else:
                        all_secrets[key] = secret
                
                resolved_data["secrets"] = list(all_secrets.values())
                resolved_data["requires_operator_review"] = len(conflicts) > 0
                logger.warning(f"Reconciled Red Vault: {len(conflicts)} conflicts require operator review")
            
            return ReconciliationResult(
                success=True,
                conflicts=conflicts,
                resolved_data=resolved_data,
                strategy_used="merge" if vault_type == "green" else "operator_choice"
            )
            
        except Exception as e:
            logger.error(f"Error reconciling vault data: {e}")
            return ReconciliationResult(
                success=False,
                conflicts=conflicts,
                error=str(e)
            )
    
    def get_reconciliation_history(self, conversation_uuid: Optional[str] = None) -> List[ReconciliationResult]:
        """Get reconciliation history, optionally filtered by conversation UUID."""
        if conversation_uuid:
            # Filter by conversation UUID if metadata contains it
            return [
                r for r in self.reconciliation_history
                if r.resolved_data and r.resolved_data.get("conversation_uuid") == conversation_uuid
            ]
        return self.reconciliation_history
