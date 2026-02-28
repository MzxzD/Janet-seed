#!/bin/bash
# Setup Cloudflare Tunnel for Janet with ジャネット.com domain
# Japanese domain: https://ジャネット.com (xn--wckzexc.com in Punycode)

set -e

echo "🎌 Setting up Janet with Japanese domain: ジャネット.com"
echo ""

# Convert Japanese domain to Punycode (ASCII-compatible encoding)
DOMAIN_JAPANESE="ジャネット.com"
DOMAIN_PUNYCODE="xn--wckzexc.com"

echo "📝 Domain Information:"
echo "   Japanese: https://${DOMAIN_JAPANESE}"
echo "   Punycode: https://${DOMAIN_PUNYCODE}"
echo "   (Both work the same!)"
echo ""

# Check if server is running
if ! lsof -i :8765 > /dev/null 2>&1; then
    echo "❌ Janet server is not running on port 8765!"
    echo ""
    echo "Please start the server first:"
    echo "  cd /Users/mzxzd/Documents/JanetOS/janet-seed"
    echo "  python3 simple_websocket_server.py &"
    echo ""
    exit 1
fi

echo "✅ Janet server is running on port 8765"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    brew install cloudflare/cloudflare/cloudflared
fi

echo "✅ cloudflared installed"
echo ""

# Login to Cloudflare
echo "🔐 Logging in to Cloudflare..."
echo "   (This will open your browser)"
echo ""
cloudflared tunnel login

echo ""
echo "✅ Logged in to Cloudflare"
echo ""

# Create tunnel
TUNNEL_NAME="janet-$(date +%s)"
echo "🚇 Creating tunnel: $TUNNEL_NAME..."
cloudflared tunnel create $TUNNEL_NAME

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo "✅ Tunnel created: $TUNNEL_ID"
echo ""

# Create config file
CONFIG_FILE=~/.cloudflared/config.yml
echo "📝 Creating config file: $CONFIG_FILE..."

cat > $CONFIG_FILE << EOF
tunnel: $TUNNEL_ID
credentials-file: ~/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: ${DOMAIN_PUNYCODE}
    service: ws://localhost:8765
  - hostname: ${DOMAIN_JAPANESE}
    service: ws://localhost:8765
  - service: http_status:404
EOF

echo "✅ Config file created"
echo ""

# Route DNS
echo "🌐 Setting up DNS for ${DOMAIN_JAPANESE}..."
echo ""
cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN_PUNYCODE

echo ""
echo "✅ DNS configured!"
echo ""

# Create LaunchAgent for auto-start
PLIST_FILE=~/Library/LaunchAgents/com.janetos.cloudflared.plist
echo "📝 Creating LaunchAgent for auto-start..."

cat > $PLIST_FILE << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.janetos.cloudflared</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/cloudflared</string>
        <string>tunnel</string>
        <string>run</string>
        <string>$TUNNEL_NAME</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/cloudflared.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/cloudflared.err</string>
</dict>
</plist>
EOF

echo "✅ LaunchAgent created"
echo ""

# Load LaunchAgent
echo "🚀 Starting tunnel..."
launchctl load $PLIST_FILE 2>/dev/null || launchctl start com.janetos.cloudflared

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 SUCCESS! Janet is now accessible at:"
echo ""
echo "   🎌 https://ジャネット.com"
echo "   🌐 https://xn--wckzexc.com"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 UPDATE YOUR IPHONE APP:"
echo ""
echo "1. Open Call Janet app"
echo "2. Go to Settings tab"
echo "3. Tap 'Server URL'"
echo "4. Change to: wss://ジャネット.com"
echo "   (or: wss://xn--wckzexc.com)"
echo "5. Save"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔧 TUNNEL STATUS:"
echo "   - Auto-starts on Mac boot"
echo "   - Check logs: tail -f /tmp/cloudflared.log"
echo "   - Stop: launchctl stop com.janetos.cloudflared"
echo "   - Start: launchctl start com.janetos.cloudflared"
echo ""
echo "✅ Setup complete!"
echo ""
