#!/bin/bash
# Install Janet API Server as a LaunchAgent (auto-start on login)
# Run from janet-seed directory or scripts directory
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JANET_SEED_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_PATH="$(which python3)"
PLIST_DEST="$HOME/Library/LaunchAgents/com.janet.api.plist"

# Create plist with substituted paths
sed -e "s|JANET_SEED_PYTHON|$PYTHON_PATH|g" \
    -e "s|JANET_SEED_PATH|$JANET_SEED_DIR|g" \
    "$SCRIPT_DIR/com.janet.api.plist" > "$PLIST_DEST"

echo "Installed plist to $PLIST_DEST"
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"
echo "Janet API Server loaded. It will auto-start on login and restart if it crashes."
echo "Logs: /tmp/janet-api.log"
echo ""
echo "Verify: curl http://localhost:8080/health"
