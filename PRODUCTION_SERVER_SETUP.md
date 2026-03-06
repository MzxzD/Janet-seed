# Janet Production Server Setup & Testing

## Overview

This document covers the complete setup, configuration, and testing of the Janet WebSocket production server accessible at `wss://heyjanet.bot`.

## Architecture

```
iPhone/Client
    ↓
wss://heyjanet.bot (Public Domain)
    ↓
Cloudflare Tunnel (janet-1772302431)
    ↓
ws://localhost:8765 (Local WebSocket Server)
    ↓
simple_websocket_server.py (Janet Brain)
```

## Components

### 1. WebSocket Server
- **File**: `simple_websocket_server.py`
- **Port**: 8765
- **Protocol**: WebSocket (ws://)
- **Location**: `/Users/mzxzd/Documents/JanetOS/janet-seed/`
- **Log**: `/tmp/janet-server.log`

### 2. Cloudflare Tunnel
- **Name**: `janet-1772302431`
- **ID**: `69067bfd-f27c-4a86-a5f9-8c2bc839e952`
- **Config**: `~/.cloudflared/config.yml`
- **Service**: macOS LaunchAgent (`com.cloudflare.cloudflared`)

### 3. DNS Configuration
- **Domain**: `ジャネット.com` (xn--yckwaps3i.com)
- **Subdomain**: `heyjanet.bot`
- **Nameservers**: 
  - `frida.ns.cloudflare.com`
  - `henry.ns.cloudflare.com`
- **Registrar**: Namecheap

## Setup Steps

### 1. Configure Cloudflare Tunnel

The tunnel is already configured in `~/.cloudflared/config.yml`:

```yaml
tunnel: 69067bfd-f27c-4a86-a5f9-8c2bc839e952
credentials-file: ~/.cloudflared/69067bfd-f27c-4a86-a5f9-8c2bc839e952.json

ingress:
  - hostname: heyjanet.bot
    service: ws://localhost:8765
  - hostname: xn--yckwaps3i.com
    service: ws://localhost:8765
  - hostname: ジャネット.com
    service: ws://localhost:8765
  - service: http_status:404
```

### 2. Configure DNS at Namecheap

**Domain**: `xn--yckwaps3i.com` (ジャネット.com)

1. Log into Namecheap
2. Go to Domain List → Manage `xn--yckwaps3i.com`
3. Change DNS from "Namecheap BasicDNS" to "Custom DNS"
4. Add nameservers:
   - `frida.ns.cloudflare.com`
   - `henry.ns.cloudflare.com`
5. Save changes

**Propagation Time**: 15-30 minutes (up to 48 hours maximum)

### 3. Configure DNS Records in Cloudflare

The CNAME record for `heyjanet.bot` is already configured in Cloudflare:

```
Type: CNAME
Name: heyjanet.bot
Target: 69067bfd-f27c-4a86-a5f9-8c2bc839e952.cfargotunnel.com
Proxied: Yes
```

## Starting Services

### Start WebSocket Server

```bash
cd /Users/mzxzd/Documents/JanetOS/janet-seed
nohup ./venv/bin/python3 simple_websocket_server.py > /tmp/janet-server.log 2>&1 &
```

**Verify**:
```bash
ps aux | grep simple_websocket_server.py | grep -v grep
lsof -i :8765
```

### Start Cloudflare Tunnel

```bash
launchctl start com.cloudflare.cloudflared
```

**Verify**:
```bash
ps aux | grep cloudflared | grep -v grep
```

### Stop Services

```bash
# Stop WebSocket server
pkill -f "simple_websocket_server.py"

# Stop Cloudflare tunnel
launchctl stop com.cloudflare.cloudflared
```

## Testing

### Automated Test Script

```bash
cd /Users/mzxzd/Documents/JanetOS/janet-seed
./test-heyjanet-bot.sh
```

This checks:
- DNS resolution
- HTTPS endpoint
- Local server status
- Cloudflare tunnel status
- WebSocket handshake
- Recent server logs

### Python WebSocket Test Client

```bash
cd /Users/mzxzd/Documents/JanetOS/janet-seed
./venv/bin/python3 test_websocket_client.py
```

Tests both local and production endpoints with proper message formats.

### Manual Testing with Postman

#### Local Server (ws://localhost:8765)

1. Open Postman
2. New → **WebSocket Request**
3. URL: `ws://localhost:8765`
4. Click **Connect**
5. Send test messages:

**Heartbeat**:
```json
{"type": "heartbeat"}
```

**User Message**:
```json
{
  "type": "user_message",
  "text": "Hello Janet!",
  "context_window": []
}
```

#### Production Server (wss://heyjanet.bot)

Same steps as above, but use URL: `wss://heyjanet.bot`

**Note**: Only works after DNS propagation is complete.

### Command Line Testing

#### Check DNS Propagation

```bash
# Check nameservers (should show Cloudflare)
dig NS xn--yckwaps3i.com +short

# Check heyjanet.bot resolution (should show Cloudflare IPs)
dig heyjanet.bot +short
```

**Expected after propagation**:
```
frida.ns.cloudflare.com.
henry.ns.cloudflare.com.
```

#### Test WebSocket with curl

```bash
# Test local
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  http://localhost:8765

# Test production (after DNS propagation)
curl -i --connect-timeout 10 --max-time 15 https://heyjanet.bot
```

#### Monitor Server Logs

```bash
tail -f /tmp/janet-server.log
```

## Message Protocol

The Janet WebSocket server expects specific message types:

### Client → Server

#### Heartbeat
```json
{"type": "heartbeat"}
```

**Response**:
```json
{"type": "heartbeat_ack"}
```

#### User Message
```json
{
  "type": "user_message",
  "text": "Your message here",
  "context_window": []
}
```

**Response**:
```json
{
  "type": "janet_response",
  "text": "Janet's response",
  "timestamp": "2026-03-01T12:00:00.000000"
}
```

#### End Conversation
```json
{
  "type": "end_conversation",
  "context_window": [...]
}
```

**Response**:
```json
{
  "type": "summary",
  "summary": {
    "id": "...",
    "timestamp": "...",
    "topics": [...],
    "summary": "...",
    "emotionalTone": "neutral",
    "actionableInsights": []
  }
}
```

#### Get Summaries
```json
{"type": "get_green_vault_summaries"}
```

**Response**:
```json
{
  "type": "summaries",
  "summaries": []
}
```

#### Dynamic Shortcuts
```json
{
  "type": "recognize_intent",
  "text": "..."
}
```

Other shortcut types: `create_shortcut`, `build_shortcut`, `get_shortcuts`, `save_shortcut`, `delete_shortcut`

## Troubleshooting

### DNS Not Propagating

**Check current nameservers**:
```bash
dig NS xn--yckwaps3i.com +short
```

If still showing `dns1.registrar-servers.com`, wait longer (15-30 minutes typical).

**Force DNS refresh** (on your machine):
```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### Server Not Starting

**Check for errors**:
```bash
cd /Users/mzxzd/Documents/JanetOS/janet-seed
./venv/bin/python3 simple_websocket_server.py
```

**Common issues**:
- Port 8765 already in use: `lsof -i :8765` and kill the process
- Missing dependencies: `./venv/bin/pip install websockets`
- Python version: Requires Python 3.14+

### Tunnel Not Working

**Check tunnel status**:
```bash
cloudflared tunnel info janet-1772302431
```

**View tunnel logs**:
```bash
tail -f ~/Library/Logs/com.cloudflare.cloudflared.err.log
```

**Restart tunnel**:
```bash
launchctl stop com.cloudflare.cloudflared
launchctl start com.cloudflare.cloudflared
```

### Connection Errors

**"missing Sec-WebSocket-Key header"**:
- This is expected for HTTP requests to a WebSocket endpoint
- Use proper WebSocket client (Postman, wscat, or test script)

**"received 1011 (internal error)"**:
- Server received message but couldn't process it
- Check message format matches expected protocol
- Check server logs: `tail -f /tmp/janet-server.log`

**"Connection timeout"**:
- DNS hasn't propagated yet (check with `dig`)
- Tunnel not running (check with `ps aux | grep cloudflared`)
- Server not running (check with `lsof -i :8765`)

## Files Reference

### Configuration Files
- `~/.cloudflared/config.yml` - Tunnel configuration
- `~/.cloudflared/69067bfd-f27c-4a86-a5f9-8c2bc839e952.json` - Tunnel credentials

### Server Files
- `simple_websocket_server.py` - Main WebSocket server
- `src/handlers/shortcut_handler.py` - Dynamic shortcuts handler

### Test Files
- `test-heyjanet-bot.sh` - Automated test script
- `test_websocket_client.py` - Python WebSocket test client
- `verify-heyjanet-bot.sh` - DNS verification script
- `ACTIVATE_HEYJANET_BOT.md` - Manual DNS setup guide

### Log Files
- `/tmp/janet-server.log` - WebSocket server logs
- `~/Library/Logs/com.cloudflare.cloudflared.err.log` - Tunnel error logs

## Production Checklist

Before deploying:

- [ ] WebSocket server running on port 8765
- [ ] Cloudflare tunnel running and connected
- [ ] DNS nameservers updated at Namecheap
- [ ] DNS propagation complete (verify with `dig`)
- [ ] Local testing successful (`ws://localhost:8765`)
- [ ] Production testing successful (`wss://heyjanet.bot`)
- [ ] Ollama running for LLM responses (optional)
- [ ] Server logs monitored for errors

## Monitoring

### Check Service Health

```bash
# Quick health check
./test-heyjanet-bot.sh

# Detailed check
ps aux | grep -E "simple_websocket_server|cloudflared" | grep -v grep
lsof -i :8765
dig heyjanet.bot +short
```

### Monitor Logs

```bash
# Server logs
tail -f /tmp/janet-server.log

# Tunnel logs
tail -f ~/Library/Logs/com.cloudflare.cloudflared.err.log
```

## Security Notes

- WebSocket server runs on localhost only (not exposed directly)
- All external traffic goes through Cloudflare Tunnel (encrypted)
- Cloudflare provides DDoS protection
- Domain privacy enabled at Namecheap
- Tunnel credentials stored in `~/.cloudflared/` (keep secure)

## Support

For issues:
1. Check logs: `/tmp/janet-server.log`
2. Verify DNS: `dig heyjanet.bot +short`
3. Test locally first: `ws://localhost:8765`
4. Run test script: `./test-heyjanet-bot.sh`

## Related Documentation

- `PRODUCTION_DEPLOYMENT.md` - General deployment guide
- `ACTIVATE_HEYJANET_BOT.md` - Manual DNS setup instructions
- Cloudflare Tunnel docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
