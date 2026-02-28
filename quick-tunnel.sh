#!/bin/bash
# Quick Cloudflare Tunnel setup for Janet
# This gives you a public URL that works from anywhere!

set -e

echo "🌐 Setting up Cloudflare Tunnel for Janet..."
echo ""
echo "This will give you a public URL like:"
echo "  https://janet-abc123.trycloudflare.com"
echo ""
echo "Then you can access Janet from:"
echo "  ✅ LTE/cellular"
echo "  ✅ Any WiFi network"
echo "  ✅ Anywhere in the world!"
echo ""

# Check if server is running
if ! lsof -i :8765 > /dev/null 2>&1; then
    echo "❌ Janet server is not running on port 8765!"
    echo ""
    echo "Please start the server first:"
    echo "  cd /Users/mzxzd/Documents/JanetOS/janet-seed"
    echo "  python3 simple_websocket_server.py"
    echo ""
    exit 1
fi

echo "✅ Janet server is running on port 8765"
echo ""

# Start tunnel
echo "🚇 Starting Cloudflare Tunnel..."
echo ""
echo "⚠️  IMPORTANT: Keep this terminal window open!"
echo "   The tunnel will stop if you close it."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run tunnel (this will output the URL)
cloudflared tunnel --url http://localhost:8765

# Note: The tunnel URL will be printed by cloudflared
# It looks like: https://janet-abc123.trycloudflare.com
