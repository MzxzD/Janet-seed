#!/bin/bash
# Quick start script for Janet Health heartbeat server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║              💚 JANET HEALTH - QUICK START 💚                         ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or later."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Checking dependencies..."
pip install -q websockets psutil 2>/dev/null || {
    echo "⚠️  Installing dependencies..."
    pip install websockets psutil
}
echo "✅ Dependencies installed"

# Check if server is already running
if lsof -Pi :8766 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo ""
    echo "⚠️  Server already running on port 8766"
    echo ""
    read -p "Kill existing server and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Stopping existing server..."
        pkill -f "heartbeat_server.py" || true
        sleep 2
    else
        echo "❌ Exiting. Stop the existing server first."
        exit 1
    fi
fi

# Start server
echo ""
echo "🚀 Starting Janet Health heartbeat server..."
echo ""

# Check if we should run in background
if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    echo "📝 Running in background. Logs: /tmp/janet-health.log"
    nohup python3 heartbeat_server.py > /tmp/janet-health.log 2>&1 &
    PID=$!
    echo "✅ Server started (PID: $PID)"
    echo ""
    echo "Monitor logs: tail -f /tmp/janet-health.log"
    echo "Stop server:  kill $PID"
else
    echo "📝 Running in foreground. Press Ctrl+C to stop."
    echo ""
    python3 heartbeat_server.py
fi
