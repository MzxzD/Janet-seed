#!/bin/bash
# Install Janet (API server + menu bar) as a single LaunchAgent.
# Replaces com.janet.api and com.janet.menubar with unified com.janet.
# Copies script to /tmp so launchd can run it (avoids Documents sandbox).
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JANET_SEED_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_DEST="$HOME/Library/LaunchAgents/com.janet.plist"
RUNNER="/tmp/janet_start_with_menubar.sh"

# Unload old separate LaunchAgents
launchctl unload "$HOME/Library/LaunchAgents/com.janet.api.plist" 2>/dev/null || true
launchctl unload "$HOME/Library/LaunchAgents/com.janet.menubar.plist" 2>/dev/null || true

# Copy script to /tmp (launchd can run from /tmp; Documents may be sandboxed)
cp "$SCRIPT_DIR/start_janet_with_menubar.sh" "$RUNNER"
chmod +x "$RUNNER"

# Create plist: run from /tmp, pass JANET_SEED_DIR via env
cat > "$PLIST_DEST" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.janet</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$RUNNER</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/tmp</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>LimitLoadToSessionType</key>
    <string>Aqua</string>
    <key>StandardOutPath</key>
    <string>/tmp/janet-menubar.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/janet-menubar.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>JANET_SEED_DIR</key>
        <string>$JANET_SEED_DIR</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin</string>
    </dict>
</dict>
</plist>
PLIST

echo "Installed plist to $PLIST_DEST"
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"
echo "Janet (API + menu bar) loaded. Both start together at login."
echo "Logs: /tmp/janet-api.log, /tmp/janet-menubar.log"
