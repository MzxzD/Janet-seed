"""
Learning Audit Logger - Transparent logging of all learning operations
Ensures full audit trail for constitutional compliance
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json


class LearningAuditLogger:
    """Logs all learning operations for transparency and audit."""
    
    def __init__(self, audit_dir: Path):
        """
        Initialize learning audit logger.
        
        Args:
            audit_dir: Directory for audit logs
        """
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.audit_dir / "learning_audit.jsonl"
    
    def log_operation(
        self,
        operation_type: str,
        data_used: List[str],
        results: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a learning operation.
        
        Args:
            operation_type: Type of operation (e.g., "fine-tuning", "behavior_adaptation")
            data_used: List of summary IDs used in the operation
            results: Optional results/outcomes of the operation
            metadata: Optional additional metadata
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation_type": operation_type,
            "data_used": {
                "summary_ids": data_used,
                "count": len(data_used)
            },
            "results": results or {},
            "metadata": metadata or {}
        }
        
        try:
            # Append to JSONL file
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"⚠️  Failed to log learning operation: {e}")
    
    def get_audit_history(
        self,
        limit: Optional[int] = None,
        operation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit history.
        
        Args:
            limit: Maximum number of entries to return
            operation_type: Filter by operation type (optional)
            
        Returns:
            List of audit log entries
        """
        if not self.audit_file.exists():
            return []
        
        try:
            entries = []
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if operation_type is None or entry.get("operation_type") == operation_type:
                            entries.append(entry)
            
            # Sort by timestamp (newest first)
            entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            if limit:
                entries = entries[:limit]
            
            return entries
        except Exception as e:
            print(f"⚠️  Failed to read audit history: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about learning operations.
        
        Returns:
            Dictionary with learning statistics
        """
        all_entries = self.get_audit_history()
        
        if not all_entries:
            return {
                "total_operations": 0,
                "operations_by_type": {},
                "total_summaries_used": 0,
                "unique_summaries_used": set(),
                "first_operation": None,
                "last_operation": None
            }
        
        operations_by_type = {}
        all_summary_ids = set()
        
        for entry in all_entries:
            op_type = entry.get("operation_type", "unknown")
            operations_by_type[op_type] = operations_by_type.get(op_type, 0) + 1
            
            data_used = entry.get("data_used", {})
            summary_ids = data_used.get("summary_ids", [])
            all_summary_ids.update(summary_ids)
        
        return {
            "total_operations": len(all_entries),
            "operations_by_type": operations_by_type,
            "total_summaries_used": sum(
                len(e.get("data_used", {}).get("summary_ids", []))
                for e in all_entries
            ),
            "unique_summaries_used": len(all_summary_ids),
            "first_operation": all_entries[-1].get("timestamp") if all_entries else None,
            "last_operation": all_entries[0].get("timestamp") if all_entries else None
        }

