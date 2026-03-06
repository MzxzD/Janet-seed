"""
JBJanet Snapshot Manager - Green Vault snapshots for backup and restore.
Project JBJanet: Janet's Git-Like Versioned Database.

Creates timestamped snapshots of SQLite + ChromaDB, supports restore.
NAS-friendly: snapshots can be stored under /volume1/janet/backups.
"""
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class SnapshotManager:
    """
    Create and restore Green Vault snapshots.
    Snapshots are timestamped directories containing SQLite copy and ChromaDB copy.
    """

    SNAPSHOT_DIRNAME = "snapshots"
    EPISODIC_FILENAME = "episodic_snapshot.db"
    CHROMADB_DIRNAME = "chromadb_snapshot"
    MANIFEST_FILENAME = "manifest.json"
    DEFAULT_RETENTION_DAILY = 7
    DEFAULT_RETENTION_WEEKLY = 4

    def __init__(
        self,
        memory_dir: Path,
        snapshot_path: Optional[Path] = None,
        retention_daily: int = DEFAULT_RETENTION_DAILY,
        retention_weekly: int = DEFAULT_RETENTION_WEEKLY,
    ):
        """
        Initialize SnapshotManager.

        Args:
            memory_dir: Green Vault directory (contains green_vault.db, green_vault_chromadb/)
            snapshot_path: Where to store snapshots (default: memory_dir/snapshots)
            retention_daily: Keep last N daily snapshots
            retention_weekly: Keep last N weekly snapshots (for future use)
        """
        self.memory_dir = Path(memory_dir)
        self.snapshot_path = Path(snapshot_path) if snapshot_path else self.memory_dir / self.SNAPSHOT_DIRNAME
        self.retention_daily = retention_daily
        self.retention_weekly = retention_weekly

        self.sqlite_path = self.memory_dir / "green_vault.db"
        self.chromadb_path = self.memory_dir / "green_vault_chromadb"

    def _file_checksum(self, path: Path) -> str:
        """Compute SHA-256 of file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _dir_checksum(self, path: Path) -> str:
        """Compute combined checksum of all files in directory (order-independent)."""
        if not path.exists():
            return ""
        h = hashlib.sha256()
        for p in sorted(path.rglob("*")):
            if p.is_file():
                h.update(str(p.relative_to(path)).encode())
                h.update(self._file_checksum(p).encode())
        return h.hexdigest()

    def create_snapshot(self) -> Optional[str]:
        """
        Create a new snapshot of Green Vault.

        Returns:
            Snapshot ID (directory name) if successful, None otherwise
        """
        if not self.sqlite_path.exists():
            print("⚠️  SnapshotManager: green_vault.db not found")
            return None

        snapshot_id = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
        snapshot_dir = self.snapshot_path / snapshot_id

        try:
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            episodic_dest = snapshot_dir / self.EPISODIC_FILENAME
            shutil.copy2(self.sqlite_path, episodic_dest)
            episodic_checksum = self._file_checksum(episodic_dest)

            chromadb_dest = snapshot_dir / self.CHROMADB_DIRNAME
            if self.chromadb_path.exists():
                shutil.copytree(self.chromadb_path, chromadb_dest, dirs_exist_ok=True)
                chromadb_checksum = self._dir_checksum(chromadb_dest)
            else:
                chromadb_dest.mkdir(parents=True, exist_ok=True)
                chromadb_checksum = ""

            episodic_count = 0
            try:
                import sqlite3
                with sqlite3.connect(str(self.sqlite_path)) as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM episodic_memory")
                    episodic_count = c.fetchone()[0]
            except Exception:
                pass

            chromadb_count = 0
            try:
                chromadb_data = chromadb_dest / "chroma.sqlite3"
                if chromadb_data.exists():
                    with open(chromadb_data, "rb") as f:
                        chromadb_count = 1
            except Exception:
                pass

            manifest = {
                "snapshot_id": snapshot_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "episodic_count": episodic_count,
                "chromadb_count": chromadb_count,
                "checksums": {
                    "episodic_snapshot.db": episodic_checksum,
                    "chromadb_snapshot": chromadb_checksum,
                },
            }
            with open(snapshot_dir / self.MANIFEST_FILENAME, "w") as f:
                json.dump(manifest, f, indent=2)

            self._prune_old_snapshots()
            return snapshot_id
        except Exception as e:
            print(f"⚠️  SnapshotManager create_snapshot failed: {e}")
            if snapshot_dir.exists():
                shutil.rmtree(snapshot_dir, ignore_errors=True)
            return None

    def list_snapshots(self) -> List[Dict]:
        """
        List all snapshots.

        Returns:
            List of dicts with snapshot_id, created_at, episodic_count, path
        """
        if not self.snapshot_path.exists():
            return []

        snapshots = []
        for d in sorted(self.snapshot_path.iterdir(), reverse=True):
            if not d.is_dir():
                continue
            manifest_path = d / self.MANIFEST_FILENAME
            if not manifest_path.exists():
                continue
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                snapshots.append({
                    "snapshot_id": d.name,
                    "created_at": manifest.get("created_at", ""),
                    "episodic_count": manifest.get("episodic_count", 0),
                    "chromadb_count": manifest.get("chromadb_count", 0),
                    "path": str(d),
                })
            except (json.JSONDecodeError, IOError):
                pass
        return snapshots

    def restore_snapshot(self, snapshot_id: str, confirm: bool = True) -> bool:
        """
        Restore Green Vault from a snapshot.

        Args:
            snapshot_id: Snapshot directory name (e.g. 2026-03-06_12-00)
            confirm: If True, require snapshot to exist and have valid manifest.
                    Set to False when caller has already confirmed.

        Returns:
            True if restore succeeded. Caller should restart janet-seed to use restored state.
        """
        snapshot_dir = self.snapshot_path / snapshot_id
        if not snapshot_dir.exists() or not snapshot_dir.is_dir():
            print(f"⚠️  SnapshotManager: snapshot {snapshot_id} not found")
            return False

        episodic_src = snapshot_dir / self.EPISODIC_FILENAME
        chromadb_src = snapshot_dir / self.CHROMADB_DIRNAME

        if not episodic_src.exists():
            print(f"⚠️  SnapshotManager: episodic_snapshot.db not found in {snapshot_id}")
            return False

        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(episodic_src, self.sqlite_path)
            if chromadb_src.exists():
                if self.chromadb_path.exists():
                    shutil.rmtree(self.chromadb_path)
                shutil.copytree(chromadb_src, self.chromadb_path)
            return True
        except Exception as e:
            print(f"⚠️  SnapshotManager restore_snapshot failed: {e}")
            return False

    def _prune_old_snapshots(self) -> None:
        """Remove snapshots beyond retention policy."""
        snapshots = self.list_snapshots()
        if len(snapshots) <= self.retention_daily:
            return
        to_remove = snapshots[self.retention_daily:]
        for s in to_remove:
            path = Path(s["path"])
            if path.exists():
                try:
                    shutil.rmtree(path)
                except OSError as e:
                    print(f"⚠️  SnapshotManager: failed to prune {path}: {e}")
