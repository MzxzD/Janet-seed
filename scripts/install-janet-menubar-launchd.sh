#!/bin/bash
# Install Janet menu bar app as a LaunchAgent (auto-start at login, shows status in menu bar)
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JANET_SEED_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_DEST="$HOME/Library/LaunchAgents/com.janet.menubar.plist"

# Prefer venv python (has rumps); fallback to system python3
if [ -x "$JANET_SEED_DIR/.venv/bin/python3" ]; then
    PYTHON_PATH="$JANET_SEED_DIR/.venv/bin/python3"
else
    PYTHON_PATH="$(which python3)"
fi

# Create plist with substituted paths
sed -e "s|JANET_PYTHON|$PYTHON_PATH|g" \
    -e "s|JANET_SEED_PATH|$JANET_SEED_DIR|g" \
    "$SCRIPT_DIR/com.janet.menubar.plist" > "$PLIST_DEST"

echo "Installed plist to $PLIST_DEST"
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"
echo "Janet menu bar loaded. Status icon will appear in the menu bar."
echo "Logs: /tmp/janet-menubar.log"
