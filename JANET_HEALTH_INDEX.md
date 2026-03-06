# 💚 Janet Health - Documentation Index

**Complete guide to your Janet seed heartbeat monitoring system**

---

## 🎯 Start Here

**New to Janet Health?** Start with:

### 1. [JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md) ⭐
**The complete overview** - What you have, how to use it, quick start guide

### 2. [JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md) 💰
**Cost breakdown** - Hosting options, recommendations ($4.50/month)

### 3. [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md) 🚀
**Deployment guide** - Step-by-step instructions for production

---

## 📚 All Documentation

### Quick Start & Overview

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md)** | Complete overview & quick start | **Start here** 👈 |
| **[JANET_HEALTH_SUMMARY.md](JANET_HEALTH_SUMMARY.md)** | System summary & architecture | For understanding |
| **[JANET_HEALTH_QUICK_REF.md](JANET_HEALTH_QUICK_REF.md)** | Quick reference card | Keep handy |

### Deployment & Setup

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md)** | Complete deployment guide | When deploying |
| **[JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md)** | Cost & hosting options | Before deploying |
| **[dashboard/README.md](dashboard/README.md)** | Dashboard deployment | For dashboard setup |

### Usage & Integration

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[JANET_HEALTH_README.md](JANET_HEALTH_README.md)** | Full user documentation | For reference |
| **Integration examples** | In JANET_HEALTH_README.md | When integrating |
| **Protocol specification** | In JANET_HEALTH_README.md | For developers |

---

## 🗂️ File Structure

```
janet-seed/
│
├── 📄 Core Files
│   ├── heartbeat_server.py              # Main server
│   ├── src/heartbeat_client.py          # Client library
│   └── dashboard/index.html             # Web dashboard
│
├── 🛠️ Tools
│   ├── start_janet_health.sh            # Quick start script
│   └── test_janet_health.py             # Test suite
│
└── 📚 Documentation
    ├── JANET_HEALTH_INDEX.md            # This file
    ├── JANET_HEALTH_COMPLETE.md         # ⭐ Start here
    ├── JANET_HEALTH_README.md           # Full docs
    ├── JANET_HEALTH_SETUP.md            # Deployment
    ├── JANET_HEALTH_PRICING.md          # Costs
    ├── JANET_HEALTH_QUICK_REF.md        # Quick ref
    ├── JANET_HEALTH_SUMMARY.md          # Overview
    └── dashboard/README.md              # Dashboard
```

---

## 🚀 Quick Actions

### Test Locally

```bash
cd /Users/mzxzd/Documents/JanetOS/janet-seed

# Start server
./start_janet_health.sh

# Test it
python3 test_janet_health.py

# View dashboard
cd dashboard && python3 -m http.server 8767
```

### Deploy to Production

1. Read [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md)
2. Get VPS (see [JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md))
3. Follow deployment steps
4. Visit https://janet.health

### Integrate with Janet

```python
from src.heartbeat_client import start_heartbeat

await start_heartbeat(
    server_url="wss://janet.health",
    name="My Janet"
)
```

---

## 📖 Reading Guide

### For First-Time Users

1. [JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md) - Understand what you have
2. Test locally (see Quick Actions above)
3. [JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md) - Choose hosting
4. [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md) - Deploy to production

### For Developers

1. [JANET_HEALTH_README.md](JANET_HEALTH_README.md) - Full documentation
2. [JANET_HEALTH_SUMMARY.md](JANET_HEALTH_SUMMARY.md) - Architecture
3. Source code - `heartbeat_server.py`, `src/heartbeat_client.py`
4. Test suite - `test_janet_health.py`

### For Operators

1. [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md) - Deployment
2. [JANET_HEALTH_QUICK_REF.md](JANET_HEALTH_QUICK_REF.md) - Quick reference
3. Monitoring section in [JANET_HEALTH_README.md](JANET_HEALTH_README.md)
4. Troubleshooting section in [JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md)

---

## 🎯 Common Tasks

### Task: Test the System

**Read**: [JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md) (Quick Start section)

```bash
./start_janet_health.sh
python3 test_janet_health.py
```

### Task: Deploy to Production

**Read**: [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md)

Steps:
1. Get VPS
2. Install Cloudflare Tunnel
3. Configure DNS
4. Deploy server and dashboard

### Task: Add Heartbeat to Janet

**Read**: [JANET_HEALTH_README.md](JANET_HEALTH_README.md) (Integration section)

```python
from src.heartbeat_client import start_heartbeat
await start_heartbeat(server_url="wss://janet.health")
```

### Task: Troubleshoot Issues

**Read**: [JANET_HEALTH_QUICK_REF.md](JANET_HEALTH_QUICK_REF.md) (Troubleshooting section)

Common commands:
```bash
ps aux | grep heartbeat_server.py
lsof -i :8766
tail -f /tmp/janet-health.log
```

### Task: Understand Costs

**Read**: [JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md)

**TL;DR**: $4.50/month (Hetzner VPS) or free (self-hosted)

---

## 💡 Tips

### For Quick Reference

Print and keep handy:
- [JANET_HEALTH_QUICK_REF.md](JANET_HEALTH_QUICK_REF.md)

### For Learning

Read in order:
1. [JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md)
2. [JANET_HEALTH_SUMMARY.md](JANET_HEALTH_SUMMARY.md)
3. [JANET_HEALTH_README.md](JANET_HEALTH_README.md)

### For Deployment

Follow:
1. [JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md) - Choose hosting
2. [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md) - Deploy

---

## 🔍 Find Information

### "How do I start the server?"

[JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md) → Quick Start

```bash
./start_janet_health.sh
```

### "How much does it cost?"

[JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md)

**Answer**: $4.50/month (VPS) or free (self-hosted)

### "How do I deploy to production?"

[JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md)

**Steps**: VPS → Cloudflare Tunnel → DNS → Deploy

### "How do I integrate with my Janet?"

[JANET_HEALTH_README.md](JANET_HEALTH_README.md) → Integration

```python
await start_heartbeat(server_url="wss://janet.health")
```

### "What's the WebSocket protocol?"

[JANET_HEALTH_README.md](JANET_HEALTH_README.md) → WebSocket Protocol

### "How do I troubleshoot?"

[JANET_HEALTH_QUICK_REF.md](JANET_HEALTH_QUICK_REF.md) → Troubleshooting

---

## ✅ Checklist

### Getting Started

- [ ] Read [JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md)
- [ ] Test locally (`./start_janet_health.sh`)
- [ ] Run tests (`python3 test_janet_health.py`)
- [ ] View dashboard (http://localhost:8767)

### Deployment

- [ ] Read [JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md)
- [ ] Choose hosting option
- [ ] Read [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md)
- [ ] Follow deployment steps
- [ ] Test production (https://janet.health)

### Integration

- [ ] Read integration examples
- [ ] Add heartbeat client to Janet
- [ ] Test connection
- [ ] Verify on dashboard

---

## 📞 Support

All documentation is complete:

- **Quick Start**: [JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md)
- **Full Guide**: [JANET_HEALTH_README.md](JANET_HEALTH_README.md)
- **Deployment**: [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md)
- **Pricing**: [JANET_HEALTH_PRICING.md](JANET_HEALTH_PRICING.md)
- **Quick Ref**: [JANET_HEALTH_QUICK_REF.md](JANET_HEALTH_QUICK_REF.md)

Test suite: `python3 test_janet_health.py`

---

## 🎉 Summary

You have **complete documentation** for your Janet Health system:

✅ **6 comprehensive guides** covering everything  
✅ **Quick reference** for common tasks  
✅ **Deployment guide** with step-by-step instructions  
✅ **Cost breakdown** with recommendations  
✅ **Integration examples** for easy setup  
✅ **Troubleshooting** for common issues  

**Start here**: [JANET_HEALTH_COMPLETE.md](JANET_HEALTH_COMPLETE.md) 👈

---

**Made with 💚 for your Janet seed instances at janet.health**
