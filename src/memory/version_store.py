"""
JBJanet Version Store - Append-only event log for Green Vault mutations.
Project JBJanet: Janet's Git-Like Versioned Database.

Records add/delete/update operations for summaries and shortcuts.
Provides undo_last() and configurable retention.
"""
import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta


class VersionStore:
    """
    Append-only event log for Green Vault mutations.
    Enables undo and audit trail (Axiom 2 User Sovereignty, Axiom 3 Transparency).
    """

    def __init__(
        self,
        memory_dir: Path,
        retention_days: int = 30,
    ):
        """
        Initialize VersionStore.

        Args:
            memory_dir: Directory for version_events database
            retention_days: Days to retain events; older events pruned (default 30)
        """
        self.memory_dir = Path(memory_dir)
        self.retention_days = retention_days
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to create VersionStore directory {self.memory_dir}: {e}")

        self.db_path = self.memory_dir / "version_events.db"
        self._init_database()

    def _init_database(self) -> None:
        """Create version_events table if not exists."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS version_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        entity_id TEXT,
                        payload_before TEXT,
                        payload_after TEXT,
                        checksum TEXT
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_version_events_timestamp
                    ON version_events(timestamp)
                """)
                conn.commit()
        except sqlite3.Error as e:
            print(f"⚠️  Failed to initialize VersionStore database: {e}")
            raise

    def _checksum(self, payload: Optional[str]) -> str:
        """Compute checksum for payload integrity."""
        if payload is None or payload == "":
            return ""
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record_event(
        self,
        operation: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        payload_before: Optional[Dict[str, Any]] = None,
        payload_after: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Append an event to the log.

        Args:
            operation: add, delete, or update
            entity_type: summary or shortcut
            entity_id: ID of the entity (entry_id)
            payload_before: State before (for delete: the deleted data; for update: old state)
            payload_after: State after (for add: the added data; for update: new state)

        Returns:
            Event ID if recorded, None on failure
        """
        if operation not in ("add", "delete", "update"):
            return None
        if entity_type not in ("summary", "shortcut"):
            return None

        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            before_str = json.dumps(payload_before) if payload_before is not None else None
            after_str = json.dumps(payload_after) if payload_after is not None else None
            checksum = self._checksum(before_str or "") + ":" + self._checksum(after_str or "")

            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO version_events
                    (timestamp, operation, entity_type, entity_id, payload_before, payload_after, checksum)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, operation, entity_type, entity_id or "", before_str, after_str, checksum))
                event_id = cursor.lastrowid
                conn.commit()
                return event_id
        except sqlite3.Error as e:
            print(f"⚠️  VersionStore record_event failed: {e}")
            return None

    def get_last_events(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the last n events (most recent first).

        Args:
            n: Number of events to return

        Returns:
            List of event dicts with id, timestamp, operation, entity_type, entity_id, payload_before, payload_after
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, timestamp, operation, entity_type, entity_id, payload_before, payload_after
                    FROM version_events
                    ORDER BY id DESC
                    LIMIT ?
                """, (n,))
                rows = cursor.fetchall()
                events = []
                for row in rows:
                    payload_before = json.loads(row["payload_before"]) if row["payload_before"] else None
                    payload_after = json.loads(row["payload_after"]) if row["payload_after"] else None
                    events.append({
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "operation": row["operation"],
                        "entity_type": row["entity_type"],
                        "entity_id": row["entity_id"] or None,
                        "payload_before": payload_before,
                        "payload_after": payload_after,
                    })
                return events
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"⚠️  VersionStore get_last_events failed: {e}")
            return []

    def prune_old_events(self) -> int:
        """
        Remove events older than retention_days.

        Returns:
            Number of events pruned
        """
        try:
            cutoff = (datetime.utcnow() - timedelta(days=self.retention_days)).isoformat() + "Z"
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM version_events WHERE timestamp < ?", (cutoff,))
                count = cursor.fetchone()[0]
                cursor.execute("DELETE FROM version_events WHERE timestamp < ?", (cutoff,))
                conn.commit()
                if count > 0:
                    print(f"📋 VersionStore: Pruned {count} events older than {self.retention_days} days")
                return count
        except sqlite3.Error as e:
            print(f"⚠️  VersionStore prune_old_events failed: {e}")
            return 0
