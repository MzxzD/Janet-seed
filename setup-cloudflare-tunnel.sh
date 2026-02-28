#!/bin/bash
# Setup Cloudflare Tunnel for Janet production deployment

set -e

echo "🌐 Setting up Cloudflare Tunnel for Janet..."
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
  - hostname: janet.yourdomain.com
    service: ws://localhost:8765
  - service: http_status:404
EOF

echo "✅ Config file created"
echo ""

# Ask for domain
echo "🌐 DOMAIN SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "What domain do you want to use for Janet?"
echo ""
echo "Options:"
echo "  1. Use your own domain (e.g., janet.yourdomain.com)"
echo "  2. Use Cloudflare's free subdomain (e.g., janet.trycloudflare.com)"
echo ""
read -p "Enter your choice (1 or 2): " DOMAIN_CHOICE

if [ "$DOMAIN_CHOICE" = "1" ]; then
    read -p "Enter your domain (e.g., janet.yourdomain.com): " DOMAIN
    
    # Update config with custom domain
    sed -i '' "s/janet.yourdomain.com/$DOMAIN/g" $CONFIG_FILE
    
    echo ""
    echo "📋 DNS SETUP REQUIRED:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Add this CNAME record to your DNS:"
    echo ""
    cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN
    echo ""
    
    SERVER_URL="wss://$DOMAIN"
else
    # Use trycloudflare.com (no DNS needed)
    DOMAIN="$TUNNEL_ID.trycloudflare.com"
    SERVER_URL="wss://$DOMAIN"
    
    echo ""
    echo "✅ Using Cloudflare subdomain: $DOMAIN"
fi

echo ""
echo "✅ TUNNEL SETUP COMPLETE!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 NEXT STEPS:"
echo ""
echo "1. Update Config.swift with your URL:"
echo "   static let JANET_PRODUCTION_URL = \"$SERVER_URL\""
echo ""
echo "2. Start the tunnel:"
echo "   cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo "3. Start Janet server:"
echo "   cd /Users/mzxzd/Documents/JanetOS/janet-seed"
echo "   python3 simple_websocket_server.py"
echo ""
echo "4. Rebuild and install iPhone app"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Your Janet server will be accessible from anywhere!"
echo ""
echo "Tunnel URL: $SERVER_URL"
echo "Tunnel ID: $TUNNEL_ID"
echo ""
