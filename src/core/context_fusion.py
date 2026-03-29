"""
Central prompt augmentation for janet-seed (SEED priority).

Single ordering for context fused into the *user* message passed to the LLM:
  1. Raw user text
  2. Relevant memories (from caller-supplied context)
  3. Tone hint
  4. PhraseMemory (Engram-style local lookup + gate inside PhraseMemory)

Use `skip_context_fusion` to bypass all additions (debug / critical paths).
Finer skips: `skip_relevant_memories`, `skip_tone_context`; phrase legacy:
`phrase_memory=False`, `skip_phrase_memory`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ContextFusionResult:
    """Output of `build_fused_user_prompt`."""

    prompt: str
    fusion_meta: Dict[str, Any] = field(default_factory=dict)


def resolve_skip_flags(context: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """
    Returns flags: all, memories, tone, phrase.
    When ``all`` is True, callers should skip every augmentation.
    ``memories`` / ``tone`` / ``phrase`` mean "skip this layer only".
    """
    c = context or {}
    all_skip = c.get("skip_context_fusion") is True
    return {
        "all": all_skip,
        "memories": all_skip or c.get("skip_relevant_memories") is True,
        "tone": all_skip or c.get("skip_tone_context") is True,
        "phrase": all_skip
        or c.get("phrase_memory") is False
        or c.get("skip_phrase_memory") is True,
    }


def build_fused_user_prompt(
    user_input: str,
    context: Optional[Dict[str, Any]],
    phrase_memory: Optional[Any] = None,
) -> ContextFusionResult:
    """
    Build the full user-role prompt string with a fixed augmentation order.

    ``phrase_memory`` is optional; if None, step 4 is skipped.
    """
    flags = resolve_skip_flags(context)
    parts: List[str] = [user_input]
    meta: Dict[str, Any] = {"skip_flags": flags}

    if flags["all"]:
        meta["layers_applied"] = []
        return ContextFusionResult(prompt=user_input, fusion_meta=meta)

    applied: List[str] = ["base"]

    if not flags["memories"] and context:
        memories = context.get("relevant_memories")
        if memories:
            parts.append("\n\nRelevant context from past conversations:")
            for mem in memories[:3]:
                parts.append(f"- {mem.get('text', '')[:100]}")
            applied.append("relevant_memories")

    if not flags["tone"] and context:
        tone = context.get("tone")
        if tone and tone.get("emotion"):
            parts.append(f"\n\nUser's emotional tone: {tone.get('emotion')}")
            applied.append("tone")

    if not flags["phrase"] and phrase_memory:
        block, key = phrase_memory.build_injection_block(user_input, context)
        if block:
            parts.append(block)
            applied.append("phrase_memory")
            if key:
                meta["phrase_memory_key"] = key

    meta["layers_applied"] = applied
    return ContextFusionResult(prompt="\n".join(parts), fusion_meta=meta)
