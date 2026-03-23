"""
AC-GV2: Tests for abilities store and "What can you do?" response.
Verification: abilities store loaded; response grounded in store; no hallucination.
"""
import sys
from pathlib import Path

# Import abilities_store in isolation (no src.memory package to avoid heavy deps)
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))
# Load module by path to avoid pulling in memory_manager, green_vault, etc.
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "abilities_store",
    _root / "src" / "memory" / "abilities_store.py",
)
_abilities_store = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_abilities_store)

get_what_can_you_do_response = _abilities_store.get_what_can_you_do_response
reload_abilities_store = _abilities_store.reload_abilities_store
_find_abilities_json = _abilities_store._find_abilities_json
_load_store = _abilities_store._load_store


def test_find_abilities_json():
    """Either finds abilities.json (Janet-Superpowers or env) or local abilities_knowledge.json."""
    path = _find_abilities_json()
    # May be None if no file exists in any candidate path
    if path:
        assert path.exists(), f"Path should exist: {path}"
        assert path.suffix == ".json"


def test_get_what_can_you_do_response_returns_string():
    """What can you do? returns a non-empty string."""
    reload_abilities_store()
    response = get_what_can_you_do_response()
    assert isinstance(response, str)
    assert len(response) > 0
    assert "what I can do" in response.lower() or "abilities" in response.lower() or "personas" in response.lower()


def test_response_grounded_in_store():
    """Response is built from store only (JACK/abilities/personas when present)."""
    reload_abilities_store()
    store = _load_store()
    response = get_what_can_you_do_response()
    # If we have abilities, response should mention at least one category or ability
    if store.get("abilities"):
        assert "Abilities" in response or "abilities" in response
    if store.get("goal_personas"):
        assert "Personas" in response or "personas" in response
    if store.get("jack_architecture"):
        assert "J.A.C.K" in response or "JACK" in response


def test_what_can_you_do_no_hallucination():
    """Response does not contain placeholder hallucination text."""
    reload_abilities_store()
    response = get_what_can_you_do_response()
    bad = ["I don't have that information", "I cannot access", "as an AI", "I'm not sure"]
    for phrase in bad:
        assert phrase.lower() not in response.lower(), f"Response should not contain: {phrase}"


if __name__ == "__main__":
    test_find_abilities_json()
    test_get_what_can_you_do_response_returns_string()
    test_response_grounded_in_store()
    test_what_can_you_do_no_hallucination()
    print("All AC-GV2 abilities_store tests passed.")
