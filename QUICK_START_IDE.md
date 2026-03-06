# Quick Start: Janet-Powered IDE

**Get Janet running in your IDE in 5 minutes!**

---

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Ollama installed ([ollama.ai](https://ollama.ai))
- [ ] VSCode installed
- [ ] At least 4GB free RAM

---

## 5-Minute Setup

### Step 1: Pull a Model (2 min)

```bash
# Fast model for autocomplete (recommended)
ollama pull tinyllama:1.1b
```

### Step 2: Install Dependencies (1 min)

```bash
cd /path/to/Janet-Projects/JanetOS/janet-seed
pip3 install fastapi uvicorn litellm
```

### Step 3: Start Janet API Server (30 sec)

```bash
./start_janet_api.sh
```

You should see:
```
============================================================
SERVER READY
============================================================
```

**Keep this terminal open!**

### Step 4: Install Continue.dev (1 min)

1. Open VSCode
2. Go to Extensions (Cmd+Shift+X)
3. Search for "Continue"
4. Click Install

### Step 5: Test It! (30 sec)

1. Press **Cmd+L** (Mac) or **Ctrl+L** (Windows/Linux)
2. Type: "Hello Janet!"
3. Watch Janet respond!

---

## What You Can Do Now

### Chat with Janet (Cmd+L)

- "Explain this function"
- "Write a Python function to sort a list"
- "How do I handle errors in async code?"

### Edit Code (Cmd+K)

1. Select some code
2. Press Cmd+K
3. Say: "Add error handling"
4. Watch Janet modify it!

### Autocomplete (Tab)

Just start typing - Janet will suggest completions.

### Reference Files (@)

- `@filename.py` - Reference a file
- `@FunctionName` - Reference a function

---

## Troubleshooting

### "Cannot connect to server"

**Fix:** Make sure `./start_janet_api.sh` is running

```bash
# Check if server is running
curl http://localhost:8080/health
```

### "Model not found"

**Fix:** Pull the model

```bash
ollama pull tinyllama:1.1b
```

### Slow responses

**Fix:** Model is too large for your hardware

```bash
# Use the fastest model
ollama pull tinyllama:1.1b
```

Then update `~/.continue/config.yaml`:
```yaml
model: tinyllama:1.1b
```

---

## Next Steps

- **Read the full guide:** [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md)
- **API documentation:** [API_REFERENCE.md](API_REFERENCE.md)
- **Try different models:** `ollama pull llama3:8b`
- **Customize Janet:** Edit `~/.continue/config.yaml`

---

## Quick Commands

```bash
# Start server
./start_janet_api.sh

# Test API
python3 test_janet_api.py

# Check health
curl http://localhost:8080/health

# List models
curl http://localhost:8080/v1/models \
  -H "Authorization: Bearer janet-local-dev"

# Stop server
Ctrl+C in the server terminal
```

---

## Configuration Files

- **API Server:** `janet_api_server.py`
- **Continue.dev Config:** `~/.continue/config.yaml`
- **Startup Script:** `start_janet_api.sh`
- **Test Suite:** `test_janet_api.py`

---

## Getting Help

- **Setup issues:** See [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md) → Troubleshooting
- **API questions:** See [API_REFERENCE.md](API_REFERENCE.md)
- **General help:** Check Janet documentation

---

**You're all set! Happy coding with Janet!** 🌱
