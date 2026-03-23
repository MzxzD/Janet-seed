#!/bin/bash
# Install Janet HA API as a launchd service (auto-start on login)
# Run from janet-seed directory or scripts directory
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JANET_SEED_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_DEST="$HOME/Library/LaunchAgents/com.janet.ha-api.plist"

# Escape path for sed
ESCAPED_PATH=$(echo "$JANET_SEED_DIR" | sed 's/[\/&]/\\&/g')

# Create plist with correct path
sed "s|\\$HOME/Documents/Janet-Projects/JanetOS/janet-seed|$ESCAPED_PATH|g" \
  "$SCRIPT_DIR/com.janet.ha-api.plist" > "$PLIST_DEST"

echo "Installed plist to $PLIST_DEST"
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"
echo "Janet HA API loaded. It will auto-start on login."
echo "Logs: /tmp/janet-ha-api.log"
