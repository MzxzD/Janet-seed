# J.A.N.E.T. Seed — Install Guide

Install and run Janet AI (janet-seed + menu bar) on macOS for local and local-network use.

---

## Requirements

- **macOS** (primary; Linux possible with minor path changes)
- **Python 3.10+** (3.11 or 3.12 recommended)
- **Ollama** (for local LLM): [ollama.ai](https://ollama.ai) — install then `ollama pull qwen2.5-coder:7b` or another model

---

## Install from source

```bash
# Clone (or use existing JanetOS repo)
git clone --recurse-submodules https://github.com/MzxzD/JANET.git
cd JANET/core/JanetOS/janet-seed
# Or: cd path/to/Janet-Projects/JanetOS/janet-seed

# Dependencies
pip install -r requirements.txt

# Optional: menu bar (macOS)
pip install rumps requests
```

---

## Run

### 1. Janet API server (required for IDE and menu bar)

**Manual run:**
```bash
cd janet-seed
export JANET_API_HOST=0.0.0.0   # optional: allow LAN access (default)
python3 janet_api_server.py
```

**Auto-start at login (LaunchAgent, API + menu bar together):**
```bash
./scripts/install-janet-launchd.sh
```
- Starts API server and menu bar at login. Logs: `/tmp/janet-api.log`, `/tmp/janet-menubar.log`
- Plist: `~/Library/LaunchAgents/com.janet.plist`

- Listens on `http://0.0.0.0:8080` by default.
- Env: `JANET_API_PORT`, `JANET_DEFAULT_MODEL`, `JANET_API_KEY` (default `janet-local-dev`).

### 2. Menu bar (macOS)

**Manual run:**
```bash
python3 janet_menubar.py
```

(Menu bar is included in `install-janet-launchd.sh` above.)

- Control surface for CLI/E2E (no GUI): `python3 janet_menubar.py --ctl status|config-get|config-set <json>|start-server [model]`
- Health check only: `python3 janet_menubar.py --test`

### 3. Optional: orchestration module

```bash
cd path/to/janet_orchestration_module
pip install -r requirements.txt
python3 main.py
# Listens on http://0.0.0.0:9090 (JANET_ORCHESTRATION_PORT)
```

---

## One-liner install (all requirements + dependencies)

**Recommended (works for private repo too):** clone then install and run tests in one line:

```bash
git clone --depth 1 https://github.com/MzxzD/Janet-Projects.git ~/Janet-Projects && ~/Janet-Projects/JanetOS/janet-seed/scripts/one-liner-install.sh --test
```

Install only (no tests):

```bash
git clone --depth 1 https://github.com/MzxzD/Janet-Projects.git ~/Janet-Projects && ~/Janet-Projects/JanetOS/janet-seed/scripts/one-liner-install.sh
```

**Public one-liner** (script hosted in [janet-install](https://github.com/MzxzD/janet-install) — no 404):

```bash
curl -sSL https://raw.githubusercontent.com/MzxzD/janet-install/main/install.sh | bash
# Install + run all tests (including edge cases):
curl -sSL https://raw.githubusercontent.com/MzxzD/janet-install/main/install.sh | bash -s -- --test
```

If you already have the repo, run the script locally:

```bash
git clone --depth 1 https://github.com/MzxzD/Janet-Projects.git && cd Janet-Projects/JanetOS/janet-seed && bash scripts/one-liner-install.sh
# With tests:  bash scripts/one-liner-install.sh --test
```

Then start Janet and talk (e.g. via Cursor or curl):

```bash
./bin/janet-server    # or: .venv/bin/python3 janet_api_server.py
# In another terminal or Cursor: apiBase http://localhost:8080/v1
```

## Homebrew (when available)

When the Janet tap and formula are published:

```bash
brew tap MzxzD/janet
brew install janet-seed
# Or ALL-in-One (janet-seed + menu bar deps + optional orchestration):
# brew install janet-all
```

- **Alternative one-liner (OpenCode bundle):** `brew tap MzxzD/janet-opencode && brew install janet-opencode-bundle` — includes janet-seed + OpenCode.
- **Development / unreleased:** Use the formula in [Janet-Projects/janet_orchestration_module/Formula/janet-all.rb](../../janet_orchestration_module/Formula/janet-all.rb) with `brew install --build-from-source <path>/Formula/janet-all.rb`.

---

## Local WiFi / network use

To use Janet from other devices on your LAN (e.g. CallJanet-iOS, Cursor on another machine):

1. **Run the API server on the host Mac** with `JANET_API_HOST=0.0.0.0` (default).
2. **On clients**, set the API base URL to the Mac’s IP, e.g. `http://192.168.1.100:8080`.
   - Menu bar config: set "API URL" in Settings, or write `~/.janet/menubar_config.json` with `"api_url": "http://<Mac-IP>:8080"`.
   - Cursor / Continue: set `apiBase` to `http://<Mac-IP>:8080/v1`.
3. **Optional:** Run mDNS advertiser so clients can discover Janet:
   ```bash
   python3 mdns_advertiser.py
   ```
   CallJanet-iOS can then discover `_janet._tcp` on the local network.
4. **Firewall:** Allow inbound TCP 8080 (and 8765 if using WebSocket) on the host if needed.

---

## Verify

- **Health:** `curl http://localhost:8080/health`
- **Models:** `curl -H "Authorization: Bearer janet-local-dev" http://localhost:8080/v1/models`
- **Control surface:** `python3 janet_menubar.py --ctl config-get`
- **Tests:** `python3 -m pytest tests/ -v` (see [tests/README.md](tests/README.md))

---

## See also

- [README.md](README.md) — Overview and architecture
- [QUICK_START_IDE.md](QUICK_START_IDE.md) — IDE integration
- [CHANGELOG.md](CHANGELOG.md) — Version history
- Operator runbook: [janet_orchestration_module/OPERATOR_RUNBOOK.md](../../janet_orchestration_module/OPERATOR_RUNBOOK.md)
