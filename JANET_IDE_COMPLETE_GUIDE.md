# Janet-Powered IDE - Complete Guide

**Transform Your IDE into a Constitutional AI Coding Assistant**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What You Get](#what-you-get)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Usage Guide](#usage-guide)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Topics](#advanced-topics)
11. [Development](#development)
12. [FAQ](#faq)

---

## Overview

### What is Janet-Powered IDE?

Janet-Powered IDE is a complete integration that brings Janet's constitutional AI into your development environment, providing Cursor-like features while maintaining privacy, working offline, and following constitutional principles.

### Key Features

- 💬 **Chat Interface** (Cmd+L) - Conversational coding assistance
- ✏️ **Inline Editing** (Cmd+K) - AI-powered code modifications
- ⚡ **Autocomplete** (Tab) - Real-time code suggestions
- 🔍 **Codebase Context** (@-mentions) - Reference files and symbols
- 🔒 **Privacy-First** - All processing local, no cloud
- 🌱 **Constitutional AI** - Follows 16 axioms
- 📡 **Offline-Capable** - Works without internet
- 🔓 **Open Source** - Full control over your AI assistant

### Why Janet Instead of Cursor?

| Feature | Cursor | Janet IDE |
|---------|--------|-----------|
| Privacy | Cloud-based | 100% local |
| Offline | Limited | Full support |
| Open Source | No | Yes |
| Constitutional AI | No | Yes (16 axioms) |
| Custom Models | Limited | Any Ollama model |
| Cost | Subscription | Free |
| Data Ownership | Vendor | You |

---

## What You Get

### Components

1. **Janet API Server** (`janet_api_server.py`)
   - OpenAI-compatible HTTP API
   - Streaming and non-streaming responses
   - Multi-model support
   - Constitutional AI integration
   - Performance tracking

2. **Continue.dev Configuration** (`~/.continue/config.yaml`)
   - Pre-configured for Janet
   - Multiple model profiles
   - Custom constitutional commands
   - Privacy-first settings

3. **Startup Scripts**
   - `start_janet_api.sh` - Automated server startup
   - Dependency checking
   - Model verification

4. **Test Suite** (`test_janet_api.py`)
   - Comprehensive API tests
   - Health checks
   - Performance verification

5. **Documentation**
   - Setup guides
   - API reference
   - Troubleshooting
   - Examples

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      VSCode IDE                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Continue.dev Extension                      │ │
│  │  • Chat Interface (Cmd+L)                           │ │
│  │  • Inline Editing (Cmd+K)                           │ │
│  │  • Autocomplete (Tab)                               │ │
│  │  • Codebase Context (@)                             │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         │
                         │ HTTP POST /v1/chat/completions
                         │ (OpenAI-compatible API)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Janet API Server (Port 8080)                │
│  ┌────────────────────────────────────────────────────┐ │
│  │  FastAPI + uvicorn                                  │ │
│  │  • Request validation & authentication              │ │
│  │  • Streaming support (SSE)                          │ │
│  │  • Session management                               │ │
│  │  • Performance tracking                             │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         │
                         │ Python API
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    JanetBrain Core                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │  • Multi-model support                              │ │
│  │  • Conversation history management                  │ │
│  │  • Response caching (LRU)                           │ │
│  │  • Performance tracking                             │ │
│  │  • Constitutional AI enforcement                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         │
                         │ LiteLLM
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Ollama (Local LLM)                      │
│  • tinyllama:1.1b (fast - autocomplete)                 │
│  • llama3:8b (balanced - general coding)                │
│  • llama3:70b (powerful - complex reasoning)            │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Action** → VSCode (Cmd+L, Cmd+K, or Tab)
2. **Continue.dev** → Formats request as OpenAI API call
3. **Janet API Server** → Validates, authenticates, routes to JanetBrain
4. **JanetBrain** → Checks cache, generates response via Ollama
5. **Response** → Streams back through API → Continue.dev → VSCode

### Privacy & Security

```
┌─────────────────────────────────────────────────────────┐
│                    Your Machine                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  VSCode  │→ │  Janet   │→ │  Ollama  │             │
│  │          │  │   API    │  │   LLM    │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                          │
│  ✅ All processing local                                │
│  ✅ No external API calls                               │
│  ✅ Your code never leaves your machine                 │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 5-Minute Setup

```bash
# 1. Pull a model (2 min)
ollama pull tinyllama:1.1b

# 2. Install dependencies (1 min)
cd Janet-Projects/JanetOS/janet-seed
pip3 install fastapi uvicorn litellm

# 3. Start Janet API server (30 sec)
./start_janet_api.sh

# 4. Install Continue.dev in VSCode (1 min)
# Extensions → Search "Continue" → Install

# 5. Start coding! (30 sec)
# Press Cmd+L and say "Hello Janet!"
```

### First Steps

1. **Chat with Janet**
   - Press **Cmd+L** (Mac) or **Ctrl+L** (Windows/Linux)
   - Type: "Explain what a closure is in JavaScript"
   - Watch Janet respond!

2. **Edit Code**
   - Select some code
   - Press **Cmd+K**
   - Say: "Add error handling"
   - Janet will suggest modifications

3. **Autocomplete**
   - Start typing code
   - Wait for suggestions
   - Press **Tab** to accept

---

## Installation

### Prerequisites

#### Required Software

1. **Python 3.8+**
   ```bash
   python3 --version  # Should be 3.8 or higher
   ```

2. **Ollama** (Local LLM runtime)
   - macOS: `brew install ollama`
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`
   - Windows: Download from https://ollama.ai

3. **VSCode** (or VSCodium)
   - Download from https://code.visualstudio.com

4. **Continue.dev Extension**
   - Install from VSCode marketplace
   - Search "Continue" in Extensions (Cmd+Shift+X)

#### Recommended Models

```bash
# Fast model for autocomplete (required)
ollama pull tinyllama:1.1b

# Balanced model for general use (recommended)
ollama pull llama3:8b

# Powerful model for complex tasks (optional)
ollama pull llama3:70b

# Embeddings for codebase search (optional)
ollama pull nomic-embed-text
```

### Step-by-Step Installation

#### Step 1: Install Python Dependencies

```bash
cd /path/to/Janet-Projects/JanetOS/janet-seed
pip3 install -r requirements.txt
```

This installs:
- FastAPI (API server framework)
- uvicorn (ASGI server)
- litellm (LLM integration)
- All other Janet dependencies

#### Step 2: Verify Installation

```bash
# Check Python packages
python3 -c "import fastapi, uvicorn, litellm; print('✅ All packages installed')"

# Check Ollama
ollama list

# Check Janet brain
python3 -c "from src.core.janet_brain import JanetBrain; print('✅ Janet brain available')"
```

#### Step 3: Start Janet API Server

```bash
# Option 1: Use startup script (recommended)
./start_janet_api.sh

# Option 2: Start directly
python3 janet_api_server.py

# Option 3: Custom configuration
JANET_API_PORT=8080 JANET_DEFAULT_MODEL=llama3:8b python3 janet_api_server.py
```

**Expected output:**
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
```

**Keep this terminal open** - the server must run while you code.

#### Step 4: Test the API Server

In a **new terminal**:

```bash
cd Janet-Projects/JanetOS/janet-seed
python3 test_janet_api.py
```

**Expected output:**
```
============================================================
JANET API SERVER TEST SUITE
============================================================

✅ PASS - Health Check
✅ PASS - List Models
✅ PASS - Chat Completion
✅ PASS - Streaming Completion
✅ PASS - Performance Stats

Results: 5/5 tests passed

🎉 All tests passed! Janet API server is working correctly.
```

#### Step 5: Install Continue.dev

1. Open VSCode
2. Press **Cmd+Shift+X** (Extensions)
3. Search for "Continue"
4. Click **Install**

#### Step 6: Verify Configuration

The configuration file is already created at `~/.continue/config.yaml`.

To verify:
```bash
cat ~/.continue/config.yaml
```

You should see Janet configured as the primary model.

#### Step 7: Restart VSCode

1. Close and reopen VSCode
2. Or: **Cmd+Shift+P** → "Developer: Reload Window"

---

## Configuration

### Environment Variables

Customize the API server:

```bash
# Port (default: 8080)
export JANET_API_PORT=8080

# Host (default: 0.0.0.0)
export JANET_API_HOST=0.0.0.0

# Default model (default: tinyllama:1.1b)
export JANET_DEFAULT_MODEL=llama3:8b

# API key (default: janet-local-dev)
export JANET_API_KEY=your-custom-key

# Start server with custom config
python3 janet_api_server.py
```

### Continue.dev Configuration

Edit `~/.continue/config.yaml`:

```yaml
models:
  # Primary model
  - name: Janet
    provider: openai
    model: janet-constitutional-ai
    apiBase: http://localhost:8080/v1
    apiKey: janet-local-dev
    title: Janet (Constitutional AI)
    contextLength: 4096
    
  # Fast model for autocomplete
  - name: Janet Fast
    provider: openai
    model: tinyllama:1.1b
    apiBase: http://localhost:8080/v1
    apiKey: janet-local-dev
    title: Janet Fast
    contextLength: 2048
    
  # Powerful model for complex tasks
  - name: Janet Pro
    provider: openai
    model: llama3:8b
    apiBase: http://localhost:8080/v1
    apiKey: janet-local-dev
    title: Janet Pro
    contextLength: 8192

# Autocomplete configuration
tabAutocompleteModel:
  name: Janet Fast
  provider: openai
  model: tinyllama:1.1b
  apiBase: http://localhost:8080/v1
  apiKey: janet-local-dev

# Embeddings for codebase search
embeddingsProvider:
  provider: ollama
  model: nomic-embed-text
  apiBase: http://localhost:11434
```

### Model Selection Guide

| Model | RAM | Speed | Quality | Use Case |
|-------|-----|-------|---------|----------|
| tinyllama:1.1b | 2GB | ⚡⚡⚡ | ⭐⭐ | Autocomplete, quick tasks |
| llama3:8b | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | General coding, explanations |
| llama3:70b | 40GB | ⚡ | ⭐⭐⭐⭐⭐ | Complex reasoning, architecture |

---

## Usage Guide

### Chat Interface (Cmd+L)

**Open the chat sidebar:**
1. Press **Cmd+L** (Mac) or **Ctrl+L** (Windows/Linux)
2. Type your question
3. Janet responds with code, explanations, or suggestions

**Examples:**

```
You: Explain how async/await works in JavaScript

Janet: Async/await is syntactic sugar over Promises that makes
asynchronous code look and behave more like synchronous code...
```

```
You: Write a Python function to parse JSON with error handling

Janet: Here's a robust JSON parser with error handling:

def parse_json_safely(json_string):
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None
```

```
You: How do I optimize this SQL query?
@database.sql

Janet: Looking at your query, here are three optimizations...
```

### Inline Editing (Cmd+K)

**Edit code directly:**
1. Select code you want to modify
2. Press **Cmd+K** (Mac) or **Ctrl+K** (Windows/Linux)
3. Describe the change
4. Janet suggests modifications

**Examples:**

```python
# Original code
def process_data(data):
    return data.upper()
```

**Select the function, press Cmd+K, say: "Add error handling and type hints"**

```python
# Janet's suggestion
def process_data(data: str) -> str:
    try:
        if not isinstance(data, str):
            raise TypeError("Data must be a string")
        return data.upper()
    except Exception as e:
        print(f"Error processing data: {e}")
        return ""
```

### Autocomplete (Tab)

**Get AI-powered suggestions:**
1. Start typing code
2. Wait for suggestions (usually <1 second)
3. Press **Tab** to accept
4. Press **Esc** to dismiss

**Example:**

```python
# You type:
def fibonacci(

# Janet suggests:
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

### Codebase Context (@-mentions)

**Reference files and symbols:**

```
@filename.py - Reference a specific file
@FunctionName - Reference a function or class
@folder/ - Reference a directory
```

**Examples:**

```
You: @app.py How does the authentication middleware work?

Janet: Looking at app.py, the authentication middleware...
```

```
You: @UserModel @AuthService How do these work together?

Janet: The UserModel and AuthService interact in the following way...
```

### Custom Constitutional Commands

#### /constitutional-check

Check code against Janet's 16 axioms:

```
You: /constitutional-check
[Select code]

Janet: Constitutional Analysis:
✅ Privacy First - No external data transmission
✅ User Sovereignty - User has full control
⚠️  Transparency - Consider adding comments explaining the algorithm
✅ Offline Capable - No network dependencies
```

#### /explain-constitutionally

Explain code with constitutional principles:

```
You: /explain-constitutionally
[Select code]

Janet: This code implements user authentication with these
constitutional considerations:

Privacy: Passwords are hashed locally before storage...
Transparency: The auth flow is clearly documented...
User Sovereignty: Users can export their data anytime...
```

#### /secure-refactor

Refactor for security and privacy:

```
You: /secure-refactor
[Select code that sends data to server]

Janet: Here's a more secure version:

1. Encrypt data before transmission
2. Validate input to prevent injection
3. Add rate limiting
4. Implement proper error handling without leaking info
```

### Red Thread Emergency Stop

If Janet starts doing something unexpected:

```
You: red thread

Janet: 🔴 Red Thread activated - all operations paused
```

This immediately stops all AI operations. It's part of Janet's constitutional design (Axiom 8).

---

## API Reference

### Base URL

```
http://localhost:8080
```

### Authentication

All requests require Bearer token authentication:

```bash
Authorization: Bearer janet-local-dev
```

### Endpoints

#### POST /v1/chat/completions

Generate a response to a conversation.

**Request:**
```json
{
  "model": "tinyllama:1.1b",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "tinyllama:1.1b",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

#### GET /v1/models

List available models.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "tinyllama:1.1b",
      "object": "model",
      "created": 1677652288,
      "owned_by": "janet"
    }
  ]
}
```

#### GET /health

Check server health.

**Response:**
```json
{
  "status": "healthy",
  "brain_available": true,
  "current_model": "tinyllama:1.1b",
  "available_models": ["tinyllama:1.1b", "llama3:8b"],
  "active_sessions": 0
}
```

#### GET /v1/performance

Get performance statistics (Janet-specific).

**Response:**
```json
{
  "current_model": "tinyllama:1.1b",
  "model_performance": {
    "tinyllama:1.1b": {
      "total_requests": 42,
      "average_latency": 0.512,
      "success_rate": 0.976
    }
  },
  "cache_stats": {
    "hit_rate": 0.190
  }
}
```

**For complete API documentation, see [API_REFERENCE.md](API_REFERENCE.md)**

---

## Troubleshooting

### Server Won't Start

**Problem:** `janet_api_server.py` fails to start

**Solutions:**

1. Check dependencies:
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
   ```

4. Try a different port:
   ```bash
   JANET_API_PORT=8081 python3 janet_api_server.py
   ```

### Connection Failed in Continue.dev

**Problem:** "Failed to connect to model"

**Solutions:**

1. Verify server is running:
   ```bash
   curl http://localhost:8080/health
   ```

2. Check API key matches:
   - Server: `janet-local-dev` (default)
   - Config: Must match server

3. Check VSCode logs:
   - **Cmd+Shift+P** → "Developer: Show Logs"
   - Select "Extension Host"

4. Restart VSCode

### Slow Responses

**Problem:** Janet takes too long to respond

**Solutions:**

1. Switch to faster model:
   ```yaml
   model: tinyllama:1.1b
   ```

2. Reduce max_tokens:
   ```yaml
   max_tokens: 500
   ```

3. Check system resources:
   ```bash
   top -o cpu  # macOS
   htop        # Linux
   ```

4. Close other applications

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

3. Update config to use available model

### Autocomplete Not Working

**Problem:** No autocomplete suggestions

**Solutions:**

1. Check tabAutocompleteModel in config
2. Verify fast model is pulled
3. Restart VSCode
4. Check Continue.dev settings:
   - Settings → Extensions → Continue
   - Enable "Tab Autocomplete"

**For more troubleshooting, see [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md#troubleshooting)**

---

## Advanced Topics

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

### Multiple Model Profiles

Configure different models for different scenarios:

```yaml
models:
  - name: Janet Fast
    model: tinyllama:1.1b
    contextLength: 2048
    
  - name: Janet Balanced
    model: llama3:8b
    contextLength: 8192
    
  - name: Janet Pro
    model: llama3:70b
    contextLength: 8192
    
  - name: Janet Code
    model: codellama:13b
    contextLength: 16384
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

3. Use strong API key:
   ```bash
   JANET_API_KEY=your-secure-key python3 janet_api_server.py
   ```

### Performance Tuning

Optimize for your hardware:

```yaml
performance:
  autocompleteDebounce: 300  # ms
  maxConcurrentRequests: 3
  requestTimeout: 30000  # ms
```

---

## Development

### Project Structure

```
janet-seed/
├── janet_api_server.py          # Main API server
├── start_janet_api.sh           # Startup script
├── test_janet_api.py            # Test suite
├── JANET_IDE_SETUP.md           # Setup guide
├── API_REFERENCE.md             # API docs
├── QUICK_START_IDE.md           # Quick start
├── JANET_IDE_COMPLETE_GUIDE.md  # This file
└── src/
    └── core/
        └── janet_brain.py       # JanetBrain core
```

### Running Tests

```bash
# Run all tests
python3 test_janet_api.py

# Test specific endpoint
curl http://localhost:8080/health
```

### Contributing

1. Read the code
2. Make improvements
3. Test thoroughly
4. Update documentation
5. Submit changes

### Debugging

Enable verbose logging:

```python
# In janet_api_server.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Monitor requests:

```bash
# Watch server logs
tail -f server.log

# Monitor performance
curl http://localhost:8080/v1/performance | jq
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

**A:** Currently optimized for VSCode with Continue.dev. JetBrains support is available through Continue.dev.

### Q: How does Janet compare to GitHub Copilot?

**A:**
- **Privacy:** Janet is 100% local, Copilot sends code to cloud
- **Offline:** Janet works offline, Copilot requires internet
- **Cost:** Janet is free, Copilot requires subscription
- **Models:** Janet supports any Ollama model, Copilot uses fixed models
- **Constitutional:** Janet follows 16 axioms, Copilot doesn't

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
8. Kind
9. Wise
10. Present
11. Teachable
12. Voice-First
13. Cross-Platform
14. Open Source
15. Community-Driven
16. Sustainable

See Janet's main documentation for complete details.

### Q: How do I update Janet?

**A:**
1. Pull latest code: `git pull`
2. Update dependencies: `pip3 install -r requirements.txt`
3. Restart API server
4. Restart VSCode

### Q: Can I contribute to Janet?

**A:** Yes! Janet is open source (GPL/MIT). See the main Janet repository for contribution guidelines.

### Q: Is Janet suitable for production use?

**A:** The IDE integration is production-ready for local development. For team/enterprise use, consider:
- Centralized Janet server
- Authentication and access control
- Monitoring and logging
- Backup and disaster recovery

---

## Resources

### Documentation

- **Setup Guide:** [JANET_IDE_SETUP.md](JANET_IDE_SETUP.md)
- **API Reference:** [API_REFERENCE.md](API_REFERENCE.md)
- **Quick Start:** [QUICK_START_IDE.md](QUICK_START_IDE.md)
- **Implementation Summary:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

### Files

- **API Server:** `janet_api_server.py`
- **Startup Script:** `start_janet_api.sh`
- **Test Suite:** `test_janet_api.py`
- **Configuration:** `~/.continue/config.yaml`

### External Links

- **Continue.dev:** https://continue.dev
- **Ollama:** https://ollama.ai
- **Janet Project:** See main repository

---

## Support

### Getting Help

1. **Check documentation** - Most questions are answered here
2. **Run tests** - `python3 test_janet_api.py`
3. **Check logs** - Server logs show detailed errors
4. **Community** - Join Janet community discussions

### Reporting Issues

When reporting issues, include:
- OS and version
- Python version
- Ollama version
- Error messages
- Steps to reproduce

---

## Conclusion

You now have a complete Cursor-like IDE experience powered by Janet's constitutional AI!

**Key Takeaways:**

✅ **Privacy-First** - Your code never leaves your machine  
✅ **Offline-Capable** - Works without internet  
✅ **Constitutional** - Follows 16 axioms  
✅ **Open Source** - Full control over your AI  
✅ **Free** - No subscriptions or hidden costs  
✅ **Powerful** - Full Cursor feature parity  

**Next Steps:**

1. Start the server: `./start_janet_api.sh`
2. Open VSCode and press Cmd+L
3. Start coding with Janet!

**Welcome to the future of constitutional AI-assisted development!** 🌱

---

**Document Version:** 1.0.0  
**Last Updated:** March 2, 2026  
**Status:** Complete and Production-Ready
