# Fixing Ollama Metal GPU Error

## The Problem

You're seeing this error:
```
OllamaException - {"error":"llama runner process has terminated: error:Error Domain=MTLLibraryErrorDomain Code=3 \"Compiler encountered XPC_ERROR_CONNECTION_INVALID (is the OS shutting down?)\" UserInfo={NSLocalizedDescription=Compiler encountered XPC_ERROR_CONNECTION_INVALID (is the OS shutting down?)}\nggml_metal_init: error: failed to initialize the Metal library\nggml_backend_metal_device_init: error: failed to allocate context"}
```

This is a macOS Metal GPU initialization failure in Ollama. It's a system-level issue.

## Quick Solution: Use Mock Mode

**Janet is currently running in MOCK MODE**, which bypasses Ollama entirely and provides basic responses for testing Continue.dev. This lets you:
- Test the Continue.dev integration
- Verify Janet's API is working
- Use the IDE features without waiting for Ollama to be fixed

The mock server provides intelligent responses based on keywords in your queries.

## Permanent Solutions

### Option 1: Restart Your Mac (Recommended)
The Metal GPU error is often caused by macOS system services getting into a bad state. A simple restart usually fixes it:

```bash
# Save your work, then:
sudo shutdown -r now
```

After restart:
```bash
# Test Ollama
ollama run qwen2:latest "Hello"

# If it works, switch back to the real Janet server
cd /Users/mzxzd/Documents/Janet-Projects/JanetOS/janet-seed
./start_janet_api.sh
```

### Option 2: Force CPU Mode
If restart doesn't work, force Ollama to use CPU only (slower but works):

```bash
# Stop the mock server
pkill -f janet_api_server_mock

# Start Janet with CPU-only Ollama
cd /Users/mzxzd/Documents/Janet-Projects/JanetOS/janet-seed
OLLAMA_NUM_GPU=0 JANET_DEFAULT_MODEL=qwen2:latest python3 janet_api_server.py
```

Update Continue.dev config to use `qwen2:latest` instead of `janet-mock`.

### Option 3: Reinstall Ollama
If the above don't work, reinstall Ollama:

```bash
# Uninstall
brew uninstall ollama

# Clean up
rm -rf ~/.ollama

# Reinstall
brew install ollama

# Pull models again
ollama pull qwen2:latest
ollama pull llama3.2:latest
```

### Option 4: Update macOS
The Metal GPU error can be caused by outdated GPU drivers. Update macOS:

```bash
softwareupdate -l
sudo softwareupdate -i -a
```

## Switching Between Mock and Real Server

### Using Mock Server (Current)
```bash
cd /Users/mzxzd/Documents/Janet-Projects/JanetOS/janet-seed
python3 janet_api_server_mock.py
```

Continue.dev config:
```json
{"models":[{"title":"Janet","provider":"openai","model":"janet-mock","apiBase":"http://localhost:8080/v1","apiKey":"janet-local-dev"}]}
```

### Using Real Server (After Fix)
```bash
cd /Users/mzxzd/Documents/Janet-Projects/JanetOS/janet-seed
./start_janet_api.sh
```

Continue.dev config:
```json
{"models":[{"title":"Janet","provider":"openai","model":"qwen2:latest","apiBase":"http://localhost:8080/v1","apiKey":"janet-local-dev"}]}
```

## Testing Ollama Directly

To verify Ollama is working before switching back:

```bash
# Test basic functionality
ollama ps

# Test model inference
ollama run qwen2:latest "Say hello in 3 words"

# If this works without errors, Ollama is fixed!
```

## Current Status

✅ **Mock server is running** - Continue.dev should work now for testing
⚠️ **Ollama has Metal GPU error** - Needs one of the fixes above
📝 **Next step**: Try Option 1 (restart Mac) when convenient

---

**Note**: The mock server provides basic responses for testing. For full AI-powered code generation, you'll need to fix Ollama and switch to the real server.
