#!/usr/bin/env python3
"""
Start Janet's Home Assistant API Server
Quick launcher for the Home Assistant integration API.
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api.home_assistant_api import start_api_server

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("🤖 JANET HOME ASSISTANT API SERVER")
    print("=" * 70)
    print()
    print("Starting API server for Home Assistant integration...")
    print()
    print("📡 Endpoints:")
    print("   GET  http://localhost:8080/health       - Health check")
    print("   GET  http://localhost:8080/api/status   - Get Janet status")
    print("   POST http://localhost:8080/api/speak    - Make Janet speak")
    print("   POST http://localhost:8080/api/command  - Send command to Janet")
    print()
    print("🏠 Home Assistant Configuration:")
    print("   Host: localhost (or your Mac's IP)")
    print("   API Port: 8080")
    print("   WebSocket Port: 8765 (not yet implemented)")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    try:
        start_api_server(host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down API server...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
