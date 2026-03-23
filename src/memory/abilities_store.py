"""
AC-GV2: Abilities store for "What can you do?" — grounded in abilities.json + goal_personas.
Single source of truth; no hallucination. Loads from Janet-Superpowers/data/abilities.json.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


def _find_abilities_json() -> Optional[Path]:
    """Locate abilities.json (Janet-Superpowers/data or env)."""
    here = Path(__file__).resolve()
    # .../janet-seed/src/memory/abilities_store.py -> go up to repo root then Janet-Superpowers
    # 3 levels up = janet-seed, 4 = JanetOS, 5 = Janet-Projects (or workspace)
    root5 = here.parent.parent.parent.parent.parent
    root4 = here.parent.parent.parent.parent
    candidates = [
        root5 / "Janet-Superpowers" / "data" / "abilities.json",
        root4 / "Janet-Superpowers" / "data" / "abilities.json",
        Path.home() / "Documents" / "Janet-Projects" / "Janet-Superpowers" / "data" / "abilities.json",
    ]
    import os
    if os.environ.get("JANET_ABILITIES_JSON"):
        candidates.insert(0, Path(os.environ["JANET_ABILITIES_JSON"]))
    for p in candidates:
        if p.exists():
            return p
    # Fallback: local abilities_knowledge.json (fewer abilities but works offline)
    local = Path(__file__).parent / "abilities_knowledge.json"
    if local.exists():
        return local
    return None


_store_cache: Optional[Dict[str, Any]] = None


def _load_store() -> Dict[str, Any]:
    """Load abilities.json (and goal_personas, jack) once; cache."""
    global _store_cache
    if _store_cache is not None:
        return _store_cache
    path = _find_abilities_json()
    if not path:
        _store_cache = {"abilities": [], "goal_personas": {}, "jack_architecture": None, "personas": {}}
        return _store_cache
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        abilities = data.get("abilities", [])
        if path.name == "abilities_knowledge.json":
            abilities = data.get("abilities", abilities)
        _store_cache = {
            "abilities": abilities,
            "goal_personas": data.get("goal_personas", {}),
            "jack_architecture": data.get("jack_architecture"),
            "personas": data.get("personas", {}),
        }
        return _store_cache
    except Exception:
        _store_cache = {"abilities": [], "goal_personas": {}, "jack_architecture": None, "personas": {}}
        return _store_cache


def get_what_can_you_do_response() -> str:
    """
    Build "What can you do?" reply from abilities store only (AC-GV2).
    No LLM; grounded in abilities.json + goal_personas + JACK.
    """
    store = _load_store()
    abilities: List[Dict] = store["abilities"]
    goal_personas: Dict = store["goal_personas"]
    jack: Optional[Dict] = store["jack_architecture"]
    personas: Dict = store["personas"]

    lines = ["Here’s what I can do, based on my current abilities and personas:\n"]

    if jack:
        lines.append(f"**{jack.get('name', 'J.A.C.K.')}** — {jack.get('description', '')}")
        lines.append("")

    # Active abilities by category
    active = [a for a in abilities if a.get("status") == "active"]
    by_cat: Dict[str, List[Dict]] = {}
    for a in active:
        cat = a.get("category") or "other"
        by_cat.setdefault(cat, []).append(a)
    if active:
        lines.append("**Abilities** (by category):")
        for cat in sorted(by_cat.keys()):
            lines.append(f"  • **{cat}**")
            for a in by_cat[cat]:
                name = a.get("name", a.get("id", ""))
                desc = (a.get("description") or "")[:200]
                if desc and len((a.get("description") or "")) > 200:
                    desc += "..."
                persona = a.get("persona", "")
                if persona:
                    lines.append(f"    - {name} ({persona}): {desc}")
                else:
                    lines.append(f"    - {name}: {desc}")
        lines.append("")

    # Goal personas (JACK)
    if goal_personas:
        lines.append("**Personas** (wake phrases):")
        for pid, p in goal_personas.items():
            name = p.get("name") or p.get("nickname") or pid
            goal = p.get("goal", "")
            wake = ", ".join(p.get("wake_phrases", [])[:3])
            lines.append(f"  • **{name}** — {goal}. e.g. {wake}")
        lines.append("")

    if personas:
        lines.append("**Other personas** (e.g. Business/Lynda):")
        for name, p in personas.items():
            desc = (p.get("description") or "")[:150]
            lines.append(f"  • {name}: {desc}")
        lines.append("")

    lines.append("You can say “What can you do?” anytime for this list, or ask about a specific ability or persona.")
    return "\n".join(lines).strip()


def reload_abilities_store() -> None:
    """Clear cache so next get_what_can_you_do_response() reloads from disk."""
    global _store_cache
    _store_cache = None
