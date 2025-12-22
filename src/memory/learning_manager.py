"""
Learning Manager - Manages learning operations from Green Vault
Ensures constitutional compliance: only Green Vault summaries used, with explicit consent
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    RED_THREAD_EVENT = None


class LearningManager:
    """Manages learning operations from Green Vault with consent and audit."""
    
    def __init__(self, green_vault, audit_logger=None):
        """
        Initialize learning manager.
        
        Args:
            green_vault: GreenVault instance
            audit_logger: LearningAuditLogger instance (optional)
        """
        self.green_vault = green_vault
        self.audit_logger = audit_logger
    
    def get_training_data(
        self,
        limit: Optional[int] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch Green Vault summaries for training.
        
        Only returns summaries that:
        - Have explicit consent for learning
        - Are not opted out
        - Are from Green Vault (never Blue or Red)
        
        Args:
            limit: Maximum number of summaries to return
            exclude_ids: List of summary IDs to exclude
            
        Returns:
            List of training data dictionaries with summaries and metadata
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - learning blocked")
            return []
        
        if exclude_ids is None:
            exclude_ids = []
        
        # Get training data from Green Vault
        training_data = self.green_vault.get_training_data(limit, exclude_ids)
        
        # Filter to only include summaries with consent and not opted out
        filtered_data = []
        for entry in training_data:
            if self.can_learn_from(entry.get("id")):
                filtered_data.append(entry)
        
        return filtered_data
    
    def request_consent(self, data_summary: Dict[str, Any]) -> bool:
        """
        Request explicit consent before learning.
        
        Args:
            data_summary: Summary of data that would be used for learning
            
        Returns:
            True if consent granted, False otherwise
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - consent request blocked")
            return False
        
        # This should be called by UI/wizard to get user consent
        # For now, return False (requires explicit consent via UI)
        return False
    
    def opt_out_summary(self, entry_id: str) -> bool:
        """
        Mark summary as excluded from training.
        
        Args:
            entry_id: ID of summary to opt out
            
        Returns:
            True if opt-out successful, False otherwise
        """
        # Axiom 8: Red Thread Protocol
        if RED_THREAD_EVENT and RED_THREAD_EVENT.is_set():
            print("🔴 Red Thread active - opt-out blocked")
            return False
        
        return self.green_vault.opt_out_summary(entry_id)
    
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
        
        return self.green_vault.grant_consent(entry_id)
    
    def can_learn_from(self, entry_id: str) -> bool:
        """
        Check if summary can be used for learning.
        
        Args:
            entry_id: ID of summary to check
            
        Returns:
            True if summary can be used (has consent and not opted out), False otherwise
        """
        if not entry_id:
            return False
        
        # Get summary metadata
        summary = self.green_vault.get_summary(entry_id)
        if not summary:
            return False
        
        metadata = summary.get("metadata", {})
        
        # Check consent
        has_consent = metadata.get("consent_for_learning", False)
        
        # Check opt-out
        is_opted_out = metadata.get("opted_out_from_learning", False)
        
        return has_consent and not is_opted_out
    
    def audit_learning_operation(
        self,
        operation_type: str,
        data_used: List[str],
        results: Optional[Dict[str, Any]] = None
    ):
        """
        Log learning operation for audit trail.
        
        Args:
            operation_type: Type of learning operation (e.g., "fine-tuning", "behavior_adaptation")
            data_used: List of summary IDs used in learning
            results: Optional results/outcomes of the operation
        """
        if self.audit_logger:
            self.audit_logger.log_operation(
                operation_type=operation_type,
                data_used=data_used,
                results=results
            )
    
    def get_consent_status(self, entry_id: str) -> Dict[str, bool]:
        """
        Get consent and opt-out status for a summary.
        
        Args:
            entry_id: ID of summary to check
            
        Returns:
            Dictionary with consent and opt-out status
        """
        summary = self.green_vault.get_summary(entry_id)
        if not summary:
            return {"has_consent": False, "is_opted_out": False, "exists": False}
        
        metadata = summary.get("metadata", {})
        return {
            "exists": True,
            "has_consent": metadata.get("consent_for_learning", False),
            "is_opted_out": metadata.get("opted_out_from_learning", False)
        }
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about learning data availability.
        
        Returns:
            Dictionary with learning statistics
        """
        # Get all summaries
        all_summaries = self.green_vault.get_all_summaries()
        
        total = len(all_summaries)
        with_consent = 0
        opted_out = 0
        available = 0
        
        for summary in all_summaries:
            metadata = summary.get("metadata", {})
            if metadata.get("consent_for_learning", False):
                with_consent += 1
            if metadata.get("opted_out_from_learning", False):
                opted_out += 1
            if self.can_learn_from(summary.get("id")):
                available += 1
        
        return {
            "total_summaries": total,
            "with_consent": with_consent,
            "opted_out": opted_out,
            "available_for_learning": available,
            "pending_consent": total - with_consent - opted_out
        }

