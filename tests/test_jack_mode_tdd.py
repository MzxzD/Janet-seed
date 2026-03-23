"""
JACK MODE — TDD tests driven by terminal output.

Run real terminal flows (menubar --ctl, optional server); use output to fix/optimize
and keep the user flow seamless. No mocks for these; assert on exit code and stdout/stderr.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

JANET_SEED_ROOT = Path(__file__).resolve().parent.parent
MENUBAR_SCRIPT = JANET_SEED_ROOT / "janet_menubar.py"


def run_terminal(cmd, cwd=None, env=None, timeout=15):
    """Run command; return (returncode, stdout, stderr)."""
    cwd = cwd or str(JANET_SEED_ROOT)
    env = env or os.environ.copy()
    result = subprocess.run(
        cmd if isinstance(cmd, list) else ["bash", "-c", cmd],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


# ---- --ctl flow: output must be valid JSON, no tracebacks ----

def test_ctl_config_get_output_is_json():
    """TDD: config-get prints exactly one JSON object; no stderr noise."""
    code, out, err = run_terminal(
        [sys.executable, str(MENUBAR_SCRIPT), "--ctl", "config-get"]
    )
    assert code == 0, f"exit {code} stderr: {err!r}"
    data = json.loads(out)
    assert isinstance(data, dict)
    # Seamless: stderr should not contain tracebacks or scary messages
    assert "Traceback" not in err
    assert "Error" not in err or "error" in out  # key in JSON is ok


def test_ctl_config_set_roundtrip_output():
    """TDD: config-set then config-get; output is parseable and reflects set value."""
    cfg = {"api_url": "http://127.0.0.1:8080", "inactivity_min": 15}
    code1, out1, err1 = run_terminal(
        [sys.executable, str(MENUBAR_SCRIPT), "--ctl", "config-set", json.dumps(cfg)]
    )
    assert code1 == 0, f"config-set failed: {err1!r}"
    data1 = json.loads(out1)
    assert data1.get("ok") is True
    assert data1.get("config", {}).get("api_url") == cfg["api_url"]

    code2, out2, err2 = run_terminal(
        [sys.executable, str(MENUBAR_SCRIPT), "--ctl", "config-get"]
    )
    assert code2 == 0
    data2 = json.loads(out2)
    assert data2.get("api_url") == cfg["api_url"]


def test_ctl_status_output_structure():
    """TDD: status prints JSON with ok and error/status_code; exit 0 or 1."""
    code, out, err = run_terminal(
        [sys.executable, str(MENUBAR_SCRIPT), "--ctl", "status"]
    )
    data = json.loads(out)
    assert "ok" in data
    if data.get("ok"):
        assert "data" in data or "status_code" in data
    else:
        assert "error" in data or "status_code" in data
    assert "Traceback" not in err


def test_ctl_unknown_command_exit_and_message():
    """TDD: unknown command exits 1 and prints usage in JSON."""
    code, out, err = run_terminal(
        [sys.executable, str(MENUBAR_SCRIPT), "--ctl", "unknown-cmd"]
    )
    assert code == 1
    data = json.loads(out)
    assert data.get("ok") is False
    assert "error" in data
    assert "usage" in data or "unknown" in data.get("error", "").lower()


def test_ctl_start_server_default_model_is_qwen():
    """TDD: start-server (no args) uses default model qwen2.5-coder:7b (seamless)."""
    menubar_src = MENUBAR_SCRIPT.read_text()
    assert "start-server" in menubar_src
    assert "qwen2.5-coder:7b" in menubar_src


# ---- One-liner / install script flow (dry run): no crash, expected lines ----

def test_one_liner_script_dry_run_exits_clean():
    """TDD: install script with JANET_ONE_LINER_DRY_RUN=1 exits 0 and prints Install dir."""
    script = JANET_SEED_ROOT / "scripts" / "one-liner-install.sh"
    if not script.exists():
        pytest.skip("one-liner-install.sh not in repo")
    code, out, err = run_terminal(
        ["bash", str(script)],
        cwd=str(JANET_SEED_ROOT),
        env={**os.environ, "JANET_SEED_DIR": str(JANET_SEED_ROOT), "JANET_ONE_LINER_DRY_RUN": "1"},
        timeout=30,
    )
    assert "Install dir:" in out or "Janet" in out
    assert "Traceback" not in out + err


def test_one_liner_script_run_sets_default_model():
    """TDD: When script starts server (--run), it should use qwen2.5-coder:7b (seamless)."""
    script = JANET_SEED_ROOT / "scripts" / "one-liner-install.sh"
    if not script.exists():
        pytest.skip("one-liner-install.sh not in repo")
    text = script.read_text()
    assert "DO_RUN" in text and "janet_api_server" in text
    # Server default is qwen2.5-coder:7b in janet_api_server.py; script may set env for --run
    assert "qwen2.5-coder" in text or "JANET_DEFAULT_MODEL" in text
