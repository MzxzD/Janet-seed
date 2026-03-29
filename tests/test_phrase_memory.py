"""Tests for Engram-inspired PhraseMemory orchestration layer."""
import json
import pytest

from src.core.phrase_memory import PhraseMemory, _hash_key, _normalize


def test_normalize_collapses_space():
    assert _normalize("  Hello   World  ") == "hello world"


def test_hash_key_stable():
    a = _hash_key("tail", "a b c")
    b = _hash_key("tail", "a b c")
    assert a == b
    assert len(a) == 24


def test_tail_lookup_and_inject(tmp_path):
    store = tmp_path / "pm.json"
    audit = tmp_path / "audit.jsonl"
    pm = PhraseMemory(storage_path=store, audit_path=audit, tail_tokens=2, enabled=True)
    pm.upsert_entry(mode="tail", pattern="foo bar", inject="HINT: bingo", confidence=0.9)

    block, key = pm.build_injection_block("hello foo bar", context=None)
    assert key is not None
    assert "bingo" in block
    assert "unverified" in block.lower()

    # Context opt-out
    block2, _ = pm.build_injection_block("hello foo bar", context={"phrase_memory": False})
    assert block2 == ""


def test_red_thread_gates(tmp_path, monkeypatch):
    store = tmp_path / "pm.json"
    audit = tmp_path / "audit.jsonl"
    pm = PhraseMemory(storage_path=store, audit_path=audit, enabled=True)
    pm.upsert_entry(mode="full", pattern="stop", inject="should not appear")

    class Ev:
        def __init__(self):
            self._v = False

        def is_set(self):
            return self._v

    ev = Ev()
    monkeypatch.setattr(
        "src.core.phrase_memory.RED_THREAD_EVENT",
        ev,
        raising=False,
    )
    ev._v = True
    block, key = pm.build_injection_block("stop", context=None)
    assert block == ""
    assert key is None


def test_upsert_persists(tmp_path):
    store = tmp_path / "pm.json"
    pm = PhraseMemory(storage_path=store, tail_tokens=3)
    kid = pm.upsert_entry(mode="full", pattern="short phrase", inject="body", confidence=0.7)
    pm2 = PhraseMemory(storage_path=store, tail_tokens=3)
    assert kid in pm2.list_key_ids()
    block, _ = pm2.build_injection_block("short phrase", None)
    assert "body" in block
