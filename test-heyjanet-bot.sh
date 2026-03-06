#!/bin/bash

echo "🧪 Testing heyjanet.bot WebSocket Connection"
echo "=============================================="
echo ""

# 1. Check DNS Resolution
echo "1️⃣  Checking DNS resolution..."
DNS_RESULT=$(dig heyjanet.bot +short | head -1)
if [ -z "$DNS_RESULT" ]; then
    echo "❌ DNS not resolving yet. Nameservers may still be propagating."
    echo "   Current nameservers:"
    dig NS xn--yckwaps3i.com +short
    exit 1
else
    echo "✅ DNS resolving to: $DNS_RESULT"
fi
echo ""

# 2. Check HTTPS endpoint
echo "2️⃣  Testing HTTPS endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 https://heyjanet.bot 2>/dev/null)
if [ "$HTTP_CODE" == "000" ]; then
    echo "❌ Cannot connect to HTTPS endpoint (connection timeout)"
elif [ "$HTTP_CODE" == "400" ]; then
    echo "✅ Server responding (400 is expected for non-WebSocket request)"
else
    echo "ℹ️  Server responded with HTTP $HTTP_CODE"
fi
echo ""

# 3. Check local server
echo "3️⃣  Checking local WebSocket server..."
if pgrep -f "simple_websocket_server.py" > /dev/null; then
    echo "✅ Local server is running (PID: $(pgrep -f simple_websocket_server.py))"
else
    echo "❌ Local server is NOT running"
    echo "   Start it with: cd /Users/mzxzd/Documents/JanetOS/janet-seed && nohup ./venv/bin/python3 simple_websocket_server.py > /tmp/janet-server.log 2>&1 &"
fi
echo ""

# 4. Check Cloudflare tunnel
echo "4️⃣  Checking Cloudflare tunnel..."
if pgrep -f "cloudflared.*tunnel.*run" > /dev/null; then
    echo "✅ Cloudflare tunnel is running (PID: $(pgrep -f 'cloudflared.*tunnel.*run'))"
else
    echo "❌ Cloudflare tunnel is NOT running"
    echo "   Start it with: launchctl start com.cloudflare.cloudflared"
fi
echo ""

# 5. Test WebSocket with curl (if available)
echo "5️⃣  Testing WebSocket handshake..."
WS_TEST=$(curl -i -N \
    -H "Connection: Upgrade" \
    -H "Upgrade: websocket" \
    -H "Sec-WebSocket-Version: 13" \
    -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
    --connect-timeout 10 --max-time 15 \
    https://heyjanet.bot 2>&1 | head -1)

if echo "$WS_TEST" | grep -q "101"; then
    echo "✅ WebSocket handshake successful (HTTP 101 Switching Protocols)"
elif echo "$WS_TEST" | grep -q "400"; then
    echo "⚠️  Server responding but check WebSocket headers"
else
    echo "ℹ️  Response: $WS_TEST"
fi
echo ""

# 6. Recent server logs
echo "6️⃣  Recent server logs (last 5 lines):"
if [ -f /tmp/janet-server.log ]; then
    tail -5 /tmp/janet-server.log
else
    echo "   No log file found at /tmp/janet-server.log"
fi
echo ""

echo "=============================================="
echo "📋 Next Steps:"
echo ""
echo "To test with Postman:"
echo "  1. Create new WebSocket Request"
echo "  2. URL: wss://heyjanet.bot"
echo "  3. Connect and send: {\"type\": \"ping\"}"
echo ""
echo "To test with wscat:"
echo "  npm install -g wscat"
echo "  wscat -c wss://heyjanet.bot"
echo ""
echo "To monitor live connections:"
echo "  tail -f /tmp/janet-server.log"
