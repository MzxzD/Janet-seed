"""
Context Builder for J.A.N.E.T. Seed
Builds conversation context from input, tone, memory, and delegation capabilities.
"""

from typing import Dict
from datetime import datetime


def build_context(janet, input_text: str, input_device: str) -> Dict:
    """Build context for conversation (tone, memory, delegation capabilities)."""
    context = {
        "input_text": input_text,
        "input_device": input_device,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "red_thread_active": janet.red_thread_active
    }
    
    # Add tone analysis (Day 2)
    if janet.tone_awareness and input_text:
        try:
            tone_analysis = janet.tone_awareness.analyze_text(input_text)
            context["tone"] = tone_analysis
        except Exception as e:
            # Tone analysis failed, continue without tone context
            print(f"⚠️  Tone analysis failed: {e}")
    
    # Add relevant memory context (Day 3)
    if janet.memory_manager:
        try:
            # Search for relevant past memories
            relevant_memories = janet.memory_manager.search(input_text, n_results=3)
            if relevant_memories:
                context["relevant_memories"] = [
                    {"text": m.get("text", ""), "timestamp": m.get("timestamp", "")}
                    for m in relevant_memories
                ]
        except Exception as e:
            # Memory search failed, continue without memory context
            print(f"⚠️  Memory search failed: {e}")
    
    # Add delegation capabilities (Day 4)
    if janet.delegation_manager:
        try:
            context["delegation_capabilities"] = janet.delegation_manager.get_capabilities()
        except Exception as e:
            # Delegation capabilities check failed, continue without
            print(f"⚠️  Failed to get delegation capabilities: {e}")
    
    return context

