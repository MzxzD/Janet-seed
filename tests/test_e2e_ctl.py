"""
E2E tests for the menu bar control surface (--ctl).
No GUI or live server required; tests config-get, config-set, status (server down).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Run janet_menubar.py --ctl from repo root
JANET_SEED_ROOT = Path(__file__).resolve().parent.parent
MENUBAR_SCRIPT = JANET_SEED_ROOT / "janet_menubar.py"


def run_ctl(*args):
    """Run python janet_menubar.py --ctl <args>; return (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(MENUBAR_SCRIPT), "--ctl"] + list(args)
    result = subprocess.run(
        cmd,
        cwd=str(JANET_SEED_ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode, result.stdout, result.stderr


def test_ctl_config_get():
    """Control surface: config-get returns valid JSON."""
    code, out, err = run_ctl("config-get")
    assert code == 0, f"stderr: {err}"
    data = json.loads(out)
    assert isinstance(data, dict)


def test_ctl_config_set_and_get():
    """Control surface: config-set then config-get round-trip."""
    test_cfg = {"api_url": "http://127.0.0.1:8080", "inactivity_min": 10}
    code, out, err = run_ctl("config-set", json.dumps(test_cfg))
    assert code == 0, f"stderr: {err}"
    data = json.loads(out)
    assert data.get("ok") is True
    assert data.get("config", {}).get("api_url") == test_cfg["api_url"]
    code2, out2, _ = run_ctl("config-get")
    assert code2 == 0
    got = json.loads(out2)
    assert got.get("api_url") == test_cfg["api_url"]


def test_ctl_status_without_server():
    """Control surface: status returns JSON with ok (true if server up, false if down)."""
    code, out, err = run_ctl("status")
    data = json.loads(out)
    assert "ok" in data
    if data.get("ok"):
        assert data.get("status_code") == 200 or "data" in data
    else:
        assert code == 1 or "error" in data or "status_code" in data


def test_ctl_unknown_command():
    """Control surface: unknown command returns error and exit 1."""
    code, out, err = run_ctl("unknown")
    assert code == 1
    data = json.loads(out)
    assert data.get("ok") is False
    assert "error" in data
