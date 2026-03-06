# Janet-Powered IDE - Documentation Index

**Complete guide to using Janet as your AI coding assistant**

---

## 📚 Documentation Overview

This is the central index for all Janet IDE integration documentation. Start here to find what you need.

---

## 🚀 Getting Started

### New Users Start Here

1. **[QUICK_START_IDE.md](QUICK_START_IDE.md)** ⭐ **START HERE**
   - 5-minute setup guide
   - Essential commands
   - Quick troubleshooting
   - **Best for:** First-time users who want to get running fast

2. **[JANET_IDE_SETUP.md](JANET_IDE_SETUP.md)**
   - Complete installation guide
   - Detailed configuration
   - Comprehensive troubleshooting
   - Advanced setup options
   - **Best for:** Users who want full understanding of the system

3. **[JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md)**
   - Master documentation (everything in one place)
   - Architecture overview
   - Usage guide
   - FAQ
   - **Best for:** Reference and deep understanding

---

## 📖 Core Documentation

### Setup & Installation

| Document | Purpose | Length | Audience |
|----------|---------|--------|----------|
| [QUICK_START_IDE.md](QUICK_START_IDE.md) | Get running in 5 minutes | 3KB | Beginners |
| [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md) | Complete setup guide | 14KB | All users |
| [JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md) | Master reference | 25KB | All users |

### Technical Reference

| Document | Purpose | Length | Audience |
|----------|---------|--------|----------|
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API documentation | 17KB | Developers |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Technical implementation details | 12KB | Developers |

---

## 🎯 Find What You Need

### By Task

#### "I want to get started quickly"
→ [QUICK_START_IDE.md](QUICK_START_IDE.md)

#### "I want to understand how to set everything up"
→ [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md)

#### "I want to learn how to use all the features"
→ [JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md) → Usage Guide section

#### "I'm having a problem"
→ [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md) → Troubleshooting section

#### "I want to integrate Janet into my own tool"
→ [API_REFERENCE.md](API_REFERENCE.md)

#### "I want to understand the architecture"
→ [JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md) → Architecture section

#### "I want to see what was implemented"
→ [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

### By Role

#### **End User** (Just want to code with Janet)
1. [QUICK_START_IDE.md](QUICK_START_IDE.md) - Get started
2. [JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md) - Usage guide
3. [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md) - Troubleshooting

#### **Developer** (Want to integrate or extend)
1. [API_REFERENCE.md](API_REFERENCE.md) - API details
2. [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Architecture
3. [JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md) - Development section

#### **System Administrator** (Setting up for team)
1. [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md) - Installation
2. [JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md) - Advanced topics
3. [API_REFERENCE.md](API_REFERENCE.md) - Security considerations

---

## 📁 Files & Scripts

### Executable Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `janet_api_server.py` | Main API server | Run directly or via script |
| `start_janet_api.sh` | Automated startup | Easiest way to start server |
| `test_janet_api.py` | Test suite | Verify installation |

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `config.yaml` | Continue.dev config | `~/.continue/config.yaml` |
| `requirements.txt` | Python dependencies | `janet-seed/requirements.txt` |

### Documentation Files

| File | Purpose | Size |
|------|---------|------|
| `QUICK_START_IDE.md` | Quick start guide | 3KB |
| `JANET_IDE_SETUP.md` | Complete setup | 14KB |
| `JANET_IDE_COMPLETE_GUIDE.md` | Master guide | 25KB |
| `API_REFERENCE.md` | API documentation | 17KB |
| `IMPLEMENTATION_SUMMARY.md` | Technical summary | 12KB |
| `JANET_IDE_INDEX.md` | This file | 5KB |

---

## 🔍 Quick Reference

### Common Commands

```bash
# Start server
./start_janet_api.sh

# Test installation
python3 test_janet_api.py

# Check health
curl http://localhost:8080/health

# Pull a model
ollama pull tinyllama:1.1b

# List models
ollama list
```

### Keyboard Shortcuts

| Action | Mac | Windows/Linux |
|--------|-----|---------------|
| Chat | Cmd+L | Ctrl+L |
| Inline Edit | Cmd+K | Ctrl+K |
| Autocomplete | Tab | Tab |
| Dismiss | Esc | Esc |

### Configuration Locations

```
~/.continue/config.yaml          # Continue.dev config
Janet-Projects/JanetOS/janet-seed/  # Janet files
```

---

## 📊 Documentation Map

```
Janet IDE Documentation
│
├── Quick Start (5 min)
│   └── QUICK_START_IDE.md
│
├── Complete Setup
│   ├── JANET_IDE_SETUP.md
│   └── JANET_IDE_COMPLETE_GUIDE.md
│
├── Technical Reference
│   ├── API_REFERENCE.md
│   └── IMPLEMENTATION_SUMMARY.md
│
└── This Index
    └── JANET_IDE_INDEX.md
```

---

## 🎓 Learning Path

### Beginner Path

1. **Read:** [QUICK_START_IDE.md](QUICK_START_IDE.md)
2. **Do:** Follow the 5-minute setup
3. **Try:** Press Cmd+L and chat with Janet
4. **Learn:** Read [JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md) Usage Guide

### Intermediate Path

1. **Read:** [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md)
2. **Configure:** Customize models and settings
3. **Explore:** Try all features (chat, edit, autocomplete)
4. **Optimize:** Tune performance for your hardware

### Advanced Path

1. **Read:** [API_REFERENCE.md](API_REFERENCE.md)
2. **Integrate:** Build custom tools using Janet API
3. **Extend:** Add new features or models
4. **Contribute:** Improve Janet for everyone

---

## 🆘 Troubleshooting Quick Links

### Common Issues

- **Server won't start** → [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md#server-wont-start)
- **Connection failed** → [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md#connection-failed-in-continuedev)
- **Slow responses** → [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md#slow-responses)
- **Model not found** → [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md#model-not-found)
- **Autocomplete not working** → [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md#autocomplete-not-working)

### Getting Help

1. Check the troubleshooting section in setup guide
2. Run the test suite: `python3 test_janet_api.py`
3. Check server logs
4. Review configuration files

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial release - Complete implementation |

---

## 🔗 External Resources

- **Continue.dev Documentation:** https://docs.continue.dev
- **Ollama Documentation:** https://ollama.ai/docs
- **Janet Main Project:** See main repository
- **VSCode Documentation:** https://code.visualstudio.com/docs

---

## 📝 Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| QUICK_START_IDE.md | ✅ Complete | 2026-03-02 |
| JANET_IDE_SETUP.md | ✅ Complete | 2026-03-02 |
| JANET_IDE_COMPLETE_GUIDE.md | ✅ Complete | 2026-03-02 |
| API_REFERENCE.md | ✅ Complete | 2026-03-02 |
| IMPLEMENTATION_SUMMARY.md | ✅ Complete | 2026-03-02 |
| JANET_IDE_INDEX.md | ✅ Complete | 2026-03-02 |

---

## 🎯 Next Steps

**New to Janet IDE?**
1. Start with [QUICK_START_IDE.md](QUICK_START_IDE.md)
2. Get running in 5 minutes
3. Come back here for more resources

**Ready to dive deeper?**
1. Read [JANET_IDE_COMPLETE_GUIDE.md](JANET_IDE_COMPLETE_GUIDE.md)
2. Explore all features
3. Customize to your needs

**Want to integrate or extend?**
1. Study [API_REFERENCE.md](API_REFERENCE.md)
2. Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
3. Build amazing things!

---

**Welcome to Janet-Powered IDE!** 🌱

*Your constitutional AI coding companion*

---

**Index Version:** 1.0.0  
**Last Updated:** March 2, 2026  
**Maintained by:** Janet Project
