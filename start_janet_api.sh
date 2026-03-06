#!/bin/bash
# Start Janet API Server for IDE integration

echo "=========================================="
echo "Janet API Server Startup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "janet_api_server.py" ]; then
    echo "❌ Error: janet_api_server.py not found"
    echo "   Please run this script from the janet-seed directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Check if Ollama is running
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Warning: ollama command not found"
    echo "   Make sure Ollama is installed: https://ollama.ai"
    echo ""
fi

# Check if required Python packages are installed
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  FastAPI or uvicorn not installed"
    echo "   Installing dependencies..."
    pip3 install fastapi uvicorn
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        echo "   Please run: pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo "✅ Dependencies OK"
echo ""

# Set environment variables (can be customized)
export JANET_API_PORT=${JANET_API_PORT:-8080}
export JANET_API_HOST=${JANET_API_HOST:-0.0.0.0}
export JANET_DEFAULT_MODEL=${JANET_DEFAULT_MODEL:-tinyllama:1.1b}
export JANET_API_KEY=${JANET_API_KEY:-janet-local-dev}

echo "Configuration:"
echo "  Port: $JANET_API_PORT"
echo "  Host: $JANET_API_HOST"
echo "  Default Model: $JANET_DEFAULT_MODEL"
echo "  API Key: $JANET_API_KEY"
echo ""

# Check if model is available
echo "Checking if model is available..."
ollama list | grep -q "$JANET_DEFAULT_MODEL"
if [ $? -ne 0 ]; then
    echo "⚠️  Model $JANET_DEFAULT_MODEL not found"
    echo "   Pulling model (this may take a few minutes)..."
    ollama pull "$JANET_DEFAULT_MODEL"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to pull model"
        echo "   Please run: ollama pull $JANET_DEFAULT_MODEL"
        exit 1
    fi
fi

echo "✅ Model available"
echo ""
echo "=========================================="
echo "Starting Janet API Server..."
echo "=========================================="
echo ""

# Start the server
python3 janet_api_server.py

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Server exited with error code $EXIT_CODE"
    exit $EXIT_CODE
fi
