#!/bin/bash
# J.A.N.E.T. Seed Bootstrap Installer
# macOS and Linux compatible
# This script sets up the Python environment and calls main.py for installation

set -e

JANET_HOME="${JANET_HOME:-$HOME/.janet}"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM="$(uname -s)"

echo "🚀 J.A.N.E.T. Seed Bootstrap"
echo "=========================="

# Check for existing installation
if [ -d "$JANET_HOME" ] && [ -f "$JANET_HOME/config/installation.json" ]; then
    echo "⚠️  Existing Janet installation found at $JANET_HOME"
    read -p "Do you want to remove it and reinstall? (yes/NO): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing installation..."
        rm -rf "$JANET_HOME"
    else
        echo "Installation cancelled."
        exit 1
    fi
fi

# Ensure Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Check for required Python packages (basic ones needed for installation)
echo "Checking Python environment..."
python3 -c "import sys; assert sys.version_info >= (3, 8), 'Python 3.8+ required'" || {
    echo "❌ Python 3.8 or higher is required"
    exit 1
}

# Install basic dependencies if needed (psutil for hardware detection)
python3 -c "import psutil" 2>/dev/null || {
    echo "Installing basic dependencies..."
    pip3 install --user psutil || {
        echo "⚠️  Could not install psutil. Installation may fail."
    }
}

# Run main.py which handles the full installation flow
echo ""
echo "Starting Janet installation process..."
echo ""
python3 "$INSTALL_DIR/src/main.py"

# Installation complete message is handled by main.py
