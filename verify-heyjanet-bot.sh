#!/bin/bash
# Verify heyjanet.bot is working with Cloudflare Tunnel

echo "🔍 Verifying heyjanet.bot setup..."
echo ""

echo "1. Checking DNS resolution..."
DNS_IPS=$(dig heyjanet.bot +short)
echo "   Current IPs: $DNS_IPS"

if echo "$DNS_IPS" | grep -q "172.64\|104."; then
    echo "   ✅ DNS pointing to Cloudflare!"
else
    echo "   ❌ DNS NOT pointing to Cloudflare (should see 172.64.x.x or 104.x.x.x)"
    echo ""
    echo "   ACTION NEEDED:"
    echo "   1. Go to https://dash.cloudflare.com"
    echo "   2. Select your domain (ジャネット.com or xn--yckwaps3i.com)"
    echo "   3. Go to DNS → Records"
    echo "   4. Find 'heyjanet.bot' record"
    echo "   5. Delete the A records (34.216.117.25, 54.149.79.189)"
    echo "   6. Add CNAME record:"
    echo "      Name: heyjanet.bot"
    echo "      Target: 69067bfd-f27c-4a86-a5f9-8c2bc839e952.cfargotunnel.com"
    echo "      Proxy: ON (orange cloud)"
    exit 1
fi

echo ""
echo "2. Checking local server..."
if lsof -i :8765 > /dev/null 2>&1; then
    echo "   ✅ WebSocket server running on port 8765"
else
    echo "   ❌ WebSocket server NOT running"
    exit 1
fi

echo ""
echo "3. Checking Cloudflare tunnel..."
if ps aux | grep -q "[c]loudflared tunnel run"; then
    echo "   ✅ Cloudflare tunnel running"
else
    echo "   ❌ Cloudflare tunnel NOT running"
    exit 1
fi

echo ""
echo "4. Testing external connectivity..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 https://heyjanet.bot 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "000" ]; then
    echo "   ❌ Cannot connect to heyjanet.bot (timeout)"
    echo "   DNS may still be propagating. Wait 5 minutes and try again."
    exit 1
elif [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "426" ]; then
    echo "   ✅ Server responding! (HTTP $HTTP_CODE - WebSocket handshake expected)"
else
    echo "   ⚠️  Server responding with HTTP $HTTP_CODE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 SUCCESS! heyjanet.bot is working!"
echo ""
echo "   Production URL: wss://heyjanet.bot"
echo ""
echo "   Your iOS/Watch apps can now connect from anywhere!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
