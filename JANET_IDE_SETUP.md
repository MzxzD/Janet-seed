# Janet IDE Setup Guide

**Transform your IDE into a Cursor-like experience powered by Janet's Constitutional AI**

This guide will help you set up Continue.dev with Janet as your primary LLM, giving you AI-powered coding assistance that's:
- ✅ **Offline-first** - Works without internet
- ✅ **Privacy-first** - Your code never leaves your machine
- ✅ **Constitutional** - Follows 16 axioms including transparency and user sovereignty
- ✅ **Open source** - Full control over your AI assistant

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)
7. [FAQ](#faq)

---

## Prerequisites

### Required Software

1. **Python 3.8+**
   ```bash
   python3 --version  # Should be 3.8 or higher
   ```

2. **Ollama** (for local LLM)
   - Download from: https://ollama.ai
   - macOS: `brew install ollama`
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`
   - Windows: Download installer from website

3. **VSCode** (or VSCodium)
   - Download from: https://code.visualstudio.com

4. **Continue.dev Extension**
   - Install from VSCode marketplace
   - Search for "Continue" in Extensions (Cmd+Shift+X)
   - Or visit: https://marketplace.visualstudio.com/items?itemName=Continue.continue

### Recommended Models

Pull at least one model before starting:

```bash
# Fast model for autocomplete (recommended)
ollama pull tinyllama:1.1b

# Balanced model for general use (recommended)
ollama pull llama3:8b

# Optional: Powerful model for complex tasks
ollama pull llama3:70b

# Optional: Embeddings for codebase search
ollama pull nomic-embed-text
```

---

## Installation

### Step 1: Install Janet Dependencies

Navigate to the janet-seed directory and install Python dependencies:

```bash
cd /path/to/Janet-Projects/JanetOS/janet-seed
pip3 install -r requirements.txt
```

This will install:
- FastAPI (API server framework)
- uvicorn (ASGI server)
- litellm (LLM integration)
- And other Janet dependencies

### Step 2: Verify Installation

Check that everything is installed correctly:

```bash
# Check Python packages
python3 -c "import fastapi, uvicorn, litellm; print('✅ All packages installed')"

# Check Ollama
ollama list

# Check Janet brain
python3 -c "from src.core.janet_brain import JanetBrain; print('✅ Janet brain available')"
```

### Step 3: Start Janet API Server

Start the API server that bridges Janet and Continue.dev:

```bash
# Option 1: Use the startup script (recommended)
./start_janet_api.sh

# Option 2: Start directly
python3 janet_api_server.py

# Option 3: Custom configuration
JANET_API_PORT=8080 JANET_DEFAULT_MODEL=llama3:8b python3 janet_api_server.py
```

You should see:

```
============================================================
JANET API SERVER - Constitutional AI for IDEs
============================================================

Configuration:
  Host: 0.0.0.0
  Port: 8080
  Default Model: tinyllama:1.1b
  Authentication: Enabled

🌱 Initializing Janet Brain...
✅ JanetBrain initialized with tinyllama:1.1b
   Available models: tinyllama:1.1b, llama3:8b

============================================================
SERVER READY
============================================================

API Endpoint: http://0.0.0.0:8080/v1/chat/completions
...
```

**Keep this terminal open** - the server needs to run while you code.

### Step 4: Test the API Server

In a **new terminal**, run the test suite:

```bash
cd /path/to/Janet-Projects/JanetOS/janet-seed
python3 test_janet_api.py
```

You should see all tests pass:

```
============================================================
JANET API SERVER TEST SUITE
============================================================

Testing /health endpoint...
✅ Health check passed
   Status: healthy
   Brain available: True
   Current model: tinyllama:1.1b
   ...

Results: 5/5 tests passed

🎉 All tests passed! Janet API server is working correctly.
```

### Step 5: Configure Continue.dev

The configuration file has already been created at `~/.continue/config.yaml`.

To verify or customize it:

```bash
# View the config
cat ~/.continue/config.yaml

# Or edit it
code ~/.continue/config.yaml  # Opens in VSCode
```

### Step 6: Restart VSCode

1. Close and reopen VSCode
2. Or reload the window: Cmd+Shift+P → "Developer: Reload Window"

---

## Configuration

### Basic Configuration

The default configuration connects Continue.dev to Janet with these settings:

```yaml
models:
  - name: Janet
    provider: openai
    model: janet-constitutional-ai
    apiBase: http://localhost:8080/v1
    apiKey: janet-local-dev
    title: Janet (Constitutional AI)
```

### Model Selection

You can configure multiple models for different tasks:

| Model | Use Case | Speed | Quality |
|-------|----------|-------|---------|
| `tinyllama:1.1b` | Autocomplete, quick tasks | ⚡⚡⚡ | ⭐⭐ |
| `llama3:8b` | General coding, explanations | ⚡⚡ | ⭐⭐⭐⭐ |
| `llama3:70b` | Complex reasoning, architecture | ⚡ | ⭐⭐⭐⭐⭐ |

### Environment Variables

Customize the API server with environment variables:

```bash
# Port (default: 8080)
export JANET_API_PORT=8080

# Host (default: 0.0.0.0)
export JANET_API_HOST=0.0.0.0

# Default model (default: tinyllama:1.1b)
export JANET_DEFAULT_MODEL=llama3:8b

# API key (default: janet-local-dev)
export JANET_API_KEY=your-custom-key

# Then start the server
python3 janet_api_server.py
```

---

## Usage

### Chat Interface (Cmd+L / Ctrl+L)

Open the chat sidebar to have conversations with Janet:

1. Press **Cmd+L** (Mac) or **Ctrl+L** (Windows/Linux)
2. Type your question or request
3. Janet will respond with code, explanations, or suggestions

**Examples:**
- "Explain this function"
- "Write a Python function to parse JSON"
- "How do I handle errors in async functions?"
- "Refactor this code for better performance"

### Inline Editing (Cmd+K / Ctrl+K)

Edit code directly with AI assistance:

1. Select code you want to modify
2. Press **Cmd+K** (Mac) or **Ctrl+K** (Windows/Linux)
3. Describe the change you want
4. Janet will suggest modifications

**Examples:**
- "Add error handling"
- "Convert to async/await"
- "Add type hints"
- "Optimize for performance"

### Autocomplete (Tab)

Get AI-powered code suggestions as you type:

1. Start typing code
2. Wait for suggestions to appear
3. Press **Tab** to accept

Autocomplete uses the fast model (TinyLlama) for instant responses.

### Codebase Context (@-mentions)

Reference files and symbols in your questions:

- `@filename.py` - Reference a specific file
- `@FunctionName` - Reference a function or class
- `@folder/` - Reference a directory

**Example:**
```
@app.py How does the authentication middleware work?
```

### Custom Commands

Janet includes special constitutional commands:

1. **Constitutional Check**
   - Command: `/constitutional-check`
   - Reviews code against Janet's 16 axioms
   - Checks privacy, transparency, user sovereignty

2. **Explain Constitutionally**
   - Command: `/explain-constitutionally`
   - Explains code with constitutional principles

3. **Secure Refactor**
   - Command: `/secure-refactor`
   - Refactors code for security and privacy

### Red Thread Emergency Stop

If Janet starts doing something unexpected:

1. Type "red thread" in any conversation
2. All operations will immediately stop
3. This is part of Janet's constitutional design

---

## Troubleshooting

### Server Won't Start

**Problem:** `janet_api_server.py` fails to start

**Solutions:**
1. Check Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

2. Verify Ollama is running:
   ```bash
   ollama list
   ```

3. Check if port is in use:
   ```bash
   lsof -i :8080  # macOS/Linux
   netstat -ano | findstr :8080  # Windows
   ```

4. Try a different port:
   ```bash
   JANET_API_PORT=8081 python3 janet_api_server.py
   ```

### Connection Failed in Continue.dev

**Problem:** "Failed to connect to model"

**Solutions:**
1. Verify API server is running:
   ```bash
   curl http://localhost:8080/health
   ```

2. Check Continue.dev config:
   ```bash
   cat ~/.continue/config.yaml
   ```

3. Verify API key matches:
   - Server default: `janet-local-dev`
   - Config should match

4. Check VSCode logs:
   - Open Command Palette (Cmd+Shift+P)
   - "Developer: Show Logs"
   - Select "Extension Host"

### Slow Responses

**Problem:** Janet takes too long to respond

**Solutions:**
1. Switch to a faster model:
   ```yaml
   model: tinyllama:1.1b  # Fastest
   ```

2. Reduce max_tokens:
   ```yaml
   max_tokens: 500  # Shorter responses
   ```

3. Check system resources:
   ```bash
   # macOS
   top -o cpu
   
   # Linux
   htop
   ```

4. Use GPU acceleration (if available):
   - Ollama automatically uses GPU
   - Check with: `ollama run llama3:8b --verbose`

### Model Not Found

**Problem:** "Model not available"

**Solutions:**
1. Pull the model:
   ```bash
   ollama pull tinyllama:1.1b
   ```

2. List available models:
   ```bash
   ollama list
   ```

3. Update config to use available model:
   ```yaml
   model: <model-from-list>
   ```

### Autocomplete Not Working

**Problem:** No autocomplete suggestions

**Solutions:**
1. Check tabAutocompleteModel in config:
   ```yaml
   tabAutocompleteModel:
     name: Janet Fast
     model: tinyllama:1.1b
   ```

2. Verify fast model is pulled:
   ```bash
   ollama pull tinyllama:1.1b
   ```

3. Restart VSCode

4. Check Continue.dev settings:
   - Settings → Extensions → Continue
   - Enable "Tab Autocomplete"

---

## Advanced Configuration

### Multiple Model Profiles

Configure different models for different scenarios:

```yaml
models:
  # Fast: Quick tasks
  - name: Janet Fast
    model: tinyllama:1.1b
    contextLength: 2048
    
  # Balanced: General use
  - name: Janet
    model: llama3:8b
    contextLength: 8192
    
  # Pro: Complex tasks
  - name: Janet Pro
    model: llama3:70b
    contextLength: 8192
    
  # Code: Specialized for code
  - name: Janet Code
    model: codellama:13b
    contextLength: 16384
```

### Custom System Message

Customize Janet's personality:

```yaml
systemMessage: |
  You are Janet, a constitutional AI coding assistant.
  
  Your style:
  - Concise but thorough
  - Focus on best practices
  - Always consider edge cases
  - Explain trade-offs
  
  Your priorities:
  1. Correctness
  2. Security
  3. Performance
  4. Maintainability
```

### Context Providers

Control what Janet can access:

```yaml
contextProviders:
  - name: code          # Current file
  - name: diff          # Git changes
  - name: terminal      # Terminal output
  - name: problems      # Linter errors
  - name: folder        # Workspace files
  - name: codebase      # Semantic search
```

### Performance Tuning

Optimize for your hardware:

```yaml
performance:
  # Debounce autocomplete (ms)
  autocompleteDebounce: 300
  
  # Max concurrent requests
  maxConcurrentRequests: 3
  
  # Request timeout (ms)
  requestTimeout: 30000
```

### Running on Different Port

If port 8080 is in use:

1. Update server:
   ```bash
   JANET_API_PORT=8081 python3 janet_api_server.py
   ```

2. Update config:
   ```yaml
   apiBase: http://localhost:8081/v1
   ```

### Remote Janet Server

Run Janet on a different machine:

1. Start server with external access:
   ```bash
   JANET_API_HOST=0.0.0.0 python3 janet_api_server.py
   ```

2. Update config:
   ```yaml
   apiBase: http://192.168.1.100:8080/v1
   ```

**Security Note:** Use a strong API key for remote access:
```bash
JANET_API_KEY=your-secure-key python3 janet_api_server.py
```

---

## FAQ

### Q: Does my code leave my machine?

**A:** No. Janet runs entirely locally. Your code is processed on your machine using Ollama. Nothing is sent to external servers.

### Q: Can I use Janet offline?

**A:** Yes! Once you've pulled the Ollama models, Janet works completely offline. No internet connection required.

### Q: How much RAM do I need?

**A:** Depends on the model:
- TinyLlama (1.1B): ~2GB RAM
- Llama3 8B: ~8GB RAM
- Llama3 70B: ~40GB RAM

### Q: Can I use Janet with other IDEs?

**A:** Currently optimized for VSCode with Continue.dev. Support for JetBrains IDEs (via Continue.dev) is also available.

### Q: How does Janet compare to Cursor?

**A:** 
- **Similarities:** Chat, inline editing, autocomplete, codebase context
- **Advantages:** Offline-first, privacy-first, constitutional AI, open source
- **Trade-offs:** Requires local setup, performance depends on hardware

### Q: Can I customize Janet's behavior?

**A:** Yes! Edit the system message in `~/.continue/config.yaml` to change Janet's personality, coding style, and priorities.

### Q: What are the 16 constitutional axioms?

**A:** Janet follows principles including:
1. Privacy First
2. User Sovereignty
3. Transparency
4. Offline Capable
5. Constitutional Integrity
6. Memory Rules
7. Red Thread (emergency stop)
... and 9 more. See Janet's documentation for the complete list.

### Q: How do I update Janet?

**A:** 
1. Pull latest code: `git pull`
2. Update dependencies: `pip3 install -r requirements.txt`
3. Restart API server
4. Restart VSCode

### Q: Can I contribute to Janet?

**A:** Yes! Janet is open source (GPL/MIT). See the main Janet repository for contribution guidelines.

---

## Next Steps

Now that you have Janet set up:

1. **Try the chat interface** - Press Cmd+L and ask Janet a question
2. **Test inline editing** - Select code, press Cmd+K, describe a change
3. **Use autocomplete** - Start typing and see Janet's suggestions
4. **Explore custom commands** - Try `/constitutional-check` on your code
5. **Read the API reference** - See `API_REFERENCE.md` for advanced usage

---

## Support

- **Documentation:** See `API_REFERENCE.md` for detailed API docs
- **Issues:** Report bugs in the Janet repository
- **Community:** Join the Janet community for help and discussions

---

**Welcome to coding with Janet - your constitutional AI companion!** 🌱
