"""
Engram-inspired conditional phrase memory for Janet (orchestration layer).

Hashes local multi-token tails (or short full utterances) for O(1) JSON-backed lookup,
with contextual gating before fusing text into the user prompt. Not the DeepSeek
in-weight Engram block — see docs/ENGRAM_MODEL_CRITERIA.md for native-model path.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from core.janet_core import RED_THREAD_EVENT
except ImportError:
    try:
        from src.core.janet_core import RED_THREAD_EVENT
    except ImportError:
        RED_THREAD_EVENT = None


def _normalize(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _hash_key(kind: str, normalized_fragment: str) -> str:
    h = hashlib.sha256(f"{kind}:{normalized_fragment}".encode("utf-8")).hexdigest()
    return h[:24]


@dataclass
class PhraseMemoryEntry:
    inject: str
    confidence: float = 0.8
    mode: str = "tail"  # "tail" | "full"
    pattern_preview: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inject": self.inject,
            "confidence": self.confidence,
            "mode": self.mode,
            "pattern_preview": self.pattern_preview,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PhraseMemoryEntry":
        return PhraseMemoryEntry(
            inject=str(d.get("inject", "")),
            confidence=float(d.get("confidence", 0.8)),
            mode=str(d.get("mode", "tail")),
            pattern_preview=str(d.get("pattern_preview", "")),
        )


@dataclass
class PhraseMemoryStats:
    lookups: int = 0
    hits: int = 0
    gated_off: int = 0


class PhraseMemory:
    """
    Local hashed lookup table + gate + prompt fuse.
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        audit_path: Optional[Path] = None,
        tail_tokens: Optional[int] = None,
        enabled: Optional[bool] = None,
    ):
        janet_home = Path(os.getenv("JANET_HOME", str(Path.home() / ".janet")))
        mem_dir = Path(os.getenv("JANET_MEMORY_DIR", str(janet_home / "memory")))
        mem_dir.mkdir(parents=True, exist_ok=True)

        self.storage_path = storage_path or (mem_dir / "phrase_memory.json")
        self.audit_path = audit_path or (mem_dir / "phrase_memory_audit.jsonl")

        if tail_tokens is None:
            tail_tokens = int(os.getenv("JANET_PHRASE_MEMORY_TAIL", "3"))
        self.tail_tokens = max(1, tail_tokens)

        if enabled is None:
            raw = os.getenv("JANET_PHRASE_MEMORY", "1").strip().lower()
            enabled = raw not in ("0", "false", "off", "no")
        self.enabled = enabled

        self._min_confidence = float(os.getenv("JANET_PHRASE_MEMORY_MIN_CONF", "0.0"))
        self._max_inject = int(os.getenv("JANET_PHRASE_MEMORY_MAX_CHARS", "4000"))

        self._lock = threading.Lock()
        self._entries: Dict[str, PhraseMemoryEntry] = {}
        self.stats = PhraseMemoryStats()
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw = data.get("entries", {})
            self._entries = {
                k: PhraseMemoryEntry.from_dict(v) for k, v in raw.items() if isinstance(v, dict)
            }
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  PhraseMemory: could not load {self.storage_path}: {e}")

    def _save_unlocked(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "entries": {k: v.to_dict() for k, v in self._entries.items()},
        }
        tmp = self.storage_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        tmp.replace(self.storage_path)

    def _audit(self, event: Dict[str, Any]) -> None:
        event = {"ts": time.time(), **event}
        try:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as e:
            print(f"⚠️  PhraseMemory audit write failed: {e}")

    def _red_thread_active(self) -> bool:
        return bool(RED_THREAD_EVENT and RED_THREAD_EVENT.is_set())

    def _gate(self, context: Optional[Dict[str, Any]], entry: PhraseMemoryEntry) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "disabled"
        if self._red_thread_active():
            return False, "red_thread"
        if context:
            if context.get("skip_context_fusion"):
                return False, "skip_context_fusion"
            if context.get("phrase_memory") is False or context.get("skip_phrase_memory"):
                return False, "context_opt_out"
        if entry.confidence < self._min_confidence:
            return False, "low_confidence"
        if not entry.inject or not entry.inject.strip():
            return False, "empty_inject"
        return True, "ok"

    def lookup_keys_for_input(self, user_input: str) -> List[Tuple[str, str]]:
        """Return list of (kind, key_id) to try in order."""
        normalized = _normalize(user_input)
        tokens = normalized.split()
        ordered: List[Tuple[str, str]] = []

        # Short utterances: prefer full-key match first
        if len(normalized) <= 256 and len(tokens) <= 24:
            ordered.append(("full", _hash_key("full", normalized)))

        if len(tokens) >= self.tail_tokens:
            tail = " ".join(tokens[-self.tail_tokens :])
            ordered.append(("tail", _hash_key("tail", tail)))

        # De-duplicate key ids while preserving order
        seen: set = set()
        out: List[Tuple[str, str]] = []
        for kind, kid in ordered:
            if kid not in seen:
                seen.add(kid)
                out.append((kind, kid))
        return out

    def build_injection_block(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Return (suffix_to_append_to_prompt, matched_key_or_none).
        """
        if not self.enabled:
            self._audit({"event": "lookup", "result": "skip", "reason": "disabled"})
            return "", None

        self.stats.lookups += 1
        for kind, key_id in self.lookup_keys_for_input(user_input):
            with self._lock:
                entry = self._entries.get(key_id)
            if not entry:
                continue
            ok, reason = self._gate(context, entry)
            if not ok:
                self.stats.gated_off += 1
                self._audit(
                    {
                        "event": "lookup",
                        "result": "gated",
                        "key_id": key_id,
                        "kind": kind,
                        "reason": reason,
                    }
                )
                continue

            self.stats.hits += 1
            body = entry.inject.strip()[: self._max_inject]
            block = (
                "\n\n[Local phrase memory — unverified; facts may be stale. "
                "Use only when helpful; prefer reasoning and Green Vault for canonical facts.]\n"
                f"{body}"
            )
            self._audit(
                {
                    "event": "lookup",
                    "result": "inject",
                    "key_id": key_id,
                    "kind": kind,
                    "confidence": entry.confidence,
                    "inject_len": len(body),
                }
            )
            return block, key_id

        self._audit({"event": "lookup", "result": "miss"})
        return "", None

    # --- management API ---

    def list_key_ids(self) -> List[str]:
        with self._lock:
            return list(self._entries.keys())

    def get_stats_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "tail_tokens": self.tail_tokens,
            "entries": len(self._entries),
            "lookups": self.stats.lookups,
            "hits": self.stats.hits,
            "gated_off": self.stats.gated_off,
            "storage_path": str(self.storage_path),
        }

    def upsert_entry(
        self,
        mode: str,
        pattern: str,
        inject: str,
        confidence: float = 0.8,
    ) -> str:
        """Add or replace entry; returns key_id."""
        mode = mode if mode in ("tail", "full") else "tail"
        normalized = _normalize(pattern)
        if mode == "tail":
            tokens = normalized.split()
            if len(tokens) >= self.tail_tokens:
                fragment = " ".join(tokens[-self.tail_tokens :])
            else:
                fragment = normalized
            key_id = _hash_key("tail", fragment)
            preview = fragment[:120]
        else:
            key_id = _hash_key("full", normalized)
            preview = normalized[:120]

        entry = PhraseMemoryEntry(
            inject=inject,
            confidence=confidence,
            mode=mode,
            pattern_preview=preview,
        )
        with self._lock:
            self._entries[key_id] = entry
            self._save_unlocked()
        self._audit(
            {
                "event": "upsert",
                "key_id": key_id,
                "mode": mode,
                "confidence": confidence,
            }
        )
        return key_id

    def delete_entry(self, key_id: str) -> bool:
        with self._lock:
            if key_id not in self._entries:
                return False
            del self._entries[key_id]
            self._save_unlocked()
        self._audit({"event": "delete", "key_id": key_id})
        return True
