#!/bin/bash
# Setup heyjanet.bot as production backend for Call Janet

set -e

echo "🤖 Setting up heyjanet.bot as Call Janet backend..."
echo ""

# Check if server is running
if ! lsof -i :8765 > /dev/null 2>&1; then
    echo "❌ Janet server is not running on port 8765!"
    exit 1
fi

echo "✅ Janet server is running on port 8765"
echo ""

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep janet- | awk '{print $1}')
TUNNEL_NAME=$(cloudflared tunnel list | grep janet- | awk '{print $2}')

echo "📝 Using existing tunnel: $TUNNEL_NAME ($TUNNEL_ID)"
echo ""

# Update config
CONFIG_FILE=~/.cloudflared/config.yml
echo "📝 Updating config file: $CONFIG_FILE..."

# Backup existing config
cp $CONFIG_FILE ${CONFIG_FILE}.backup

# Add heyjanet.bot to ingress
cat > $CONFIG_FILE << EOF
tunnel: $TUNNEL_ID
credentials-file: ~/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: heyjanet.bot
    service: ws://localhost:8765
  - hostname: xn--yckwaps3i.com
    service: ws://localhost:8765
  - hostname: ジャネット.com
    service: ws://localhost:8765
  - service: http_status:404
EOF

echo "✅ Config file updated"
echo ""

# Route DNS
echo "🌐 Setting up DNS for heyjanet.bot..."
cloudflared tunnel route dns $TUNNEL_NAME heyjanet.bot

echo ""
echo "✅ DNS configured!"
echo ""

# Restart tunnel
echo "🔄 Restarting tunnel..."
launchctl stop com.janetos.cloudflared
sleep 2
launchctl start com.janetos.cloudflared

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 SUCCESS! heyjanet.bot is now configured!"
echo ""
echo "   🤖 Production: wss://heyjanet.bot"
echo "   🎌 Japanese: wss://ジャネット.com"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 iOS/Watch apps will now use heyjanet.bot by default"
echo ""
