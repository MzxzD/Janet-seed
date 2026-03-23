"""
E2E tests for Janet API server (health, models, chat, "What can you do?").
Requires janet_api_server running, or set JANET_E2E_API_URL to skip when server is down.
"""
import os
import sys
from pathlib import Path

import pytest

try:
    import requests
except ImportError:
    requests = None

# API base: env or default localhost
API_BASE = os.environ.get("JANET_E2E_API_URL", "http://localhost:8080")
API_KEY = os.environ.get("JANET_API_KEY", "janet-local-dev")
JANET_SEED_ROOT = Path(__file__).resolve().parent.parent


def server_available():
    """Check if Janet API server is reachable."""
    if not requests:
        return False
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not server_available(), reason="Janet API server not running at JANET_E2E_API_URL / localhost:8080")
def test_e2e_health():
    """E2E: GET /health returns 200 and brain/model info."""
    r = requests.get(f"{API_BASE}/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data or "brain_available" in data or "current_model" in data


@pytest.mark.skipif(not server_available(), reason="Janet API server not running")
def test_e2e_models():
    """E2E: GET /v1/models returns list."""
    r = requests.get(
        f"{API_BASE}/v1/models",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=5,
    )
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.skipif(not server_available(), reason="Janet API server not running")
def test_e2e_what_can_you_do():
    """E2E: Chat with 'What can you do?' returns grounded abilities (no hallucination)."""
    r = requests.post(
        f"{API_BASE}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.environ.get("JANET_DEFAULT_MODEL", "qwen2.5-coder:7b"),
            "messages": [{"role": "user", "content": "What can you do?"}],
            "temperature": 0.3,
            "max_tokens": 500,
            "stream": False,
        },
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    # AC-GV2: response should be from abilities store (contain abilities/personas/JACK)
    assert content, "Response must not be empty"
    # Should mention abilities or personas or JACK (grounded)
    assert any(
        word in content.lower() for word in ["abilities", "personas", "jack", "what i can do"]
    ), f"Expected grounded abilities response, got: {content[:200]}..."
