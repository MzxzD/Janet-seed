"""Tests for central context fusion (janet-seed)."""
from src.core.context_fusion import (
    build_fused_user_prompt,
    resolve_skip_flags,
)


class FakePhraseMemory:
    def __init__(self):
        self.called = False

    def build_injection_block(self, user_input, context):
        self.called = True
        if user_input.strip() == "trigger":
            return ("\n\n[Local phrase memory — unverified]\nextra", "key1")
        return "", None


def test_resolve_skip_flags_all():
    f = resolve_skip_flags({"skip_context_fusion": True})
    assert f["all"] and f["memories"] and f["tone"] and f["phrase"]


def test_resolve_phrase_opt_out():
    f = resolve_skip_flags({"phrase_memory": False})
    assert not f["all"] and not f["memories"] and f["phrase"]


def test_fusion_order_and_skip_all():
    pm = FakePhraseMemory()
    ctx = {
        "relevant_memories": [{"text": "mem1"}],
        "tone": {"emotion": "calm"},
    }
    r = build_fused_user_prompt("hi", ctx, pm)
    assert "mem1" in r.prompt
    assert "calm" in r.prompt
    assert pm.called
    assert r.fusion_meta.get("layers_applied") == ["base", "relevant_memories", "tone"]

    r2 = build_fused_user_prompt(
        "trigger",
        {**ctx, "skip_context_fusion": True},
        pm,
    )
    assert r2.prompt == "trigger"
    assert "mem1" not in r2.prompt
    # Second call: phrase memory should not run when all skip
    pm2 = FakePhraseMemory()
    build_fused_user_prompt("trigger", {"skip_context_fusion": True}, pm2)
    assert not pm2.called


def test_skip_layers_individually():
    pm = FakePhraseMemory()
    ctx = {
        "relevant_memories": [{"text": "unique_mem_marker"}],
        "tone": {"emotion": "sad"},
        "skip_relevant_memories": True,
        "skip_tone_context": True,
    }
    r = build_fused_user_prompt("trigger", ctx, pm)
    assert "unique_mem_marker" not in r.prompt
    assert "sad" not in r.prompt
    assert "extra" in r.prompt
