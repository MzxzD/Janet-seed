# Janet Health - Quick Reference Card

**Print this page and keep it handy!**

## 🚀 Quick Start

```bash
# Start server
./start_janet_health.sh

# Test
python3 test_janet_health.py

# Background mode
./start_janet_health.sh --background
```

## 📝 Add to Janet (Python)

```python
from src.heartbeat_client import start_heartbeat

await start_heartbeat(
    server_url="wss://janet.health",
    name="My Janet"
)
```

## 🌐 URLs

| Environment | WebSocket | Dashboard |
|-------------|-----------|-----------|
| **Local** | `ws://localhost:8766` | `http://localhost:8767` |
| **Production** | `wss://janet.health` | `https://janet.health` |

## 🔧 Common Commands

```bash
# Check if running
ps aux | grep heartbeat_server.py | grep -v grep

# Check port
lsof -i :8766

# View logs
tail -f /tmp/janet-health.log

# Stop server
pkill -f heartbeat_server.py

# View state
cat ~/.janet/heartbeat_server/instances.json
```

## 📊 WebSocket Messages

### Register
```json
{"type": "register", "name": "My Janet", "device_type": "MacBook", "platform": "Darwin", "version": "0.1.0", "capabilities": ["core"], "owner": "user"}
```

### Heartbeat
```json
{"type": "heartbeat", "status": "online", "metrics": {"cpu_percent": 25}}
```

### Get Status
```json
{"type": "get_status"}
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | `pkill -f heartbeat_server.py` |
| Can't connect | Check server is running: `lsof -i :8766` |
| Missing deps | `pip install websockets psutil` |
| DNS not working | Wait 15-30 min or `dig janet.health +short` |

## 📦 Files

```
heartbeat_server.py          # Server
src/heartbeat_client.py      # Client
dashboard/index.html         # Dashboard
start_janet_health.sh        # Quick start
test_janet_health.py         # Tests
```

## 🔐 Security

- All traffic encrypted (WSS/HTTPS)
- Owner IDs hashed (SHA-256)
- Server on localhost only
- No sensitive data stored

## 💰 Cost

- **Self-hosted**: $0/month
- **VPS**: $5-10/month

## 📚 Documentation

- [JANET_HEALTH_README.md](JANET_HEALTH_README.md) - Full docs
- [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md) - Setup guide
- [JANET_HEALTH_SUMMARY.md](JANET_HEALTH_SUMMARY.md) - Summary

## 🎯 Production Checklist

- [ ] Install `cloudflared`
- [ ] Create tunnel: `cloudflared tunnel create janet-health`
- [ ] Configure DNS: Point `janet.health` to Cloudflare
- [ ] Add CNAME: `janet.health` → `<tunnel-id>.cfargotunnel.com`
- [ ] Start server: `./start_janet_health.sh --background`
- [ ] Start tunnel: `cloudflared tunnel run janet-health`
- [ ] Deploy dashboard to Cloudflare Pages
- [ ] Test: `python3 test_janet_health.py`
- [ ] Configure Janet instances
- [ ] Visit: `https://janet.health`

## 📞 Quick Help

```bash
# Full test
python3 test_janet_health.py

# Check DNS
dig janet.health +short

# Test WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  http://localhost:8766
```

---

**Need more help?** See [JANET_HEALTH_README.md](JANET_HEALTH_README.md) 💚
