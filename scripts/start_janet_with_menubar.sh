#!/bin/bash
# Start Janet API server + menu bar together. Used by LaunchAgent.
# JANET_SEED_DIR from env. Run from /tmp to avoid Documents sandbox; use full paths.
set -e
JANET_DIR="${JANET_SEED_DIR:?JANET_SEED_DIR not set}"

# Prefer venv for both (menubar needs rumps)
if [ -x "$JANET_DIR/.venv/bin/python3" ]; then
    PYTHON="$JANET_DIR/.venv/bin/python3"
else
    PYTHON="$(which python3)"
fi

# 1. Start API server in background (if not already running)
if ! curl -s http://localhost:8080/health >/dev/null 2>&1; then
    nohup "$PYTHON" "$JANET_DIR/janet_api_server.py" >> /tmp/janet-api.log 2>> /tmp/janet-api.err &
    sleep 2
fi

# 2. Run menu bar (foreground — LaunchAgent keeps this alive)
exec "$PYTHON" "$JANET_DIR/janet_menubar.py"
