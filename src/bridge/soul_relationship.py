"""
Soul Relationship Tracking - Track relationship state between Constitutional and Networked Souls
Tracks sync history, shared knowledge, personality divergence metrics, and relationship patterns
over time as souls develop their relationship through knowledge exchange.
"""
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass, field

from .state_reconciliation import Conflict

logger = logging.getLogger(__name__)


@dataclass
class SyncRecord:
    """Record of a single synchronization event between souls."""
    timestamp: datetime
    direction: str  # "constitutional→networked" or "networked→constitutional"
    conversation_uuid: str
    categories_transferred: List[str]  # ["memory", "inference", "capabilities", "tone"]
    size_bytes: int
    duration_seconds: float
    merge_conflicts: List[Conflict] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "direction": self.direction,
            "conversation_uuid": self.conversation_uuid,
            "categories_transferred": self.categories_transferred,
            "size_bytes": self.size_bytes,
            "duration_seconds": self.duration_seconds,
            "merge_conflicts": [c.to_dict() for c in self.merge_conflicts],
            "conflict_count": len(self.merge_conflicts),
            "success": self.success,
            "error": self.error
        }


class SoulRelationship:
    """
    Tracks how the two souls (Constitutional and Networked) develop their relationship over time.
    
    Maintains:
    - Sync history (all transfer events)
    - Shared knowledge (what both souls know)
    - Personality divergence metrics (how different they've become)
    - Inside jokes (references only they understand)
    - Conflict history (resolved and unresolved conflicts)
    """
    
    def __init__(self):
        """Initialize Soul Relationship tracker."""
        self.sync_history: List[SyncRecord] = []
        self.shared_knowledge: Dict[str, Any] = {
            "green_vault_intersection": [],  # Green Vault entries both souls have
            "inference_patterns": {},  # Shared inference shortcuts
            "capability_understanding": {},  # Common capability knowledge
            "relationship_context": []  # References to past syncs
        }
        self.personality_divergence: float = 0.0  # 0.0 = identical, 1.0 = very different
        self.inside_jokes: List[str] = []  # References only they understand
        self.conflict_history: List[Conflict] = []
        self.last_sync_timestamp: Optional[datetime] = None
    
    def record_sync(self, sync_record: SyncRecord) -> None:
        """
        Record a synchronization event between souls.
        
        Args:
            sync_record: SyncRecord with details of the sync event
        """
        self.sync_history.append(sync_record)
        self.last_sync_timestamp = sync_record.timestamp
        
        # Update shared knowledge based on sync
        if sync_record.success:
            # Add to shared knowledge if successfully transferred
            for category in sync_record.categories_transferred:
                if category not in self.shared_knowledge:
                    self.shared_knowledge[category] = []
                # Mark category as shared (details would come from actual sync data)
                if category not in self.shared_knowledge.get("relationship_context", []):
                    self.shared_knowledge.setdefault("relationship_context", []).append({
                        "category": category,
                        "synced_at": sync_record.timestamp.isoformat(),
                        "conversation_uuid": sync_record.conversation_uuid
                    })
        
        # Record conflicts if any
        if sync_record.merge_conflicts:
            self.conflict_history.extend(sync_record.merge_conflicts)
            logger.info(f"Recorded {len(sync_record.merge_conflicts)} conflicts from sync at {sync_record.timestamp}")
        
        # Update divergence score after sync
        self.personality_divergence = self.calculate_divergence()
        
        logger.info(f"Recorded sync: {sync_record.direction} at {sync_record.timestamp}, "
                   f"{len(sync_record.categories_transferred)} categories, "
                   f"{sync_record.size_bytes} bytes, "
                   f"{len(sync_record.merge_conflicts)} conflicts")
    
    def calculate_divergence(self) -> float:
        """
        Calculate personality divergence score between souls.
        
        Returns:
            Float between 0.0 (identical) and 1.0 (very different)
            
        Factors:
        - Number of conflicts (more conflicts = more divergence)
        - Time since last sync (longer = more divergence)
        - Different inference patterns
        - Different capability understanding
        """
        if not self.sync_history:
            # No syncs yet, assume they start identical
            return 0.0
        
        divergence_factors = []
        
        # Factor 1: Conflict frequency
        total_conflicts = len(self.conflict_history)
        total_syncs = len(self.sync_history)
        if total_syncs > 0:
            conflict_rate = min(total_conflicts / total_syncs, 1.0)  # Cap at 1.0
            divergence_factors.append(conflict_rate * 0.4)  # 40% weight
        
        # Factor 2: Time since last sync (assumes divergence increases with time)
        if self.last_sync_timestamp:
            time_since_sync = (datetime.utcnow() - self.last_sync_timestamp).total_seconds()
            # Normalize: 1 week = 0.5 divergence, 1 month = 1.0 divergence
            days_since_sync = time_since_sync / (24 * 3600)
            time_divergence = min(days_since_sync / 30.0, 1.0)  # Cap at 1.0
            divergence_factors.append(time_divergence * 0.3)  # 30% weight
        else:
            divergence_factors.append(0.0)
        
        # Factor 3: Number of unique inference patterns (if we track them)
        # This is a placeholder - actual implementation would compare pattern sets
        pattern_divergence = 0.0
        if "inference_patterns" in self.shared_knowledge:
            # In real implementation, compare source vs target patterns
            pattern_divergence = 0.2  # Placeholder
        divergence_factors.append(pattern_divergence * 0.3)  # 30% weight
        
        # Calculate weighted average
        total_divergence = sum(divergence_factors)
        return min(total_divergence, 1.0)  # Cap at 1.0
    
    def get_shared_context(self) -> Dict[str, Any]:
        """
        Get shared context that both souls understand.
        
        Returns:
            Dictionary containing:
            - Knowledge both souls have (Green Vault intersection)
            - Shared inference patterns
            - Common capability understanding
            - Relationship-specific context (references to past syncs)
        """
        return {
            "green_vault_intersection": self.shared_knowledge.get("green_vault_intersection", []),
            "inference_patterns": self.shared_knowledge.get("inference_patterns", {}),
            "capability_understanding": self.shared_knowledge.get("capability_understanding", {}),
            "relationship_context": self.shared_knowledge.get("relationship_context", []),
            "sync_count": len(self.sync_history),
            "inside_jokes_count": len(self.inside_jokes),
            "personality_divergence": self.personality_divergence,
            "last_sync": self.last_sync_timestamp.isoformat() if self.last_sync_timestamp else None
        }
    
    def detect_relationship_patterns(self) -> List[str]:
        """
        Detect patterns in the relationship between souls.
        
        Returns:
            List of pattern descriptions, e.g.:
            - "Souls have synced 5 times, developing shared understanding"
            - "High conflict rate suggests growing divergence"
            - "Frequent syncs indicate active relationship"
        """
        patterns = []
        
        if not self.sync_history:
            patterns.append("No syncs yet - relationship just beginning")
            return patterns
        
        total_syncs = len(self.sync_history)
        successful_syncs = sum(1 for s in self.sync_history if s.success)
        
        # Pattern: Sync frequency
        if total_syncs >= 5:
            patterns.append(f"Souls have synced {total_syncs} times, developing shared understanding")
        elif total_syncs >= 2:
            patterns.append(f"Souls have synced {total_syncs} times, relationship forming")
        else:
            patterns.append(f"Souls have synced {total_syncs} time, relationship just beginning")
        
        # Pattern: Success rate
        success_rate = successful_syncs / total_syncs if total_syncs > 0 else 0.0
        if success_rate >= 0.9:
            patterns.append("High success rate - smooth knowledge exchange")
        elif success_rate >= 0.7:
            patterns.append("Moderate success rate - some transfer issues")
        else:
            patterns.append("Low success rate - frequent transfer problems")
        
        # Pattern: Conflict rate
        total_conflicts = len(self.conflict_history)
        if total_syncs > 0:
            conflict_rate = total_conflicts / total_syncs
            if conflict_rate > 0.5:
                patterns.append("High conflict rate suggests growing divergence")
            elif conflict_rate > 0.2:
                patterns.append("Moderate conflicts - some differences in knowledge")
            else:
                patterns.append("Low conflict rate - souls remain aligned")
        
        # Pattern: Divergence
        if self.personality_divergence > 0.7:
            patterns.append("High divergence - souls developing distinct personalities")
        elif self.personality_divergence > 0.4:
            patterns.append("Moderate divergence - souls showing some differences")
        elif self.personality_divergence > 0.1:
            patterns.append("Low divergence - souls remain similar")
        else:
            patterns.append("Very low divergence - souls closely aligned")
        
        # Pattern: Time since last sync
        if self.last_sync_timestamp:
            days_since = (datetime.utcnow() - self.last_sync_timestamp).days
            if days_since > 30:
                patterns.append(f"Last sync was {days_since} days ago - relationship may be dormant")
            elif days_since > 7:
                patterns.append(f"Last sync was {days_since} days ago - infrequent contact")
            elif days_since > 1:
                patterns.append(f"Last sync was {days_since} days ago - regular contact")
            else:
                patterns.append("Recent sync - active relationship")
        
        # Pattern: Inside jokes
        if len(self.inside_jokes) > 0:
            patterns.append(f"{len(self.inside_jokes)} inside joke(s) - shared cultural understanding")
        
        return patterns
    
    def get_sync_history(self, limit: Optional[int] = None) -> List[SyncRecord]:
        """
        Get sync history, optionally limited to most recent N records.
        
        Args:
            limit: Optional limit on number of records to return
            
        Returns:
            List of SyncRecord objects, most recent first
        """
        history = sorted(self.sync_history, key=lambda s: s.timestamp, reverse=True)
        if limit:
            return history[:limit]
        return history
    
    def get_conflict_history(self, unresolved_only: bool = False) -> List[Conflict]:
        """
        Get conflict history, optionally filtered to unresolved conflicts only.
        
        Args:
            unresolved_only: If True, return only unresolved conflicts
            
        Returns:
            List of Conflict objects
        """
        if unresolved_only:
            return [c for c in self.conflict_history if not c.resolved]
        return self.conflict_history
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship state to dictionary for serialization."""
        return {
            "sync_history": [s.to_dict() for s in self.sync_history],
            "sync_count": len(self.sync_history),
            "shared_knowledge": self.shared_knowledge,
            "personality_divergence": self.personality_divergence,
            "inside_jokes": self.inside_jokes,
            "conflict_count": len(self.conflict_history),
            "unresolved_conflicts": len([c for c in self.conflict_history if not c.resolved]),
            "last_sync_timestamp": self.last_sync_timestamp.isoformat() if self.last_sync_timestamp else None,
            "relationship_patterns": self.detect_relationship_patterns()
        }
