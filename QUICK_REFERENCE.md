# Janet Production Server - Quick Reference

## 🚀 Quick Start

```bash
# Start everything
cd /Users/mzxzd/Documents/JanetOS/janet-seed
nohup ./venv/bin/python3 simple_websocket_server.py > /tmp/janet-server.log 2>&1 &
launchctl start com.cloudflare.cloudflared

# Test everything
./test-heyjanet-bot.sh
```

## 🔍 Status Check

```bash
# Check if services are running
ps aux | grep simple_websocket_server.py | grep -v grep
ps aux | grep cloudflared | grep -v grep
lsof -i :8765

# Check DNS
dig heyjanet.bot +short
dig NS xn--yckwaps3i.com +short
```

## 🧪 Testing

### Local Test
```bash
cd /Users/mzxzd/Documents/JanetOS/janet-seed
./venv/bin/python3 test_websocket_client.py
```

### Postman Test
1. New → WebSocket Request
2. URL: `ws://localhost:8765` or `wss://heyjanet.bot`
3. Send: `{"type": "heartbeat"}`

## 📝 Message Examples

### Heartbeat
```json
{"type": "heartbeat"}
```

### User Message
```json
{
  "type": "user_message",
  "text": "Hello Janet!",
  "context_window": []
}
```

## 🛑 Stop Services

```bash
pkill -f "simple_websocket_server.py"
launchctl stop com.cloudflare.cloudflared
```

## 📊 Monitor Logs

```bash
tail -f /tmp/janet-server.log
```

## 🌐 URLs

- **Local**: `ws://localhost:8765`
- **Production**: `wss://heyjanet.bot`
- **Domain**: `ジャネット.com` (xn--yckwaps3i.com)

## 🔧 Troubleshooting

### DNS Not Working
```bash
# Check nameservers (should be Cloudflare)
dig NS xn--yckwaps3i.com +short
```

### Server Not Responding
```bash
# Check if listening
lsof -i :8765

# View errors
tail -20 /tmp/janet-server.log
```

### Restart Everything
```bash
pkill -f "simple_websocket_server.py"
launchctl stop com.cloudflare.cloudflared
sleep 2
cd /Users/mzxzd/Documents/JanetOS/janet-seed
nohup ./venv/bin/python3 simple_websocket_server.py > /tmp/janet-server.log 2>&1 &
launchctl start com.cloudflare.cloudflared
```

## 📁 Important Files

- Server: `simple_websocket_server.py`
- Config: `~/.cloudflared/config.yml`
- Logs: `/tmp/janet-server.log`
- Tests: `test-heyjanet-bot.sh`, `test_websocket_client.py`

## ✅ Expected DNS Values

**Nameservers**:
```
frida.ns.cloudflare.com.
henry.ns.cloudflare.com.
```

**Resolution** (after propagation):
```
heyjanet.bot → Cloudflare IPs (172.64.x.x or 104.21.x.x)
```

## 🎯 Cloudflare Tunnel

- **Name**: `janet-1772302431`
- **ID**: `69067bfd-f27c-4a86-a5f9-8c2bc839e952`
- **Service**: `com.cloudflare.cloudflared`
