#!/bin/bash
# Start Janet API Server with Qwen2 model (CPU-only mode to avoid Metal GPU issues)

echo "=========================================="
echo "Starting Janet with Qwen2 (CPU mode)"
echo "=========================================="

# Kill any existing servers
pkill -f janet_api_server 2>/dev/null
pkill -f janet_api_server_mock 2>/dev/null

# Make sure Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    brew services start ollama
    sleep 3
fi

# Check if qwen2 model is available
if ! ollama list | grep -q "qwen2:latest"; then
    echo "❌ Error: qwen2:latest model not found"
    echo "Run: ollama pull qwen2:latest"
    exit 1
fi

echo "✅ Qwen2 model found"
echo "🚀 Starting Janet API Server..."
echo ""

# Start Janet with CPU-only Ollama and qwen2 model
cd "$(dirname "$0")"
export OLLAMA_NUM_GPU=0
export JANET_DEFAULT_MODEL=qwen2:latest
export JANET_API_PORT=8080
export JANET_API_KEY=janet-local-dev

python3 janet_api_server.py

# Note: This will run in foreground. Press Ctrl+C to stop.
