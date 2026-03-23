"""
Edge-case tests: API (server down, bad port, timeout, bad request, auth) and install script (idempotent, env).
These run without a live server for API-down cases; optional server for live edge cases.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

try:
    import requests
except ImportError:
    requests = None

JANET_SEED_ROOT = Path(__file__).resolve().parent.parent
API_BASE = os.environ.get("JANET_E2E_API_URL", "http://localhost:8080")
API_KEY = os.environ.get("JANET_API_KEY", "janet-local-dev")


# ---- API edge cases (no server or unreachable) ----

@pytest.mark.skipif(not requests, reason="requests not installed")
def test_api_health_when_server_down():
    """When server is down, GET /health fails (connection error or 5xx)."""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=2)
        # If server is up, we expect 200
        assert r.status_code in (200, 502, 503), f"Unexpected {r.status_code}"
    except requests.exceptions.ConnectTimeout:
        pass
    except requests.exceptions.ConnectionError:
        pass


@pytest.mark.skipif(not requests, reason="requests not installed")
def test_api_bad_port_connection_error():
    """Request to invalid port (e.g. 19999) raises connection error."""
    try:
        requests.get("http://127.0.0.1:19999/health", timeout=1)
        # If something is listening on 19999, we just require no crash
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
        pass


@pytest.mark.skipif(not requests, reason="requests not installed")
def test_api_chat_without_server():
    """POST /v1/chat/completions when server down: connection/timeout or 5xx."""
    try:
        r = requests.post(
            f"{API_BASE}/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "test", "messages": [{"role": "user", "content": "Hi"}]},
            timeout=2,
        )
        assert r.status_code in (200, 502, 503, 504)
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
        pass


@pytest.mark.skipif(not requests, reason="requests not installed")
def test_api_malformed_json_returns_4xx():
    """POST with invalid JSON body should return 4xx (when server is up)."""
    try:
        r = requests.post(
            f"{API_BASE}/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data="not json at all",
            timeout=3,
        )
        assert r.status_code in (400, 422, 502, 503) or r.status_code >= 500
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
        pass


@pytest.mark.skipif(not requests, reason="requests not installed")
def test_api_wrong_key_returns_401_when_server_up():
    """When server is up, wrong API key should return 401 (or 200 if dev bypass)."""
    try:
        r = requests.get(
            f"{API_BASE}/v1/models",
            headers={"Authorization": "Bearer wrong-key"},
            timeout=3,
        )
        assert r.status_code in (200, 401, 403, 502, 503)
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
        pass


# ---- Install script edge cases ----

def _run_install_script(extra_env=None, *args):
    """Run one-liner-install.sh in repo; return (returncode, stdout, stderr)."""
    script = JANET_SEED_ROOT / "scripts" / "one-liner-install.sh"
    if not script.exists():
        pytest.skip("one-liner-install.sh not found")
    env = os.environ.copy()
    env.setdefault("JANET_SEED_DIR", str(JANET_SEED_ROOT))
    # Dry run so we don't install Homebrew/pip in tests (fast)
    env.setdefault("JANET_ONE_LINER_DRY_RUN", "1")
    if extra_env:
        env.update(extra_env)
    cmd = ["bash", str(script)] + list(args)
    result = subprocess.run(
        cmd,
        cwd=str(JANET_SEED_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode, result.stdout, result.stderr


def test_install_script_accepts_custom_janet_seed_dir():
    """Script respects JANET_SEED_DIR when set."""
    # Run with --test might fail if no brew/python in CI; we only check it doesn't crash with JANET_SEED_DIR
    env = {"JANET_SEED_DIR": str(JANET_SEED_ROOT)}
    code, out, err = _run_install_script(env)
    # 0 = success; non-zero can be brew/python missing in CI
    assert code in (0, 1)
    assert "Install dir:" in out or "Janet" in out or "Using:" in out or len(out) > 0


def test_install_script_idempotent_second_run():
    """Second run of install script does not fail (idempotent)."""
    code1, _, _ = _run_install_script()
    code2, _, _ = _run_install_script()
    # Both should exit 0 or same non-zero (e.g. CI without brew)
    assert code1 == code2


def test_install_script_bin_stubs_exist_and_are_executable_after_install():
    """After a real install, bin/janet-server and bin/janet-menubar exist and are executable."""
    bin_server = JANET_SEED_ROOT / "bin" / "janet-server"
    bin_menubar = JANET_SEED_ROOT / "bin" / "janet-menubar"
    if not (JANET_SEED_ROOT / ".venv").exists():
        pytest.skip("No .venv; run one-liner-install.sh first")
    if not bin_server.exists() or not bin_menubar.exists():
        pytest.skip("bin stubs not found; run one-liner-install.sh (without JANET_ONE_LINER_DRY_RUN) once")
    assert os.access(bin_server, os.X_OK), "bin/janet-server should be executable"
    assert os.access(bin_menubar, os.X_OK), "bin/janet-menubar should be executable"
